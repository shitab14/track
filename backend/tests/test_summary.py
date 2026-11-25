"""ADR0010: meeting summary — parity, immutability, attribution, serving.

Parity and endpoint/authorization run against the configured PostgreSQL database;
immutability and attribution run deterministically on isolated seeded SQLite.
Meetings created against the shared DB are removed in teardown (the seed has no
meetings for team_ops/team_sales; mt1/mt2 belong to team_lead).
"""
from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import Base, SessionLocal
from app.db.seed import seed_database
from app.models import Meeting, Score, Team, User
from app.domain.report import generate_rules_report
from app.services.issues import create_issue, get_issue_for_write, solve_issue
from app.services.todos import create_todo
from app.services.meetings import (
    end_meeting,
    get_meeting,
    get_meeting_summary,
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
# Parity: the API summary equals the rules report (seeded meetings)
# ==========================================================================
@requires_pg
def test_seeded_summary_matches_rules_report():
    db = SessionLocal()
    try:
        report = generate_rules_report(db)
        for mid in ("mt1", "mt2"):
            meeting = get_meeting(db, mid)
            assert get_meeting_summary(db, meeting) == report["teams"]["team_lead"]["meetings"][mid]
    finally:
        db.close()


@requires_pg
def test_summary_endpoint_and_authorization():
    ok = client.get("/api/v1/meetings/mt2/summary", headers={"X-User-Id": "u1"})
    assert ok.status_code == 200
    assert ok.json()["data"]["scorecard_week"] == "2026-10-26"
    assert ok.json()["data"]["rating"] == 8.3

    # u6 is team_sales only -> cannot read a team_lead meeting.
    denied = client.get("/api/v1/meetings/mt2/summary", headers={"X-User-Id": "u6"})
    assert denied.status_code == 403


@requires_pg
def test_summary_requires_ended_meeting(clean_meetings):
    start = client.post("/api/v1/teams/team_ops/meetings", headers={"X-User-Id": "u4"})
    meeting_id = start.json()["data"]["id"]
    res = client.get(f"/api/v1/meetings/{meeting_id}/summary", headers={"X-User-Id": "u4"})
    assert res.status_code == 409


# ==========================================================================
# Attribution + immutability (deterministic, isolated SQLite)
# ==========================================================================
def _run_live_meeting(db):
    """Start a team_ops meeting, solve a new issue and add a to-do during it, then
    end it. Returns (meeting, issue_id, todo_id)."""
    u4 = db.query(User).filter_by(id="u4").first()
    team = db.query(Team).filter_by(id="team_ops").first()
    meeting, _ = start_meeting(db, "team_ops", u4)

    issue_id = create_issue(db, team, u4, "Ops throughput dip", 3)["id"]
    issue = get_issue_for_write(db, issue_id)
    solve_issue(db, issue, "Rebalanced the queue")
    todo_id = create_todo(db, issue, u4, "Document the fix", u4.id, None)["id"]

    end_meeting(db, meeting.id, u4)
    return meeting, issue_id, todo_id


def test_attribution_captured_in_summary(sdb):
    meeting, issue_id, todo_id = _run_live_meeting(sdb)

    # Attribution links were set during the meeting.
    assert get_issue_for_write(sdb, issue_id).solved_in_meeting_id == meeting.id

    summary = get_meeting_summary(sdb, meeting)
    assert issue_id in summary["issues_solved"]
    assert todo_id in summary["todos_created"]
    # Live conclusion references APP_NOW's last closed week.
    assert summary["scorecard_week"] == "2026-11-02"


def test_solve_outside_meeting_is_not_attributed(sdb):
    u4 = sdb.query(User).filter_by(id="u4").first()
    team = sdb.query(Team).filter_by(id="team_ops").first()
    issue_id = create_issue(sdb, team, u4, "Standalone issue", 2)["id"]
    issue = get_issue_for_write(sdb, issue_id)
    solve_issue(sdb, issue, "no meeting running")
    assert get_issue_for_write(sdb, issue_id).solved_in_meeting_id is None


def test_summary_is_immutable_after_score_edit(sdb):
    meeting, _, _ = _run_live_meeting(sdb)
    before = get_meeting_summary(sdb, meeting)
    week = date.fromisoformat(before["scorecard_week"])

    # Tamper with the inputs the summary was computed from.
    sdb.query(Score).filter_by(measurable_id="m7", week_start=week).delete()
    sdb.commit()

    after = get_meeting_summary(sdb, meeting)
    assert after == before  # served from the frozen snapshot, unaffected by edits


def test_summary_requires_ended_meeting_service(sdb):
    u4 = sdb.query(User).filter_by(id="u4").first()
    meeting, _ = start_meeting(sdb, "team_ops", u4)
    with pytest.raises(HTTPException) as exc:
        get_meeting_summary(sdb, meeting)
    assert exc.value.status_code == 409
