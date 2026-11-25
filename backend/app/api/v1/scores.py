from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, require_team_read, require_team_write
from app.core.response import ApiResponse
from app.db.session import get_db
from app.models import Team, User
from app.schemas.scorecard import ScoreUpsert
from app.services.scorecard import upsert_score
from app.services.issues import make_issue
from app.services.meetings import publish_data_changed

router = APIRouter()


@router.post("/teams/{team_id}/scores")
def save_score(body: ScoreUpsert, team: Team = Depends(require_team_write), db: Session = Depends(get_db)):
    data = upsert_score(db, team, body.measurable_id, body.week_start, body.value)
    publish_data_changed(db, team.id, "scorecard")
    return ApiResponse.success(data, "Score saved")


@router.post("/scores/{score_id}/make-issue")
def promote_score(score_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from fastapi import HTTPException
    from app.models import Score
    score = db.query(Score).filter_by(id=score_id).first()
    if score is None:
        raise HTTPException(404, "Score not found")
    require_team_read(team_id=score.measurable.team_id, current_user=user, db=db)
    require_team_write(team_id=score.measurable.team_id, current_user=user, db=db)
    issue, created = make_issue(db, score_id, user)
    publish_data_changed(db, score.measurable.team_id, "issues")
    return ApiResponse.success(issue, "Issue created" if created else "Issue already exists")
