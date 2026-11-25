from decimal import Decimal
from datetime import date, datetime, timezone
from app.domain import rules
from app.models import Issue, Todo, Rock, Milestone

def test_round_half_up():
    assert rules.round_half_up(12.5, 0) == 13
    assert rules.round_half_up(12.4, 0) == 12
    assert rules.round_half_up(8.25, 1) == 8.3
    assert rules.round_half_up(8.24, 1) == 8.2

def test_measurable_status_boundaries():
    # at_least 10
    assert rules.compute_measurable_status("at_least", Decimal("10"), None, None, Decimal("10"), False) == "on_track"
    assert rules.compute_measurable_status("at_least", Decimal("10"), None, None, Decimal("9.99"), False) == "off_track"

    # at_most 3.0
    assert rules.compute_measurable_status("at_most", Decimal("3.0"), None, None, Decimal("3.0"), False) == "on_track"
    assert rules.compute_measurable_status("at_most", Decimal("3.0"), None, None, Decimal("3.01"), False) == "off_track"

    # between 2 and 4
    assert rules.compute_measurable_status("between", None, Decimal("2"), Decimal("4"), Decimal("2.0"), False) == "on_track"
    assert rules.compute_measurable_status("between", None, Decimal("2"), Decimal("4"), Decimal("4.0"), False) == "on_track"
    assert rules.compute_measurable_status("between", None, Decimal("2"), Decimal("4"), Decimal("1.99"), False) == "off_track"
    assert rules.compute_measurable_status("between", None, Decimal("2"), Decimal("4"), Decimal("4.01"), False) == "off_track"

    # exactly 1
    assert rules.compute_measurable_status("exactly", Decimal("1"), None, None, Decimal("1"), False) == "on_track"
    assert rules.compute_measurable_status("exactly", Decimal("1"), None, None, Decimal("0"), False) == "off_track"

    # Missing scores
    assert rules.compute_measurable_status("at_least", Decimal("10"), None, None, None, is_closed_week=True) == "off_track"
    assert rules.compute_measurable_status("at_least", Decimal("10"), None, None, None, is_closed_week=False) == "pending"

def test_todo_completion_rate():
    week_end = datetime(2026, 11, 8, 23, 59, 59, tzinfo=timezone.utc)

    # Zero due -> None
    assert rules.compute_todo_completion_rate([], week_end) is None

    # 10 due, 9 done within week -> 90%, meets_target True
    t_due_10 = [
        Todo(id=f"t_{i}", team_id="team_lead", owner_id="u1", title="test", due_date=date(2026, 11, 4),
             done_at=datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc) if i < 9 else None)
        for i in range(10)
    ]
    res_10 = rules.compute_todo_completion_rate(t_due_10, week_end)
    assert res_10["due"] == 10
    assert res_10["done"] == 9
    assert res_10["rate_percent"] == 90
    assert res_10["meets_target"] is True

    # 9 due, 8 done -> exact 8/9 = 88.88% -> 89%, meets_target False
    t_due_9 = [
        Todo(id=f"t_{i}", team_id="team_lead", owner_id="u1", title="test", due_date=date(2026, 11, 4),
             done_at=datetime(2026, 11, 6, 12, 0, tzinfo=timezone.utc) if i < 8 else None)
        for i in range(9)
    ]
    res_9 = rules.compute_todo_completion_rate(t_due_9, week_end)
    assert res_9["due"] == 9
    assert res_9["done"] == 8
    assert res_9["rate_percent"] == 89
    assert res_9["meets_target"] is False

    # Done after week end counts as not done
    t_late = [
        Todo(id="t_late", team_id="team_lead", owner_id="u1", title="test", due_date=date(2026, 11, 4),
             done_at=datetime(2026, 11, 9, 2, 0, tzinfo=timezone.utc)) # finished Monday after week ended
    ]
    res_late = rules.compute_todo_completion_rate(t_late, week_end)
    assert res_late["due"] == 1
    assert res_late["done"] == 0
    assert res_late["rate_percent"] == 0
    assert res_late["meets_target"] is False

def test_rock_status_and_progress():
    today = date(2026, 11, 11)

    # 1. Complete rock
    r_comp = Rock(id="r1", team_id="team_lead", owner_id="u1", title="ERP", quarter="2026-Q4", status="complete")
    status, progress = rules.compute_rock_status_and_progress(r_comp, today)
    assert status == "complete"
    assert progress == 100

    # 2. Rock with milestone due today (not past due)
    r_today = Rock(id="r2", team_id="team_lead", owner_id="u1", title="Portal", quarter="2026-Q4", status="on_track")
    r_today.milestones = [
        Milestone(id="ms1", rock_id="r2", title="Spec", due_date=date(2026, 10, 15), done=True),
        Milestone(id="ms2", rock_id="r2", title="Beta", due_date=today, done=False), # Due today
    ]
    status, progress = rules.compute_rock_status_and_progress(r_today, today)
    assert status == "on_track"
    assert progress == 50

    # 3. Rock with milestone due yesterday (past due) -> off_track
    r_past = Rock(id="r3", team_id="team_lead", owner_id="u1", title="Hire", quarter="2026-Q4", status="on_track")
    r_past.milestones = [
        Milestone(id="ms3", rock_id="r3", title="JD", due_date=date(2026, 10, 10), done=True),
        Milestone(id="ms4", rock_id="r3", title="Shortlist", due_date=date(2026, 11, 10), done=False), # Yesterday
        Milestone(id="ms5", rock_id="r3", title="Interviews", due_date=date(2026, 11, 20), done=False),
    ]
    status, progress = rules.compute_rock_status_and_progress(r_past, today)
    assert status == "off_track"
    # 1 done of 3 -> 33%
    assert progress == 33

def test_issue_sorting():
    i1 = Issue(id="i1", team_id="team_lead", owner_id="u1", title="Low priority", priority=1,
               created_at=datetime(2026, 10, 1, tzinfo=timezone.utc))
    i2 = Issue(id="i2", team_id="team_lead", owner_id="u1", title="High priority older", priority=5,
               created_at=datetime(2026, 10, 5, tzinfo=timezone.utc))
    i3 = Issue(id="i3", team_id="team_lead", owner_id="u1", title="High priority newer", priority=5,
               created_at=datetime(2026, 10, 10, tzinfo=timezone.utc))
    i4 = Issue(id="i4", team_id="team_lead", owner_id="u1", title="No priority", priority=None,
               created_at=datetime(2026, 9, 1, tzinfo=timezone.utc))

    sorted_list = rules.sort_issues([i1, i4, i3, i2])
    # Expect: i2 (P5 older), i3 (P5 newer), i1 (P1), i4 (None)
    assert [x.id for x in sorted_list] == ["i2", "i3", "i1", "i4"]

def test_meeting_rating():
    assert rules.compute_meeting_rating([]) is None
    assert rules.compute_meeting_rating([8, 9, 7]) == 8.0
    # Average of 8, 9, 8, 8 is 33/4 = 8.25 -> rounds half up to 8.3
    assert rules.compute_meeting_rating([8, 9, 8, 8]) == 8.3
