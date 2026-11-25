from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, require_team_read
from app.db.session import get_db
from app.models import Team, User
from app.services.teams import list_accessible_teams, list_team_members
from app.services.scorecard import get_scorecard
from app.services.issues import list_issues
from app.services.todos import list_todos
from app.services.rocks import list_rocks
from app.core.response import ApiResponse

router = APIRouter()


@router.get("")
def get_teams(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return ApiResponse.success(list_accessible_teams(db, user))


@router.get("/{team_id}/members")
def members(team: Team = Depends(require_team_read), db: Session = Depends(get_db)):
    return ApiResponse.success(list_team_members(db, team))


@router.get("/{team_id}/scorecard")
def scorecard(team: Team = Depends(require_team_read), db: Session = Depends(get_db)):
    return ApiResponse.success(get_scorecard(db, team))


@router.get("/{team_id}/issues")
def issues(team: Team = Depends(require_team_read), db: Session = Depends(get_db)):
    return ApiResponse.success(list_issues(db, team))


@router.get("/{team_id}/todos")
def todos(team: Team = Depends(require_team_read), db: Session = Depends(get_db)):
    return ApiResponse.success(list_todos(db, team))


@router.get("/{team_id}/rocks")
def rocks(team: Team = Depends(require_team_read), db: Session = Depends(get_db)):
    return ApiResponse.success(list_rocks(db, team))
