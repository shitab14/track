"""ADR0009: Level 10 Meeting state machine, authorization, and real-time push.

Deterministic state-machine and broadcaster tests run on an isolated, freshly
seeded in-memory SQLite database. Endpoint authorization and the SSE
snapshot-on-connect run against the configured PostgreSQL database via the HTTP
client, and any meeting created there is removed in teardown (the seed has no
meetings for team_ops/team_sales; mt1/mt2 belong to team_lead).
"""
import asyncio
import json

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import Base, SessionLocal
from app.db.seed import seed_database
from app.models import Meeting, MeetingAttendee, User
from app.core.broadcaster import broadcaster
from app.services.meetings import (
    advance_meeting,
    end_meeting,
    get_active_meeting,
    set_rating,
    start_meeting,
)

client = TestClient(app)


def _pg_available() -> bool:
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception:
        return False


requires_pg = pytest.mark.skipif(
    not _pg_available(), reason="Configured PostgreSQL database is not reachable"
)


@pytest.fixture
def sdb():
    """Isolated, freshly seeded in-memory SQLite session."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    seed_database(session)
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def clean_meetings():
    """Removes any meetings created on team_ops/team_sales against the shared DB
    before and after a test (cascade removes attendees and ratings)."""
    def _wipe():
        db = SessionLocal()
        try:
            db.query(Meeting).filter(Meeting.team_id.in_(["team_ops", "team_sales"])).delete(
                synchronize_session=False
            )
            db.commit()
        finally:
            db.close()

    _wipe()
    yield
    _wipe()


# ==========================================================================
# State machine (deterministic, isolated SQLite)
# ==========================================================================
def test_start_is_idempotent_per_team(sdb):
    u4 = sdb.query(User).filter_by(id="u4").first()
    first, created_first = start_meeting(sdb, "team_ops", u4)
    second, created_second = start_meeting(sdb, "team_ops", u4)

    assert created_first is True
    assert created_second is False
    assert first.id == second.id
    assert get_active_meeting(sdb, "team_ops").id == first.id


def test_advance_follows_section_order(sdb):
    u4 = sdb.query(User).filter_by(id="u4").first()
    meeting, _ = start_meeting(sdb, "team_ops", u4)
    assert meeting.current_section == "scorecard"

    assert advance_meeting(sdb, meeting.id, u4).current_section == "ids"
    assert advance_meeting(sdb, meeting.id, u4).current_section == "conclude"

    ended = advance_meeting(sdb, meeting.id, u4)
    assert ended.current_section == "ended"
    assert ended.ended_at is not None
    assert get_active_meeting(sdb, "team_ops") is None  # no longer active


def test_non_facilitator_cannot_advance(sdb):
    u4 = sdb.query(User).filter_by(id="u4").first()
    u8 = sdb.query(User).filter_by(id="u8").first()  # team_ops member, not facilitator
    meeting, _ = start_meeting(sdb, "team_ops", u4)

    with pytest.raises(HTTPException) as exc:
        advance_meeting(sdb, meeting.id, u8)
    assert exc.value.status_code == 403


def test_advance_and_rating_rejected_after_end(sdb):
    u4 = sdb.query(User).filter_by(id="u4").first()
    meeting, _ = start_meeting(sdb, "team_ops", u4)
    end_meeting(sdb, meeting.id, u4)

    with pytest.raises(HTTPException) as adv:
        advance_meeting(sdb, meeting.id, u4)
    assert adv.value.status_code == 409

    with pytest.raises(HTTPException) as rate:
        set_rating(sdb, meeting, u4, 8)
    assert rate.value.status_code == 409


def test_rating_upsert_and_average(sdb):
    u2 = sdb.query(User).filter_by(id="u2").first()  # team_sales member -> attendee via start
    meeting, _ = start_meeting(sdb, "team_sales", u2)

    set_rating(sdb, meeting, u2, 8)
    state = _state(sdb, meeting)
    assert state["ratings"]["average"] == 8.0
    assert state["ratings"]["count"] == 1

    set_rating(sdb, meeting, u2, 9)  # change own rating -> upsert, not a second row
    state = _state(sdb, meeting)
    assert state["ratings"]["average"] == 9.0
    assert state["ratings"]["count"] == 1


def test_non_attendee_cannot_rate(sdb):
    u2 = sdb.query(User).filter_by(id="u2").first()
    u6 = sdb.query(User).filter_by(id="u6").first()  # team_sales member but not joined
    meeting, _ = start_meeting(sdb, "team_sales", u2)

    with pytest.raises(HTTPException) as exc:
        set_rating(sdb, meeting, u6, 7)
    assert exc.value.status_code == 403


def _state(db, meeting):
    from app.services.meetings import serialize_state

    return serialize_state(db, meeting)


# ==========================================================================
# Real-time broadcaster
# ==========================================================================
def test_broadcaster_delivers_published_event():
    async def scenario():
        broadcaster.bind_loop(asyncio.get_running_loop())
        queue = broadcaster.subscribe("mt_test")
        broadcaster.publish("mt_test", {"type": "meeting_state", "data": {"section": "ids"}})
        event = await asyncio.wait_for(queue.get(), timeout=1)
        broadcaster.unsubscribe("mt_test", queue)
        return event

    event = asyncio.run(scenario())
    assert event["type"] == "meeting_state"
    assert event["data"]["section"] == "ids"


def test_advance_pushes_state_to_subscriber():
    """End-to-end on the loop: a subscriber receives a meeting_state carrying the
    new section when the facilitator advances."""
    async def scenario():
        engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = Session()
        seed_database(db)
        try:
            u4 = db.query(User).filter_by(id="u4").first()
            meeting, _ = start_meeting(db, "team_ops", u4)
            broadcaster.bind_loop(asyncio.get_running_loop())
            queue = broadcaster.subscribe(meeting.id)
            advance_meeting(db, meeting.id, u4)  # publishes meeting_state
            event = await asyncio.wait_for(queue.get(), timeout=1)
            broadcaster.unsubscribe(meeting.id, queue)
            return event
        finally:
            db.close()
            Base.metadata.drop_all(bind=engine)

    event = asyncio.run(scenario())
    assert event["type"] == "meeting_state"
    assert event["data"]["section"] == "ids"


# ==========================================================================
# Endpoints: authorization + SSE snapshot (PostgreSQL via HTTP)
# ==========================================================================
@requires_pg
def test_start_and_state_endpoints(clean_meetings):
    res = client.post("/api/v1/teams/team_ops/meetings", headers={"X-User-Id": "u4"})
    assert res.status_code == 200
    assert res.json()["message"] == "Meeting started"
    state = res.json()["data"]
    assert state["section"] == "scorecard"
    assert state["facilitator_id"] == "u4"
    meeting_id = state["id"]

    # Second start returns the same active meeting idempotently.
    again = client.post("/api/v1/teams/team_ops/meetings", headers={"X-User-Id": "u4"})
    assert again.json()["message"] == "Meeting already active"
    assert again.json()["data"]["id"] == meeting_id

    got = client.get(f"/api/v1/meetings/{meeting_id}", headers={"X-User-Id": "u8"})
    assert got.status_code == 200
    assert got.json()["data"]["id"] == meeting_id


@requires_pg
def test_non_facilitator_advance_refused(clean_meetings):
    start = client.post("/api/v1/teams/team_ops/meetings", headers={"X-User-Id": "u4"})
    meeting_id = start.json()["data"]["id"]

    # u8 is a team_ops member (write access) but not the facilitator.
    res = client.post(f"/api/v1/meetings/{meeting_id}/advance", headers={"X-User-Id": "u8"})
    assert res.status_code == 403


@requires_pg
def test_observer_cannot_rate(clean_meetings):
    # u2 (team_sales member) starts; u7 (observer of team_sales) joins then rates.
    start = client.post("/api/v1/teams/team_sales/meetings", headers={"X-User-Id": "u2"})
    meeting_id = start.json()["data"]["id"]

    joined = client.post(f"/api/v1/meetings/{meeting_id}/join", headers={"X-User-Id": "u7"})
    assert joined.status_code == 200  # observers may read/join

    rated = client.put(
        f"/api/v1/meetings/{meeting_id}/rating", headers={"X-User-Id": "u7"}, json={"rating": 9}
    )
    assert rated.status_code == 403  # observers cannot write


@requires_pg
def test_non_member_cannot_open_stream(clean_meetings):
    start = client.post("/api/v1/teams/team_ops/meetings", headers={"X-User-Id": "u4"})
    meeting_id = start.json()["data"]["id"]

    # u6 is a team_sales member only -> no read access to a team_ops meeting.
    res = client.get(f"/api/v1/meetings/{meeting_id}/events", params={"user_id": "u6"})
    assert res.status_code == 403


@requires_pg
def test_sse_snapshot_on_connect(clean_meetings):
    from app.api.v1.meetings import meeting_events

    start = client.post("/api/v1/teams/team_ops/meetings", headers={"X-User-Id": "u4"})
    meeting_id = start.json()["data"]["id"]

    async def scenario():
        response = await meeting_events(meeting_id, user_id="u4")
        body = response.body_iterator
        try:
            # First chunk is the snapshot; bound the read so a stall fails fast.
            chunk = await asyncio.wait_for(body.__anext__(), timeout=5)
        finally:
            await body.aclose()  # runs the generator's finally -> unsubscribe
        return chunk

    chunk = asyncio.run(scenario())

    assert "event: meeting_state" in chunk
    data_line = next(ln for ln in chunk.splitlines() if ln.startswith("data:"))
    data = json.loads(data_line.split(":", 1)[1].strip())
    assert data["id"] == meeting_id
    assert data["section"] == "scorecard"
