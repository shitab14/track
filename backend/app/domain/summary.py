"""Shared meeting-summary computation (ADR0010).

One function produces a meeting's summary for both the rules report
(`app/domain/report.py`) and the API, so the two cannot diverge. The summary
covers: the last closed week's Measurable statuses (as of a business instant),
the Issues solved and To-Dos created during the meeting, the attendees, and the
rating.

"During the meeting" is resolved two ways:
  - explicit attribution ids (``solved_ids`` / ``created_ids``) when known — the
    clock-independent path used when the app concludes a live meeting;
  - otherwise the ``[started_at, ended_at]`` timestamp window — the path the
    rules report uses for the seeded meetings, whose timestamps share one clock.
"""
from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core import clock
from app.domain import rules
from app.models import Issue, Measurable, Meeting, Score, Todo


def _as_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def compute_meeting_summary(
    db: Session,
    meeting: Meeting,
    as_of_utc: datetime,
    solved_ids: Optional[List[str]] = None,
    created_ids: Optional[List[str]] = None,
) -> dict:
    """Return the summary dict for ``meeting``.

    ``as_of_utc`` is the business instant whose last closed week the Scorecard
    reflects (the meeting's conclusion time). When ``solved_ids`` / ``created_ids``
    are given they define the in-meeting lists; otherwise they are derived from
    the meeting's timestamp window.
    """
    team_id = meeting.team_id
    scorecard_week = clock.get_last_closed_week_start(_as_utc(as_of_utc))

    measurables = db.query(Measurable).filter_by(team_id=team_id).order_by(Measurable.id).all()
    measurable_status = {}
    for m in measurables:
        score = db.query(Score).filter_by(measurable_id=m.id, week_start=scorecard_week).first()
        measurable_status[m.id] = rules.compute_measurable_status(
            goal_type=m.goal_type,
            goal_value=m.goal_value,
            goal_min=m.goal_min,
            goal_max=m.goal_max,
            score_value=score.value if score else None,
            is_closed_week=True,
        )

    if solved_ids is None:
        solved_ids = [
            i.id
            for i in db.query(Issue)
            .filter_by(team_id=team_id)
            .filter(Issue.solved_at >= meeting.started_at, Issue.solved_at <= meeting.ended_at)
            .all()
        ]
    if created_ids is None:
        created_ids = [
            t.id
            for t in db.query(Todo)
            .filter_by(team_id=team_id)
            .filter(Todo.created_at >= meeting.started_at, Todo.created_at <= meeting.ended_at)
            .all()
        ]

    attendee_ids = sorted(a.user_id for a in meeting.attendees)
    rating = rules.compute_meeting_rating([r.rating for r in meeting.ratings])

    return {
        "scorecard_week": scorecard_week.isoformat(),
        "measurable_status": measurable_status,
        "issues_solved": sorted(solved_ids),
        "todos_created": sorted(created_ids),
        "attendee_ids": attendee_ids,
        "rating": rating,
    }
