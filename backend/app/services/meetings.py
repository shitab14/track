"""Level 10 Meeting lifecycle and real-time state (ADR0009).

The meetings row is the single source of truth. Every mutating operation
commits, then publishes the fresh snapshot through the broadcaster so connected
attendees converge within ~1s. Meeting *timing* uses the real wall clock
(``datetime.now(timezone.utc)``), which is deliberately distinct from the frozen
business clock ``APP_NOW`` that drives domain rules.
"""
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.broadcaster import broadcaster
from app.domain.rules import compute_meeting_rating
from app.models import Meeting, MeetingAttendee, MeetingRating, User

# Forward-only agenda with the seeded section budgets (minutes).
SECTION_ORDER = ["scorecard", "ids", "conclude", "ended"]
SECTION_BUDGET_SECONDS = {"scorecard": 5 * 60, "ids": 60 * 60, "conclude": 10 * 60}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value):
    """Normalize a possibly-naive DB timestamp to timezone-aware UTC."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _iso(value):
    value = _as_utc(value)
    return value.isoformat().replace("+00:00", "Z") if value else None


# --------------------------------------------------------------------------
# Serialization
# --------------------------------------------------------------------------
def serialize_state(db: Session, meeting: Meeting) -> dict:
    """Authoritative meeting snapshot pushed to clients and returned by the API.

    Includes ``server_now`` so clients render the section countdown locally
    between pushes, and ``over_time`` for the current overrun state.
    """
    meeting = (
        db.query(Meeting)
        .options(
            joinedload(Meeting.attendees).joinedload(MeetingAttendee.user),
            joinedload(Meeting.ratings),
        )
        .filter_by(id=meeting.id)
        .first()
    )

    section = meeting.current_section
    budget = SECTION_BUDGET_SECONDS.get(section)
    now = _now()
    elapsed = None
    over_time = False
    if section != "ended" and meeting.section_started_at is not None:
        elapsed = (now - _as_utc(meeting.section_started_at)).total_seconds()
        over_time = budget is not None and elapsed > budget

    rating_values = {r.user_id: r.rating for r in meeting.ratings}

    return {
        "id": meeting.id,
        "team_id": meeting.team_id,
        "facilitator_id": meeting.facilitator_id,
        "section": section,
        "section_started_at": _iso(meeting.section_started_at),
        "section_budget_seconds": budget,
        "elapsed_seconds": int(elapsed) if elapsed is not None else None,
        "over_time": over_time,
        "server_now": _iso(now),
        "started_at": _iso(meeting.started_at),
        "ended_at": _iso(meeting.ended_at),
        "attendees": [
            {"id": a.user_id, "name": a.user.name, "joined_at": _iso(a.joined_at)}
            for a in sorted(meeting.attendees, key=lambda a: a.user_id)
        ],
        "ratings": {
            "values": rating_values,
            "count": len(rating_values),
            "average": compute_meeting_rating(list(rating_values.values())),
        },
    }


def _publish_state(db: Session, meeting: Meeting) -> None:
    if broadcaster.has_subscribers(meeting.id):
        broadcaster.publish(meeting.id, {"type": "meeting_state", "data": serialize_state(db, meeting)})


def publish_data_changed(db: Session, team_id: str, scope: str) -> None:
    """Signal connected attendees to refetch a reused section (Scorecard/Issues/
    To-Dos) from its REST endpoint. No-op when the team has no active meeting or
    no subscribers; never allowed to disrupt the originating mutation.
    """
    try:
        meeting = db.query(Meeting).filter_by(team_id=team_id, ended_at=None).first()
        if meeting and broadcaster.has_subscribers(meeting.id):
            broadcaster.publish(meeting.id, {"type": "data_changed", "data": {"scope": scope}})
    except Exception:  # pragma: no cover - signalling must never break a write
        pass


# --------------------------------------------------------------------------
# Lookups
# --------------------------------------------------------------------------
def get_meeting(db: Session, meeting_id: str) -> Meeting:
    meeting = db.query(Meeting).filter_by(id=meeting_id).first()
    if meeting is None:
        raise HTTPException(404, "Meeting not found")
    return meeting


def get_active_meeting(db: Session, team_id: str):
    return db.query(Meeting).filter_by(team_id=team_id, ended_at=None).first()


# --------------------------------------------------------------------------
# Lifecycle
# --------------------------------------------------------------------------
def start_meeting(db: Session, team_id: str, user: User):
    """Start the team's meeting and become facilitator. Idempotent: if an active
    meeting already exists (including under a concurrent start), return it."""
    existing = get_active_meeting(db, team_id)
    if existing:
        return existing, False

    now = _now()
    meeting = Meeting(
        id=f"mt_{uuid4().hex}",
        team_id=team_id,
        facilitator_id=user.id,
        current_section="scorecard",
        started_at=now,
        section_started_at=now,
    )
    db.add(meeting)
    db.add(MeetingAttendee(meeting_id=meeting.id, user_id=user.id, joined_at=now))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = get_active_meeting(db, team_id)
        if existing is None:
            raise
        return existing, False
    db.refresh(meeting)
    return meeting, True


def join_meeting(db: Session, meeting: Meeting, user: User) -> Meeting:
    """Record the user as an attendee (idempotent) and broadcast the roster."""
    exists = db.query(MeetingAttendee).filter_by(meeting_id=meeting.id, user_id=user.id).first()
    if not exists:
        db.add(MeetingAttendee(meeting_id=meeting.id, user_id=user.id, joined_at=_now()))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()  # concurrent join of the same user
    _publish_state(db, meeting)
    return meeting


def _require_facilitator(meeting: Meeting, user: User) -> None:
    if meeting.facilitator_id != user.id:
        raise HTTPException(403, "Only the facilitator can control the meeting")


def advance_meeting(db: Session, meeting_id: str, user: User) -> Meeting:
    """Advance to the next section under a row lock so a double-click cannot skip
    a section. Facilitator only; terminal once ended."""
    meeting = db.query(Meeting).filter_by(id=meeting_id).with_for_update().first()
    if meeting is None:
        raise HTTPException(404, "Meeting not found")
    _require_facilitator(meeting, user)
    if meeting.current_section == "ended" or meeting.ended_at is not None:
        raise HTTPException(409, "Meeting has already ended")

    nxt = SECTION_ORDER[SECTION_ORDER.index(meeting.current_section) + 1]
    now = _now()
    meeting.current_section = nxt
    meeting.section_started_at = now
    if nxt == "ended":
        meeting.ended_at = now
    db.commit()
    db.refresh(meeting)
    _publish_state(db, meeting)
    return meeting


def end_meeting(db: Session, meeting_id: str, user: User) -> Meeting:
    """End the meeting at any time. Facilitator only; terminal once ended."""
    meeting = db.query(Meeting).filter_by(id=meeting_id).with_for_update().first()
    if meeting is None:
        raise HTTPException(404, "Meeting not found")
    _require_facilitator(meeting, user)
    if meeting.current_section == "ended" or meeting.ended_at is not None:
        raise HTTPException(409, "Meeting has already ended")

    now = _now()
    meeting.current_section = "ended"
    meeting.ended_at = now
    meeting.section_started_at = now
    db.commit()
    db.refresh(meeting)
    _publish_state(db, meeting)
    return meeting


def set_rating(db: Session, meeting: Meeting, user: User, rating: int) -> Meeting:
    """Set or change the caller's rating (1–10). Only attending Admins/Team
    Members may rate; Observers are rejected upstream by require_team_write."""
    if meeting.ended_at is not None or meeting.current_section == "ended":
        raise HTTPException(409, "Meeting has already ended")
    is_attendee = db.query(MeetingAttendee).filter_by(meeting_id=meeting.id, user_id=user.id).first()
    if not is_attendee:
        raise HTTPException(403, "Only attendees can rate the meeting")

    existing = db.query(MeetingRating).filter_by(meeting_id=meeting.id, user_id=user.id).first()
    if existing:
        existing.rating = rating
    else:
        db.add(MeetingRating(meeting_id=meeting.id, user_id=user.id, rating=rating))
    db.commit()
    db.refresh(meeting)
    _publish_state(db, meeting)
    return meeting
