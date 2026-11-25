import os
from datetime import datetime, date, timedelta, timezone
from typing import Optional, Union, Tuple, List
import pytz
from app.core.config import settings

def get_app_now_utc(override_iso: Optional[str] = None) -> datetime:
    """Returns the current simulated time as a timezone-aware UTC datetime.
    
    Priority:
    1. override_iso parameter
    2. APP_NOW environment variable
    3. settings.APP_NOW
    4. Default fallback: '2026-11-11T15:00:00Z'
    """
    raw_now = override_iso or os.environ.get("APP_NOW") or settings.APP_NOW or "2026-11-11T15:00:00Z"
    if raw_now.endswith("Z"):
        raw_now = raw_now[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw_now)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def get_company_tz():
    """Returns the pytz timezone object for the company."""
    return pytz.timezone(settings.COMPANY_TIMEZONE)

def get_app_now_company(now_utc: Optional[datetime] = None) -> datetime:
    """Converts the UTC simulated time into company timezone (America/Chicago)."""
    utc_dt = now_utc or get_app_now_utc()
    return utc_dt.astimezone(get_company_tz())

def get_today_company(now_utc: Optional[datetime] = None) -> date:
    """Returns the calendar date of APP_NOW in company time."""
    return get_app_now_company(now_utc).date()

def get_week_start(d: Union[date, datetime]) -> date:
    """Given any date or datetime in company time, returns the Monday date of that week."""
    target_date = d.date() if isinstance(d, datetime) else d
    return target_date - timedelta(days=target_date.weekday())

def get_week_range(week_start: date) -> Tuple[datetime, datetime]:
    """Returns (start_utc, end_utc) for a given week_start Monday in company time.
    
    A week runs Monday 00:00:00 to Sunday 23:59:59.999999 in company time.
    """
    tz = get_company_tz()
    start_local = tz.localize(datetime(week_start.year, week_start.month, week_start.day, 0, 0, 0))
    sunday = week_start + timedelta(days=6)
    end_local = tz.localize(datetime(sunday.year, sunday.month, sunday.day, 23, 59, 59, 999999))
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)

def get_current_week_start(now_utc: Optional[datetime] = None) -> date:
    """Returns the Monday of the current week based on APP_NOW in company time."""
    return get_week_start(get_today_company(now_utc))

def get_last_closed_week_start(now_utc: Optional[datetime] = None) -> date:
    """Returns the Monday of the last closed week (full week before the current one)."""
    return get_current_week_start(now_utc) - timedelta(days=7)

def get_13_weeks_range(current_week: Optional[date] = None, now_utc: Optional[datetime] = None) -> List[date]:
    """Returns a list of 13 consecutive Monday dates ending with the current week."""
    cur_week = current_week or get_current_week_start(now_utc)
    return [cur_week - timedelta(weeks=12 - i) for i in range(13)]

def get_current_quarter(d: Optional[Union[date, datetime]] = None) -> str:
    """Returns the calendar quarter in format 'YYYY-QX' based on date in company time."""
    if d is None:
        target_date = get_today_company()
    elif isinstance(d, datetime):
        target_date = d.date()
    else:
        target_date = d
    quarter_num = (target_date.month - 1) // 3 + 1
    return f"{target_date.year}-Q{quarter_num}"

def is_overdue(due_date: date, done_at: Optional[datetime], now_utc: Optional[datetime] = None) -> bool:
    """A To-Do is overdue when it is not done and its due date is before today in company time."""
    if done_at is not None:
        return False
    today = get_today_company(now_utc)
    return due_date < today
