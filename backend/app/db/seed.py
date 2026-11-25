import json
import logging
from pathlib import Path
from decimal import Decimal
from datetime import datetime, date
from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import (
    Company,
    Team,
    User,
    TeamMembership,
    Measurable,
    Score,
    Rock,
    Milestone,
    Issue,
    Todo,
    Meeting,
    MeetingAttendee,
    MeetingRating,
)

logger = logging.getLogger("track.seed")

def parse_iso_dt(val: Optional[str]) -> Optional[datetime]:
    if not val:
        return None
    if val.endswith("Z"):
        val = val[:-1] + "+00:00"
    return datetime.fromisoformat(val)

def parse_date(val: Optional[str]) -> Optional[date]:
    if not val:
        return None
    return date.fromisoformat(val)

def seed_database(db: Session, seed_file_path: Optional[Path] = None, reset: bool = False):
    """Idempotently seed the database from seed.json."""
    if seed_file_path is None:
        # Default path to task_resources/seed.json
        seed_file_path = Path(__file__).resolve().parent.parent.parent.parent / "task_resources" / "seed.json"

    if not seed_file_path.exists():
        raise FileNotFoundError(f"Seed file not found at: {seed_file_path}")

    with open(seed_file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if reset:
        logger.info("Resetting tables before seeding...")
        # Clean in reverse FK order
        db.query(MeetingRating).delete()
        db.query(MeetingAttendee).delete()
        db.query(Meeting).delete()
        db.query(Todo).delete()
        db.query(Issue).delete()
        db.query(Milestone).delete()
        db.query(Rock).delete()
        db.query(Score).delete()
        db.query(Measurable).delete()
        db.query(TeamMembership).delete()
        db.query(User).delete()
        db.query(Team).delete()
        db.query(Company).delete()
        db.flush()

    # 1. Company
    co_data = data["company"]
    company = db.query(Company).filter_by(id=co_data["id"]).first()
    if not company:
        company = Company(
            id=co_data["id"],
            name=co_data["name"],
            timezone=co_data.get("timezone", "America/Chicago"),
        )
        db.add(company)
    else:
        company.name = co_data["name"]
        company.timezone = co_data.get("timezone", "America/Chicago")
    db.flush()

    # 2. Teams
    for t in data["teams"]:
        team = db.query(Team).filter_by(id=t["id"]).first()
        if not team:
            team = Team(id=t["id"], company_id=company.id, name=t["name"])
            db.add(team)
        else:
            team.name = t["name"]
    db.flush()

    # 3. Users
    for u in data["users"]:
        user = db.query(User).filter_by(id=u["id"]).first()
        if not user:
            user = User(
                id=u["id"],
                company_id=company.id,
                name=u["name"],
                email=u["email"],
                role=u["role"],
            )
            db.add(user)
        else:
            user.name = u["name"]
            user.email = u["email"]
            user.role = u["role"]
    db.flush()

    # 4. Team Memberships
    for m in data["memberships"]:
        membership = db.query(TeamMembership).filter_by(user_id=m["user_id"], team_id=m["team_id"]).first()
        if not membership:
            membership = TeamMembership(user_id=m["user_id"], team_id=m["team_id"])
            db.add(membership)
    db.flush()

    # 5. Measurables
    for ms in data["measurables"]:
        goal = ms["goal"]
        goal_type = goal["type"]
        goal_val = Decimal(str(goal["value"])) if "value" in goal else None
        goal_min = Decimal(str(goal["min"])) if "min" in goal else None
        goal_max = Decimal(str(goal["max"])) if "max" in goal else None

        measurable = db.query(Measurable).filter_by(id=ms["id"]).first()
        if not measurable:
            measurable = Measurable(
                id=ms["id"],
                team_id=ms["team_id"],
                owner_id=ms["owner_id"],
                name=ms["name"],
                unit=ms["unit"],
                goal_type=goal_type,
                goal_value=goal_val,
                goal_min=goal_min,
                goal_max=goal_max,
            )
            db.add(measurable)
        else:
            measurable.team_id = ms["team_id"]
            measurable.owner_id = ms["owner_id"]
            measurable.name = ms["name"]
            measurable.unit = ms["unit"]
            measurable.goal_type = goal_type
            measurable.goal_value = goal_val
            measurable.goal_min = goal_min
            measurable.goal_max = goal_max
    db.flush()

    # 6. Scores
    for sc in data["scores"]:
        week_st = parse_date(sc["week_start"])
        score_val = Decimal(str(sc["value"]))
        score = db.query(Score).filter_by(measurable_id=sc["measurable_id"], week_start=week_st).first()
        if not score:
            score = Score(
                measurable_id=sc["measurable_id"],
                week_start=week_st,
                value=score_val,
            )
            db.add(score)
        else:
            score.value = score_val
    db.flush()

    # 7. Rocks
    for r in data["rocks"]:
        rock = db.query(Rock).filter_by(id=r["id"]).first()
        if not rock:
            rock = Rock(
                id=r["id"],
                team_id=r["team_id"],
                owner_id=r["owner_id"],
                title=r["title"],
                quarter=r["quarter"],
                status=r["status"],
            )
            db.add(rock)
        else:
            rock.team_id = r["team_id"]
            rock.owner_id = r["owner_id"]
            rock.title = r["title"]
            rock.quarter = r["quarter"]
            rock.status = r["status"]
    db.flush()

    # 8. Milestones
    for ml in data["milestones"]:
        milestone = db.query(Milestone).filter_by(id=ml["id"]).first()
        due_d = parse_date(ml["due_date"])
        if not milestone:
            milestone = Milestone(
                id=ml["id"],
                rock_id=ml["rock_id"],
                title=ml["title"],
                due_date=due_d,
                done=ml["done"],
            )
            db.add(milestone)
        else:
            milestone.rock_id = ml["rock_id"]
            milestone.title = ml["title"]
            milestone.due_date = due_d
            milestone.done = ml["done"]
    db.flush()

    # 9. Issues
    for iss in data["issues"]:
        src = iss.get("source")
        src_m_id = src.get("measurable_id") if src else None
        src_week = parse_date(src.get("week_start")) if src else None

        issue = db.query(Issue).filter_by(id=iss["id"]).first()
        if not issue:
            issue = Issue(
                id=iss["id"],
                team_id=iss["team_id"],
                owner_id=iss["owner_id"],
                title=iss["title"],
                priority=iss.get("priority"),
                source_measurable_id=src_m_id,
                source_week_start=src_week,
                created_at=parse_iso_dt(iss.get("created_at")),
                solved_at=parse_iso_dt(iss.get("solved_at")),
                resolution_note=iss.get("resolution_note"),
            )
            db.add(issue)
        else:
            issue.team_id = iss["team_id"]
            issue.owner_id = iss["owner_id"]
            issue.title = iss["title"]
            issue.priority = iss.get("priority")
            issue.source_measurable_id = src_m_id
            issue.source_week_start = src_week
            issue.created_at = parse_iso_dt(iss.get("created_at"))
            issue.solved_at = parse_iso_dt(iss.get("solved_at"))
            issue.resolution_note = iss.get("resolution_note")
    db.flush()

    # 10. To-Dos
    for td in data["todos"]:
        todo = db.query(Todo).filter_by(id=td["id"]).first()
        due_d = parse_date(td["due_date"])
        created_dt = parse_iso_dt(td.get("created_at"))
        done_dt = parse_iso_dt(td.get("done_at"))

        if not todo:
            todo = Todo(
                id=td["id"],
                team_id=td["team_id"],
                owner_id=td["owner_id"],
                source_issue_id=td.get("source_issue_id"),
                title=td["title"],
                due_date=due_d,
                done_at=done_dt,
                created_at=created_dt,
            )
            db.add(todo)
        else:
            todo.team_id = td["team_id"]
            todo.owner_id = td["owner_id"]
            todo.source_issue_id = td.get("source_issue_id")
            todo.title = td["title"]
            todo.due_date = due_d
            todo.done_at = done_dt
            todo.created_at = created_dt
    db.flush()

    # 11. Meetings
    for mt in data["meetings"]:
        meeting = db.query(Meeting).filter_by(id=mt["id"]).first()
        started_dt = parse_iso_dt(mt.get("started_at"))
        ended_dt = parse_iso_dt(mt.get("ended_at"))

        if not meeting:
            meeting = Meeting(
                id=mt["id"],
                team_id=mt["team_id"],
                facilitator_id=mt["facilitator_id"],
                started_at=started_dt,
                ended_at=ended_dt,
                current_section="ended" if ended_dt else "scorecard",
                section_started_at=ended_dt or started_dt,
            )
            db.add(meeting)
        else:
            meeting.team_id = mt["team_id"]
            meeting.facilitator_id = mt["facilitator_id"]
            meeting.started_at = started_dt
            meeting.ended_at = ended_dt
            meeting.current_section = "ended" if ended_dt else "scorecard"
        db.flush()

        # Attendees
        for att_id in mt.get("attendee_ids", []):
            att = db.query(MeetingAttendee).filter_by(meeting_id=mt["id"], user_id=att_id).first()
            if not att:
                att = MeetingAttendee(meeting_id=mt["id"], user_id=att_id, joined_at=started_dt)
                db.add(att)
        db.flush()

        # Ratings
        for rat in mt.get("ratings", []):
            m_rat = db.query(MeetingRating).filter_by(meeting_id=mt["id"], user_id=rat["user_id"]).first()
            if not m_rat:
                m_rat = MeetingRating(meeting_id=mt["id"], user_id=rat["user_id"], rating=rat["rating"])
                db.add(m_rat)
            else:
                m_rat.rating = rat["rating"]
        db.flush()

    db.commit()
    logger.info("Database seeding completed successfully!")

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    do_reset = "--reset" in sys.argv
    db_session = SessionLocal()
    try:
        seed_database(db_session, reset=do_reset)
    finally:
        db_session.close()
