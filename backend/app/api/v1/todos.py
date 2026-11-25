from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, require_team_write
from app.core.response import ApiResponse
from app.db.session import get_db
from app.models import User
from app.schemas.issue import IssueTodoCreate
from app.services.issues import get_issue_for_write
from app.services.todos import create_todo, get_todo, set_done

router = APIRouter()


@router.post("/issues/{issue_id}/todos")
def add_todo(issue_id: str, body: IssueTodoCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    issue = get_issue_for_write(db, issue_id)
    require_team_write(team_id=issue.team_id, current_user=user, db=db)
    return ApiResponse.success(create_todo(db, issue, user, body.title, body.owner_id, body.due_date), "Todo created", 201)


@router.post("/todos/{todo_id}/done")
def mark_done(todo_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    todo = get_todo(db, todo_id)
    require_team_write(team_id=todo.team_id, current_user=user, db=db)
    return ApiResponse.success(set_done(db, todo, True), "Todo marked done")


@router.post("/todos/{todo_id}/undo")
def undo_done(todo_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    todo = get_todo(db, todo_id)
    require_team_write(team_id=todo.team_id, current_user=user, db=db)
    return ApiResponse.success(set_done(db, todo, False), "Todo marked incomplete")
