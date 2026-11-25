"""ADR0011 backend additions: seeded-user list, team-member list, and the
last-closed-week To-Do completion rate. Runs against the configured PostgreSQL
database via the HTTP client.
"""
import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.domain.report import generate_rules_report

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


@requires_pg
def test_list_seeded_users():
    res = client.get("/api/v1/auth/users")
    assert res.status_code == 200
    users = res.json()["data"]
    assert [u["id"] for u in users] == [f"u{i}" for i in range(1, 10)]
    assert {u["role"] for u in users} == {"admin", "team_member", "observer"}


@requires_pg
def test_team_members_are_admins_and_team_members():
    res = client.get("/api/v1/teams/team_ops/members", headers={"X-User-Id": "u1"})
    assert res.status_code == 200
    ids = {u["id"] for u in res.json()["data"]}
    # u1 is the company admin; u4/u8/u9 are team_ops team members.
    assert ids == {"u1", "u4", "u8", "u9"}
    assert "observer" not in {u["role"] for u in res.json()["data"]}


@requires_pg
def test_team_members_requires_read_access():
    # u6 is a team_sales member only.
    res = client.get("/api/v1/teams/team_ops/members", headers={"X-User-Id": "u6"})
    assert res.status_code == 403


@requires_pg
def test_todo_completion_rate_is_last_closed_week():
    db = SessionLocal()
    try:
        report = generate_rules_report(db)
        last_closed = "2026-11-02"  # last closed week as of APP_NOW (2026-11-11)
        week = report["teams"]["team_lead"]["todo_completion"][last_closed]
    finally:
        db.close()
    expected = (week["rate_percent"] / 100) if week else None

    res = client.get("/api/v1/teams/team_lead/todos", headers={"X-User-Id": "u1"})
    assert res.status_code == 200
    assert res.json()["data"]["completion_rate"] == expected
