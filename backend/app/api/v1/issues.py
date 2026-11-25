from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, require_team_write
from app.core.response import ApiResponse
from app.db.session import get_db
from app.models import Team, User
from app.schemas.issue import IssueCreate, IssueSolve, PriorityUpdate
from app.services.issues import create_issue, get_issue_for_write, solve_issue, update_priority
from app.services.meetings import publish_data_changed

router = APIRouter()


@router.post("/teams/{team_id}/issues")
def add_issue(body: IssueCreate, team: Team = Depends(require_team_write), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = create_issue(db, team, user, body.title, body.priority)
    publish_data_changed(db, team.id, "issues")
    return ApiResponse.success(data, "Issue created", 201)


@router.patch("/issues/{issue_id}/priority")
def set_priority(issue_id: str, body: PriorityUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    issue = get_issue_for_write(db, issue_id)
    require_team_write(team_id=issue.team_id, current_user=user, db=db)
    data = update_priority(db, issue, body.priority)
    publish_data_changed(db, issue.team_id, "issues")
    return ApiResponse.success(data, "Priority updated")


@router.post("/issues/{issue_id}/solve")
def solve(issue_id: str, body: IssueSolve, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    issue = get_issue_for_write(db, issue_id)
    require_team_write(team_id=issue.team_id, current_user=user, db=db)
    data = solve_issue(db, issue, body.resolution_note)
    publish_data_changed(db, issue.team_id, "issues")
    return ApiResponse.success(data, "Issue solved")
