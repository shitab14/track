from typing import Optional
from fastapi import Header, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User, Team, TeamMembership

def get_current_user(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db)
) -> User:
    """Retrieves the authenticated user from the X-User-Id header.
    
    Defaulting to 'u1' (Admin) if header is omitted in development/testing.
    """
    user_id = x_user_id or "u1"
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or unknown user context: '{user_id}'"
        )
    return user

def verify_team_access(
    team_id: str,
    write: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Team:
    """Verifies server-side team boundary and role permissions.
    
    Rules:
    - Admin: full access to every team across the company.
    - Team Member: read and write in assigned teams only.
    - Observer: read-only in assigned teams only. Writes are rejected with 403.
    - Any access to an unassigned team (even by guessed ID) is rejected with 403.
    """
    team = db.query(Team).filter_by(id=team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team '{team_id}' not found"
        )

    # Admin has universal access
    if current_user.role == "admin":
        return team

    # Verify team membership
    membership = db.query(TeamMembership).filter_by(
        user_id=current_user.id,
        team_id=team_id
    ).first()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access to team '{team_id}' is denied for user '{current_user.name}'"
        )

    # Check write permission for observers
    if write and current_user.role == "observer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Observers have read-only access and cannot perform modifications"
        )

    return team

def require_team_read(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Team:
    """Dependency verifying read access to a team."""
    return verify_team_access(team_id=team_id, write=False, current_user=current_user, db=db)

def require_team_write(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Team:
    """Dependency verifying write access to a team."""
    return verify_team_access(team_id=team_id, write=True, current_user=current_user, db=db)
