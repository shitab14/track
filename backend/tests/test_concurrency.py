"""ADR0008: Concurrency and idempotency for "Make it an Issue".

Covers the four cases named in the ADR's Verification section:
  1. Sequential repeat requests stay idempotent.
  2. Two (or more) concurrent requests yield a single unsolved Issue.
  3. Re-promoting a score whose source Issue is solved creates a new Issue.
  4. Authorization: cross-team read and Observer write are refused server-side.

Deterministic cases run on an isolated, freshly seeded in-memory SQLite
database. The true concurrency race runs against the configured PostgreSQL
dialect (as ADR0008 requires), skipped when that database is unreachable.
Any Issue created against the shared database is removed in teardown so the
count-sensitive assertions in other suites are unaffected.
"""
import threading
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import Base, SessionLocal
from app.db.seed import seed_database
from app.models import Issue, Score, User
from app.services.issues import make_issue

client = TestClient(app)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _m7_score_id(db, week: date) -> int:
    """Resolve the integer score id for measurable m7 (team_ops) at a week."""
    score = db.query(Score).filter_by(measurable_id="m7", week_start=week).first()
    assert score is not None, f"expected a seeded m7 score for week {week}"
    return score.id


def _count_unsolved(db, measurable_id: str, week: date) -> int:
    return (
        db.query(Issue)
        .filter_by(source_measurable_id=measurable_id, source_week_start=week, solved_at=None)
        .count()
    )


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


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------
@pytest.fixture
def seeded_sqlite():
    """Isolated, freshly seeded in-memory SQLite database with the partial
    unique index (uq_unsolved_source_issue) created via the ORM metadata."""
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
def cleanup_m7():
    """Collects weeks touched against the shared DB and removes any m7 Issues
    for them afterwards, restoring the pre-test baseline."""
    weeks: list[date] = []
    yield weeks
    db = SessionLocal()
    try:
        for week in weeks:
            db.query(Issue).filter_by(source_measurable_id="m7", source_week_start=week).delete()
        db.commit()
    finally:
        db.close()


# --------------------------------------------------------------------------
# 1. Sequential idempotency (deterministic, isolated SQLite)
# --------------------------------------------------------------------------
def test_sequential_repeat_is_idempotent(seeded_sqlite):
    db = seeded_sqlite
    week = date(2026, 8, 17)
    score_id = _m7_score_id(db, week)
    user = db.query(User).filter_by(id="u4").first()

    first, created_first = make_issue(db, score_id, user)
    second, created_second = make_issue(db, score_id, user)

    assert created_first is True
    assert created_second is False
    assert first["id"] == second["id"]
    assert _count_unsolved(db, "m7", week) == 1


# --------------------------------------------------------------------------
# 3. Re-promotion after the source Issue is solved (deterministic SQLite)
# --------------------------------------------------------------------------
def test_solved_source_allows_new_issue(seeded_sqlite):
    db = seeded_sqlite
    week = date(2026, 8, 24)
    score_id = _m7_score_id(db, week)
    user = db.query(User).filter_by(id="u4").first()

    first, created_first = make_issue(db, score_id, user)
    assert created_first is True

    # Solve the first Issue (note is required by the schema check constraint).
    issue = db.query(Issue).filter_by(id=first["id"]).first()
    issue.solved_at = datetime(2026, 8, 30, 0, 0, 0, tzinfo=timezone.utc)
    issue.resolution_note = "handled"
    db.commit()

    second, created_second = make_issue(db, score_id, user)
    assert created_second is True
    assert second["id"] != first["id"]
    assert _count_unsolved(db, "m7", week) == 1  # only the new one is unsolved


# --------------------------------------------------------------------------
# 2. Concurrent promotion returns a single Issue (real PostgreSQL race)
# --------------------------------------------------------------------------
@requires_pg
def test_concurrent_make_issue_returns_single_issue(cleanup_m7):
    week = date(2026, 9, 7)
    cleanup_m7.append(week)

    # Clean any residue from a previous failed run for a deterministic start.
    pre = SessionLocal()
    try:
        pre.query(Issue).filter_by(source_measurable_id="m7", source_week_start=week).delete()
        pre.commit()
        score_id = _m7_score_id(pre, week)
    finally:
        pre.close()

    n_workers = 8
    barrier = threading.Barrier(n_workers)
    results: list[str] = []
    errors: list[Exception] = []
    lock = threading.Lock()

    def worker():
        db = SessionLocal()
        try:
            user = db.query(User).filter_by(id="u4").first()
            barrier.wait()  # line all threads up so the inserts truly race
            issue, _created = make_issue(db, score_id, user)
            with lock:
                results.append(issue["id"])
        except Exception as exc:  # pragma: no cover - surfaced via assert below
            with lock:
                errors.append(exc)
        finally:
            db.close()

    threads = [threading.Thread(target=worker) for _ in range(n_workers)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"workers raised: {errors}"
    assert len(results) == n_workers
    assert len(set(results)) == 1, "all concurrent callers must receive the same Issue id"

    check = SessionLocal()
    try:
        assert _count_unsolved(check, "m7", week) == 1
    finally:
        check.close()


# --------------------------------------------------------------------------
# 4. Authorization is enforced on the endpoint (real DB via HTTP)
# --------------------------------------------------------------------------
@requires_pg
def test_make_issue_cross_team_read_refused():
    # u6 is a Team Member of team_sales only; m7 belongs to team_ops.
    db = SessionLocal()
    try:
        score_id = _m7_score_id(db, date(2026, 9, 14))
    finally:
        db.close()

    res = client.post(f"/api/v1/scores/{score_id}/make-issue", headers={"X-User-Id": "u6"})
    assert res.status_code == 403
    assert res.json()["code"] == 403

    # Nothing was created.
    check = SessionLocal()
    try:
        assert _count_unsolved(check, "m7", date(2026, 9, 14)) == 0
    finally:
        check.close()


@requires_pg
def test_make_issue_observer_write_refused():
    # u5 is an Observer of team_lead; m1 belongs to team_lead.
    # Read is permitted, but the write (promotion) must be refused.
    db = SessionLocal()
    try:
        score = db.query(Score).filter_by(measurable_id="m1", week_start=date(2026, 8, 17)).first()
        score_id = score.id
    finally:
        db.close()

    res = client.post(f"/api/v1/scores/{score_id}/make-issue", headers={"X-User-Id": "u5"})
    assert res.status_code == 403
    assert res.json()["code"] == 403


@requires_pg
def test_make_issue_team_member_success_then_idempotent(cleanup_m7):
    week = date(2026, 9, 21)
    cleanup_m7.append(week)

    db = SessionLocal()
    try:
        db.query(Issue).filter_by(source_measurable_id="m7", source_week_start=week).delete()
        db.commit()
        score_id = _m7_score_id(db, week)
    finally:
        db.close()

    # u4 is a Team Member of team_ops -> allowed.
    first = client.post(f"/api/v1/scores/{score_id}/make-issue", headers={"X-User-Id": "u4"})
    assert first.status_code == 200
    assert first.json()["message"] == "Issue created"
    issue_id = first.json()["data"]["id"]

    second = client.post(f"/api/v1/scores/{score_id}/make-issue", headers={"X-User-Id": "u4"})
    assert second.status_code == 200
    assert second.json()["message"] == "Issue already exists"
    assert second.json()["data"]["id"] == issue_id

    check = SessionLocal()
    try:
        assert _count_unsolved(check, "m7", week) == 1
    finally:
        check.close()
