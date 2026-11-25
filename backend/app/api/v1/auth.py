from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.response import ApiResponse
from app.api.deps import get_current_user, require_team_read, require_team_write
from app.db.session import get_db
from app.models import User, Team

router = APIRouter()

@router.get("/users", response_model=ApiResponse[list])
def list_seeded_users(db: Session = Depends(get_db)):
    """Lists the seeded users for the header user switcher (login stand-in)."""
    users = db.query(User).order_by(User.id).all()
    return ApiResponse.success(
        [{"id": u.id, "name": u.name, "role": u.role} for u in users],
        "Seeded users",
    )

@router.get("/me", response_model=ApiResponse[dict])
def get_current_user_profile(user: User = Depends(get_current_user)):
    """Returns the authenticated user's profile and role."""
    return ApiResponse.success(
        data={
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        },
        message="User profile fetched"
    )

@router.get("/teams/{team_id}/verify-read", response_model=ApiResponse[dict])
def verify_read(team: Team = Depends(require_team_read), user: User = Depends(get_current_user)):
    """Verifies read access for the current user to a team."""
    return ApiResponse.success(
        data={"team_id": team.id, "team_name": team.name, "user": user.name},
        message="Read access authorized"
    )

@router.post("/teams/{team_id}/verify-write", response_model=ApiResponse[dict])
def verify_write(team: Team = Depends(require_team_write), user: User = Depends(get_current_user)):
    """Verifies write access for the current user to a team."""
    return ApiResponse.success(
        data={"team_id": team.id, "team_name": team.name, "user": user.name},
        message="Write access authorized"
    )
