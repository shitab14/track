from sqlalchemy.orm import Session
from app.models import Team, TeamMembership, User


def list_team_members(db: Session, team: Team):
    """Eligible To-Do owners for a team: the team's Team Members plus every
    company Admin (spec 2.5 — owners are the team's Admins and Team Members).
    Observers are excluded; this mirrors who the server allows to write."""
    team_members = (
        db.query(User)
        .join(TeamMembership, TeamMembership.user_id == User.id)
        .filter(TeamMembership.team_id == team.id, User.role == "team_member")
        .all()
    )
    admins = db.query(User).filter(User.role == "admin").all()
    by_id = {u.id: u for u in list(admins) + list(team_members)}
    ordered = sorted(by_id.values(), key=lambda u: u.id)
    return [{"id": u.id, "name": u.name, "role": u.role} for u in ordered]


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
