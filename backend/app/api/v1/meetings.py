"""Level 10 Meeting endpoints and the SSE real-time stream (ADR0009).

Client actions are ordinary REST calls; only server→client state is pushed, over
Server-Sent Events. The stream takes the user id as a query parameter because
the browser ``EventSource`` cannot set the ``X-User-Id`` header; it enforces the
same team-read check as every other read.
"""
import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_team_read, require_team_write, verify_team_access
from app.core.broadcaster import broadcaster
from app.core.response import ApiResponse
from app.db.session import SessionLocal, get_db
from app.models import User
from app.schemas.meeting import RatingInput
from app.services.meetings import (
    advance_meeting,
    end_meeting,
    get_active_meeting,
    get_meeting,
    get_meeting_summary,
    join_meeting,
    serialize_state,
    set_rating,
    start_meeting,
)

router = APIRouter()

HEARTBEAT_SECONDS = 15


def _resolve_user(db: Session, user_id: Optional[str]) -> User:
    """Resolve a seeded user the same way get_current_user does, for the SSE
    query-parameter path."""
    uid = user_id or "u1"
    user = db.query(User).filter_by(id=uid).first()
    if not user:
        raise HTTPException(401, f"Invalid or unknown user context: '{uid}'")
    return user


def _sse(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"


@router.post("/teams/{team_id}/meetings")
def start(team_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    verify_team_access(team_id=team_id, write=True, current_user=user, db=db)
    meeting, created = start_meeting(db, team_id, user)
    return ApiResponse.success(
        serialize_state(db, meeting),
        "Meeting started" if created else "Meeting already active",
    )


@router.get("/teams/{team_id}/active-meeting")
def active_meeting(team_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    verify_team_access(team_id=team_id, write=False, current_user=user, db=db)
    meeting = get_active_meeting(db, team_id)
    data = serialize_state(db, meeting) if meeting else None
    return ApiResponse.success(data, "Active meeting" if data else "No active meeting")


@router.get("/meetings/{meeting_id}")
def meeting_state(meeting_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    meeting = get_meeting(db, meeting_id)
    verify_team_access(team_id=meeting.team_id, write=False, current_user=user, db=db)
    return ApiResponse.success(serialize_state(db, meeting), "Meeting state")


@router.post("/meetings/{meeting_id}/join")
def join(meeting_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    meeting = get_meeting(db, meeting_id)
    verify_team_access(team_id=meeting.team_id, write=False, current_user=user, db=db)
    join_meeting(db, meeting, user)
    return ApiResponse.success(serialize_state(db, meeting), "Joined meeting")


@router.post("/meetings/{meeting_id}/advance")
def advance(meeting_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    meeting = get_meeting(db, meeting_id)
    verify_team_access(team_id=meeting.team_id, write=True, current_user=user, db=db)
    meeting = advance_meeting(db, meeting_id, user)
    return ApiResponse.success(serialize_state(db, meeting), "Section advanced")


@router.post("/meetings/{meeting_id}/end")
def end(meeting_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    meeting = get_meeting(db, meeting_id)
    verify_team_access(team_id=meeting.team_id, write=True, current_user=user, db=db)
    meeting = end_meeting(db, meeting_id, user)
    return ApiResponse.success(serialize_state(db, meeting), "Meeting ended")


@router.put("/meetings/{meeting_id}/rating")
def rate(meeting_id: str, body: RatingInput, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    meeting = get_meeting(db, meeting_id)
    verify_team_access(team_id=meeting.team_id, write=True, current_user=user, db=db)
    meeting = set_rating(db, meeting, user, body.rating)
    return ApiResponse.success(serialize_state(db, meeting), "Rating saved")


@router.get("/meetings/{meeting_id}/summary")
def meeting_summary(meeting_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return an ended meeting's summary (frozen snapshot, or computed for seeded
    meetings). Available for any ended meeting, including seeded mt1/mt2."""
    meeting = get_meeting(db, meeting_id)
    verify_team_access(team_id=meeting.team_id, write=False, current_user=user, db=db)
    return ApiResponse.success(get_meeting_summary(db, meeting), "Meeting summary")


@router.get("/meetings/{meeting_id}/events")
async def meeting_events(meeting_id: str, user_id: Optional[str] = None):
    """SSE stream: an immediate ``meeting_state`` snapshot (recovery for late
    joins, refreshes and reconnects), then live events until disconnect."""
    # Short-lived session for auth + the initial snapshot; released before the
    # stream blocks, so an open SSE connection never holds a pooled connection.
    db = SessionLocal()
    try:
        user = _resolve_user(db, user_id)
        meeting = get_meeting(db, meeting_id)
        verify_team_access(team_id=meeting.team_id, write=False, current_user=user, db=db)
        snapshot = serialize_state(db, meeting)
    finally:
        db.close()

    broadcaster.bind_loop(asyncio.get_running_loop())
    queue = broadcaster.subscribe(meeting_id)

    async def event_stream():
        try:
            yield _sse("meeting_state", snapshot)
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
                    yield _sse(event["type"], event["data"])
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        finally:
            broadcaster.unsubscribe(meeting_id, queue)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
