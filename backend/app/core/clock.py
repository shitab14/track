from datetime import datetime, timezone
import pytz
from app.core.config import settings

def get_app_now_utc() -> datetime:
    """Returns the current simulated time as a timezone-aware UTC datetime.
    
    Reads from settings.APP_NOW (ISO 8601).
    """
    raw_now = settings.APP_NOW
    if raw_now.endswith("Z"):
        raw_now = raw_now[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw_now)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def get_company_tz():
    """Returns the pytz timezone object for the company."""
    return pytz.timezone(settings.COMPANY_TIMEZONE)

def get_app_now_company() -> datetime:
    """Returns current simulated time in company timezone."""
    return get_app_now_utc().astimezone(get_company_tz())
