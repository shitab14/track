from datetime import date
from uuid import uuid4
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.core import clock
from app.domain.rules import sort_issues
from app.models import Issue, Score, Team


def serialize_issue(issue):
    return {"id": issue.id, "title": issue.title, "priority": issue.priority, "owner": {"id": issue.owner.id, "name": issue.owner.name}, "source": ({"measurable_id": issue.source_measurable_id, "week_start": issue.source_week_start} if issue.source_measurable_id else None), "created_at": issue.created_at, "resolution_note": issue.resolution_note, "solved_at": issue.solved_at}


def list_issues(db: Session, team: Team):
    rows = db.query(Issue).options(joinedload(Issue.owner)).filter_by(team_id=team.id).all()
    unsolved = sort_issues([i for i in rows if i.solved_at is None])
    solved = sorted((i for i in rows if i.solved_at is not None), key=lambda i: i.solved_at, reverse=True)
    return {"unsolved": [serialize_issue(i) for i in unsolved], "solved": [serialize_issue(i) for i in solved]}


def get_issue_for_write(db: Session, issue_id: str):
    issue = db.query(Issue).options(joinedload(Issue.owner)).filter_by(id=issue_id).first()
    if issue is None:
        raise HTTPException(404, "Issue not found")
    return issue


def create_issue(db: Session, team: Team, user, title: str, priority):
    issue = Issue(id=f"i_{uuid4().hex}", team_id=team.id, owner_id=user.id, title=title.strip(), priority=priority)
    db.add(issue); db.commit(); db.refresh(issue)
    return serialize_issue(get_issue_for_write(db, issue.id))


def update_priority(db: Session, issue: Issue, priority):
    issue.priority = priority; db.commit(); db.refresh(issue)
    return serialize_issue(get_issue_for_write(db, issue.id))


def solve_issue(db: Session, issue: Issue, note: str):
    if issue.solved_at is not None:
        raise HTTPException(409, "Issue already solved")
    issue.solved_at = clock.get_app_now_utc(); issue.resolution_note = note.strip()
    db.commit(); db.refresh(issue)
    return serialize_issue(get_issue_for_write(db, issue.id))


def make_issue(db: Session, score_id: int, user):
    score = db.query(Score).options(joinedload(Score.measurable)).filter_by(id=score_id).first()
    if score is None:
        raise HTTPException(404, "Score not found")
    m = score.measurable
    existing = db.query(Issue).filter_by(source_measurable_id=m.id, source_week_start=score.week_start, solved_at=None).first()
    if existing:
        return serialize_issue(get_issue_for_write(db, existing.id)), False
    issue = Issue(id=f"i_{uuid4().hex}", team_id=m.team_id, owner_id=user.id, title=f"{m.name} was off track for week of {score.week_start.isoformat()}", source_measurable_id=m.id, source_week_start=score.week_start)
    db.add(issue)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(Issue).filter_by(source_measurable_id=m.id, source_week_start=score.week_start, solved_at=None).first()
        if existing is None:
            raise
        return serialize_issue(get_issue_for_write(db, existing.id)), False
    db.refresh(issue)
    return serialize_issue(get_issue_for_write(db, issue.id)), True
