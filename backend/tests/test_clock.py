from datetime import date, datetime, timezone
import pytest
from app.core import clock

def test_default_app_now():
    now_utc = clock.get_app_now_utc()
    assert now_utc.isoformat() == "2026-11-11T15:00:00+00:00"
    
    # In America/Chicago, 15:00 UTC on Nov 11 is 09:00 AM CST (UTC-6)
    company_dt = clock.get_app_now_company(now_utc)
    assert company_dt.hour == 9
    assert company_dt.minute == 0
    assert clock.get_today_company(now_utc) == date(2026, 11, 11)

def test_week_calculations_at_default_now():
    now_utc = clock.get_app_now_utc()
    # Nov 11, 2026 is a Wednesday. Current week Monday is Nov 9, 2026.
    cur_week = clock.get_current_week_start(now_utc)
    assert cur_week == date(2026, 11, 9)
    
    # Last closed week Monday is Nov 2, 2026.
    last_closed = clock.get_last_closed_week_start(now_utc)
    assert last_closed == date(2026, 11, 2)
    
    # 13 weeks range ending with current week (2026-08-17 to 2026-11-09)
    weeks_13 = clock.get_13_weeks_range(now_utc=now_utc)
    assert len(weeks_13) == 13
    assert weeks_13[0] == date(2026, 8, 17)
    assert weeks_13[-1] == date(2026, 11, 9)

def test_week_boundary_transitions():
    # Sunday 2026-11-08 23:59:59 Chicago time -> Monday 2026-11-09 05:59:59 UTC
    sunday_utc = datetime(2026, 11, 9, 5, 59, 59, tzinfo=timezone.utc)
    assert clock.get_today_company(sunday_utc) == date(2026, 11, 8)
    assert clock.get_current_week_start(sunday_utc) == date(2026, 11, 2)

    # Monday 2026-11-09 00:00:00 Chicago time -> Monday 2026-11-09 06:00:00 UTC
    monday_utc = datetime(2026, 11, 9, 6, 0, 0, tzinfo=timezone.utc)
    assert clock.get_today_company(monday_utc) == date(2026, 11, 9)
    assert clock.get_current_week_start(monday_utc) == date(2026, 11, 9)

def test_quarter_calculation():
    assert clock.get_current_quarter(date(2026, 1, 15)) == "2026-Q1"
    assert clock.get_current_quarter(date(2026, 5, 20)) == "2026-Q2"
    assert clock.get_current_quarter(date(2026, 8, 30)) == "2026-Q3"
    assert clock.get_current_quarter(date(2026, 11, 11)) == "2026-Q4"

def test_is_overdue():
    now_utc = clock.get_app_now_utc("2026-11-11T15:00:00Z")
    today = date(2026, 11, 11)
    
    # Due yesterday and not done -> overdue
    assert clock.is_overdue(date(2026, 11, 10), done_at=None, now_utc=now_utc) is True
    
    # Due today and not done -> NOT overdue (boundary rule)
    assert clock.is_overdue(today, done_at=None, now_utc=now_utc) is False
    
    # Due tomorrow and not done -> NOT overdue
    assert clock.is_overdue(date(2026, 11, 12), done_at=None, now_utc=now_utc) is False
    
    # Due yesterday but marked done -> NOT overdue
    done_time = datetime(2026, 11, 10, 18, 0, 0, tzinfo=timezone.utc)
    assert clock.is_overdue(date(2026, 11, 10), done_at=done_time, now_utc=now_utc) is False
