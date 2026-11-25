from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.core import clock
from app.domain import rules
from app.domain.summary import compute_meeting_summary
from app.models import (
    Team,
    Measurable,
    Score,
    Todo,
    Rock,
    Issue,
    Meeting,
)

def generate_rules_report(db: Session, now_utc: Optional[datetime] = None) -> Dict[str, Any]:
    """Generates the exact rules report dictionary matching task_resources/README.md specification."""
    current_now_utc = now_utc or clock.get_app_now_utc()
    today_company = clock.get_today_company(current_now_utc)
    current_week_start = clock.get_current_week_start(current_now_utc)
    thirteen_weeks = clock.get_13_weeks_range(current_week_start, current_now_utc)
    thirteen_weeks_str = [w.isoformat() for w in thirteen_weeks]

    teams = db.query(Team).order_by(Team.id).all()
    report_teams: Dict[str, Any] = {}

    for team in teams:
        # 1. Measurable Status for 13 weeks
        team_measurables = db.query(Measurable).filter_by(team_id=team.id).order_by(Measurable.id).all()
        measurable_status: Dict[str, Dict[str, str]] = {}

        for m in team_measurables:
            measurable_status[m.id] = {}
            # Fetch all scores for this measurable
            scores_by_week = {
                s.week_start.isoformat(): s.value
                for s in db.query(Score).filter_by(measurable_id=m.id).all()
            }

            for week_dt in thirteen_weeks:
                w_str = week_dt.isoformat()
                score_val = scores_by_week.get(w_str)
                is_closed = week_dt < current_week_start
                status = rules.compute_measurable_status(
                    goal_type=m.goal_type,
                    goal_value=m.goal_value,
                    goal_min=m.goal_min,
                    goal_max=m.goal_max,
                    score_value=score_val,
                    is_closed_week=is_closed,
                )
                measurable_status[m.id][w_str] = status

        # 2. To-Do Completion for 13 weeks
        todo_completion: Dict[str, Any] = {}
        all_team_todos = db.query(Todo).filter_by(team_id=team.id).all()

        for week_dt in thirteen_weeks:
            w_str = week_dt.isoformat()
            week_start_utc, week_end_utc = clock.get_week_range(week_dt)
            # Find todos due that week (Monday to Sunday in company time)
            week_sunday = week_dt.fromordinal(week_dt.toordinal() + 6)
            todos_due_in_week = [
                t for t in all_team_todos
                if week_dt <= t.due_date <= week_sunday
            ]
            rate_data = rules.compute_todo_completion_rate(todos_due_in_week, week_end_utc)
            todo_completion[w_str] = rate_data

        # 3. Overdue To-Dos (sorted plain strings)
        overdue_todos = [
            t.id for t in all_team_todos
            if clock.is_overdue(t.due_date, t.done_at, current_now_utc)
        ]
        overdue_todos.sort()

        # 4. Rocks status and progress
        team_rocks = db.query(Rock).filter_by(team_id=team.id).order_by(Rock.id).all()
        rocks_report: Dict[str, Dict[str, Any]] = {}
        for r in team_rocks:
            status, progress = rules.compute_rock_status_and_progress(r, today_company)
            rocks_report[r.id] = {
                "status": status,
                "progress_percent": progress,
            }

        # 5. Issue Order (strictly unsolved issues in issue order)
        unsolved_issues = db.query(Issue).filter_by(team_id=team.id).filter(Issue.solved_at.is_(None)).all()
        sorted_issues = rules.sort_issues(unsolved_issues)
        issue_order = [iss.id for iss in sorted_issues]

        # 6. Ended Meetings
        ended_meetings = db.query(Meeting).filter_by(team_id=team.id).filter(Meeting.ended_at.isnot(None)).order_by(Meeting.id).all()
        meetings_report: Dict[str, Any] = {}

        for mt in ended_meetings:
            # Reference instant is the meeting's own start (seeded meetings carry
            # business-timeline timestamps); in-meeting lists use the timestamp
            # window. Shared with the API via compute_meeting_summary (ADR0010).
            meetings_report[mt.id] = compute_meeting_summary(db, mt, as_of_utc=mt.started_at)

        report_teams[team.id] = {
            "measurable_status": measurable_status,
            "todo_completion": todo_completion,
            "overdue_todos": overdue_todos,
            "rocks": rocks_report,
            "issue_order": issue_order,
            "meetings": meetings_report,
        }

    return {
        "now": current_now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "teams": report_teams,
    }
