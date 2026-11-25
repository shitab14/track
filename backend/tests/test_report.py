import pytest
from app.db.session import SessionLocal
from app.domain.report import generate_rules_report
from app.core import clock

def test_generate_rules_report_structure():
    db = SessionLocal()
    try:
        report = generate_rules_report(db)

        # 1. Root structure
        assert "now" in report
        assert report["now"] == "2026-11-11T15:00:00Z"
        assert "teams" in report
        assert set(report["teams"].keys()) == {"team_lead", "team_sales", "team_ops"}

        lead = report["teams"]["team_lead"]
        # 2. Team lead components
        assert "measurable_status" in lead
        assert "todo_completion" in lead
        assert "overdue_todos" in lead
        assert "rocks" in lead
        assert "issue_order" in lead
        assert "meetings" in lead

        # 3. Measurables 13 weeks
        assert "m1" in lead["measurable_status"]
        assert len(lead["measurable_status"]["m1"]) == 13
        assert "2026-11-09" in lead["measurable_status"]["m1"]
        assert "2026-08-17" in lead["measurable_status"]["m1"]

        # 4. To-Do completion 13 weeks
        assert len(lead["todo_completion"]) == 13
        # Check specific week with todos
        w_oct26 = lead["todo_completion"]["2026-10-26"]
        assert w_oct26 is not None
        assert "due" in w_oct26
        assert "done" in w_oct26
        assert "rate_percent" in w_oct26
        assert "meets_target" in w_oct26

        # 5. Overdue todos
        assert isinstance(lead["overdue_todos"], list)
        assert lead["overdue_todos"] == sorted(lead["overdue_todos"])
        # t12 is due 2026-11-01 and done_at is null -> overdue
        assert "t12" in lead["overdue_todos"]
        # t30 is due 2026-11-11 (today) and not done -> NOT overdue
        assert "t30" not in lead["overdue_todos"]

        # 6. Rocks
        assert "r1" in lead["rocks"]
        assert lead["rocks"]["r1"]["status"] in ["on_track", "off_track", "complete"]
        assert isinstance(lead["rocks"]["r1"]["progress_percent"], int)

        # 7. Issue order
        assert isinstance(lead["issue_order"], list)
        # Unsolved issues: i1, i2, i3, i4, i5
        assert len(lead["issue_order"]) == 5
        # i4 has null priority, must be last
        assert lead["issue_order"][-1] == "i4"

        # 8. Ended Meetings
        assert "mt1" in lead["meetings"]
        assert "mt2" in lead["meetings"]
        mt1 = lead["meetings"]["mt1"]
        assert mt1["scorecard_week"] == "2026-10-19" # closed week prior to 2026-10-28
        assert mt1["rating"] == 8.0 # (8+9+7)/3 = 8.0
        assert mt1["attendee_ids"] == sorted(mt1["attendee_ids"])

        mt2 = lead["meetings"]["mt2"]
        assert mt2["scorecard_week"] == "2026-10-26" # closed week prior to 2026-11-04
        assert mt2["rating"] == 8.3 # (8+9+8+8)/4 = 33/4 = 8.25 -> 8.3
        assert mt2["todos_created"] == ["t30"]
        assert mt2["issues_solved"] == ["i6"]

    finally:
        db.close()
