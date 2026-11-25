from datetime import timedelta
from uuid import uuid4
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from app.core import clock
from app.domain.rules import compute_todo_completion_rate
from app.models import Issue, Meeting, Todo, Team, User


def serialize_todo(todo, now=None):
    return {"id": todo.id, "title": todo.title, "owner": {"id": todo.owner.id, "name": todo.owner.name}, "due_date": todo.due_date, "done": todo.done_at is not None, "overdue": clock.is_overdue(todo.due_date, todo.done_at, now), "source_issue_id": todo.source_issue_id, "created_at": todo.created_at, "done_at": todo.done_at}


def list_todos(db: Session, team: Team):
    now = clock.get_app_now_utc()
    todos = db.query(Todo).options(joinedload(Todo.owner)).filter_by(team_id=team.id).order_by(Todo.due_date, Todo.id).all()
    # Spec 2.5: the widget shows the LAST CLOSED week's completion rate.
    week_start = clock.get_last_closed_week_start(now)
    _, week_end = clock.get_week_range(week_start)
    due = [t for t in todos if week_start <= t.due_date <= week_start + timedelta(days=6)]
    completion = compute_todo_completion_rate(due, week_end)
    completion_rate = (completion["rate_percent"] / 100) if completion else None
    return {"completion_rate": completion_rate, "todos": [serialize_todo(t, now) for t in todos]}


def create_todo(db: Session, issue: Issue, current_user: User, title: str, owner_id, due_date):
    owner = db.query(User).filter_by(id=owner_id or current_user.id).first()
    if owner is None:
        raise HTTPException(404, "Todo owner not found")
    if not any(m.team_id == issue.team_id for m in owner.memberships) and owner.role != "admin":
        raise HTTPException(422, "Todo owner must belong to the issue's team")
    todo = Todo(id=f"td_{uuid4().hex}", team_id=issue.team_id, owner_id=owner.id, source_issue_id=issue.id, title=title.strip(), due_date=due_date or (clock.get_today_company() + timedelta(days=7)))
    # ADR0010: attribute creation to the team's active meeting, if any.
    active = db.query(Meeting).filter_by(team_id=issue.team_id, ended_at=None).first()
    if active:
        todo.created_in_meeting_id = active.id
    db.add(todo); db.commit(); db.refresh(todo)
    todo = db.query(Todo).options(joinedload(Todo.owner)).filter_by(id=todo.id).one()
    return serialize_todo(todo)


def set_done(db: Session, todo: Todo, done: bool):
    todo.done_at = clock.get_app_now_utc() if done else None
    db.commit(); db.refresh(todo)
    todo = db.query(Todo).options(joinedload(Todo.owner)).filter_by(id=todo.id).one()
    return serialize_todo(todo)


def get_todo(db: Session, todo_id: str):
    todo = db.query(Todo).filter_by(id=todo_id).first()
    if todo is None:
        raise HTTPException(404, "Todo not found")
    return todo
