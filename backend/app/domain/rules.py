from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime
from typing import Optional, Union, List, Tuple
from app.models import Issue, Todo, Rock

def round_half_up(val: Union[float, Decimal, int], decimals: int = 0) -> Union[int, float]:
    """Rounds half up: 12.5% -> 13%, 8.25 -> 8.3."""
    d = Decimal(str(val))
    target = Decimal("1") if decimals == 0 else Decimal("10") ** -decimals
    rounded = d.quantize(target, rounding=ROUND_HALF_UP)
    return int(rounded) if decimals == 0 else float(rounded)

def compute_measurable_status(
    goal_type: str,
    goal_value: Optional[Decimal],
    goal_min: Optional[Decimal],
    goal_max: Optional[Decimal],
    score_value: Optional[Decimal],
    is_closed_week: bool,
) -> str:
    """Computes the status of a measurable for a given week.
    
    Status values: 'on_track', 'off_track', 'pending'.
    Rules:
    - Boundaries are on track.
    - A closed week with no score is off track.
    - The current week (or unclosed) with no score is pending.
    """
    if score_value is None:
        return "off_track" if is_closed_week else "pending"

    if goal_type == "at_least":
        if goal_value is not None and score_value >= goal_value:
            return "on_track"
        return "off_track"

    elif goal_type == "at_most":
        if goal_value is not None and score_value <= goal_value:
            return "on_track"
        return "off_track"

    elif goal_type == "between":
        if goal_min is not None and goal_max is not None:
            if goal_min <= score_value <= goal_max:
                return "on_track"
        return "off_track"

    elif goal_type == "exactly":
        if goal_value is not None and score_value == goal_value:
            return "on_track"
        return "off_track"

    return "off_track"

def compute_todo_completion_rate(
    todos_due: List[Todo],
    week_end_utc: datetime,
) -> Optional[dict]:
    """Computes To-Do completion rate for a week.
    
    Rules:
    - Done by the end of a week ÷ To-Dos due that week.
    - Target is 90%. Exactly 90% meets target.
    - Done after its due week counts as not done.
    - Zero due means no rate (returns None / null).
    - Rate percent is whole number rounded half up.
    - meets_target compares the exact ratio with 90%, not the rounded percent.
    """
    due_count = len(todos_due)
    if due_count == 0:
        return None

    done_count = sum(
        1 for t in todos_due
        if t.done_at is not None and t.done_at <= week_end_utc
    )

    exact_ratio = Decimal(str(done_count)) / Decimal(str(due_count))
    rate_percent = round_half_up(exact_ratio * Decimal("100"), 0)
    meets_target = exact_ratio >= Decimal("0.90")

    return {
        "due": due_count,
        "done": done_count,
        "rate_percent": rate_percent,
        "meets_target": meets_target,
    }

def compute_rock_status_and_progress(
    rock: Rock,
    today_company: date,
) -> Tuple[str, int]:
    """Computes status ('complete' | 'off_track' | 'on_track') and progress percent for a Rock.
    
    Rules:
    - Complete if seeded status is 'complete'.
    - Off-track if seeded status is 'off_track', or if an unfinished Milestone is past due (due_date < today).
    - A Milestone due today is NOT past due.
    - Otherwise On-track.
    - Progress: Completed Milestones ÷ total Milestones, as a whole percent rounded half up.
    - No Milestones: 0%, or 100% once Complete.
    """
    milestones = rock.milestones or []
    total_ms = len(milestones)

    # Calculate status
    if rock.status == "complete":
        computed_status = "complete"
    elif rock.status == "off_track":
        computed_status = "off_track"
    else:
        # Check if any unfinished milestone is past due
        has_past_due = any(
            (not ms.done and ms.due_date < today_company)
            for ms in milestones
        )
        computed_status = "off_track" if has_past_due else "on_track"

    # Calculate progress percent
    if total_ms == 0:
        progress_pct = 100 if computed_status == "complete" else 0
    else:
        done_ms = sum(1 for ms in milestones if ms.done)
        progress_pct = round_half_up((Decimal(str(done_ms)) / Decimal(str(total_ms))) * Decimal("100"), 0)

    return computed_status, progress_pct

def sort_issues(issues: List[Issue]) -> List[Issue]:
    """Sorts issues in strict EOS Issue order:
    
    Rules:
    - Priority 5 first, down to 1.
    - Within a priority, oldest first (created_at ascending).
    - No priority comes last, sorted oldest first.
    """
    def issue_sort_key(issue: Issue):
        # Category 0: has priority (sort desc by priority)
        # Category 1: priority is None
        has_no_priority = 1 if issue.priority is None else 0
        priority_val = -(issue.priority or 0)
        return (has_no_priority, priority_val, issue.created_at)

    return sorted(issues, key=issue_sort_key)

def compute_meeting_rating(ratings: List[int]) -> Optional[float]:
    """Computes average of submitted meeting ratings to one decimal place, rounded half up.
    
    Rules:
    - Excludes attendees who didn't rate.
    - No ratings means no score (None / null).
    """
    if not ratings:
        return None
    total = sum(ratings)
    count = len(ratings)
    exact_avg = Decimal(str(total)) / Decimal(str(count))
    return round_half_up(exact_avg, 1)
