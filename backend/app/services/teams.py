from sqlalchemy.orm import Session
from app.models import Team, TeamMembership, User


def list_accessible_teams(db: Session, user: User):
    if user.role == "admin":
        rows = db.query(Team).order_by(Team.id).all()
        return [{"id": t.id, "name": t.name, "user_role": user.role} for t in rows]
    rows = (
        db.query(Team, TeamMembership)
        .join(TeamMembership, TeamMembership.team_id == Team.id)
        .filter(TeamMembership.user_id == user.id)
        .order_by(Team.id)
        .all()
    )
    return [{"id": t.id, "name": t.name, "user_role": user.role} for t, _ in rows]
