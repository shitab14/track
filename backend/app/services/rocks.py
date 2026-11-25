from sqlalchemy.orm import Session, joinedload
from app.core import clock
from app.domain.rules import compute_rock_status_and_progress
from app.models import Rock, Team


def list_rocks(db: Session, team: Team):
    now = clock.get_app_now_utc()
    rocks = db.query(Rock).options(joinedload(Rock.owner), joinedload(Rock.milestones)).filter_by(team_id=team.id).order_by(Rock.id).all()
    result = []
    for rock in rocks:
        status, percent = compute_rock_status_and_progress(rock, clock.get_today_company(now))
        done = sum(1 for m in rock.milestones if m.done)
        result.append({"id": rock.id, "title": rock.title, "quarter": rock.quarter, "owner": {"id": rock.owner.id, "name": rock.owner.name}, "computed_status": status, "progress": {"done": done, "total": len(rock.milestones), "percent": percent}, "milestones": [{"id": m.id, "title": m.title, "due_date": m.due_date, "done": m.done, "overdue": not m.done and m.due_date < clock.get_today_company(now)} for m in sorted(rock.milestones, key=lambda x: (x.due_date, x.id))]})
    return result
