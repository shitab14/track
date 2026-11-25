from datetime import date
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from app.core import clock
from app.domain.rules import compute_measurable_status
from app.models import Measurable, Score, Team


def get_scorecard(db: Session, team: Team):
    now = clock.get_app_now_utc()
    current_week = clock.get_current_week_start(now)
    last_closed = clock.get_last_closed_week_start(now)
    weeks = clock.get_13_weeks_range(last_closed)
    measurables = db.query(Measurable).options(joinedload(Measurable.owner), joinedload(Measurable.scores)).filter_by(team_id=team.id).order_by(Measurable.id).all()
    result = []
    for m in measurables:
        scores = {}
        current = None
        for s in m.scores:
            status = compute_measurable_status(m.goal_type, m.goal_value, m.goal_min, m.goal_max, s.value, s.week_start < current_week)
            item = {"id": s.id, "value": s.value, "status": status}
            if s.week_start == current_week:
                current = item
            elif s.week_start in weeks:
                scores[s.week_start.isoformat()] = item
        result.append({"id": m.id, "name": m.name, "unit": m.unit, "goal_type": m.goal_type, "goal_value": m.goal_value, "goal_min": m.goal_min, "goal_max": m.goal_max, "owner": {"id": m.owner.id, "name": m.owner.name}, "scores": scores, "current_week_score": current})
    return {"weeks": [d.isoformat() for d in weeks], "measurables": result}


def upsert_score(db: Session, team: Team, measurable_id: str, week_start: date, value):
    if week_start.weekday() != 0:
        raise HTTPException(422, "week_start must be a Monday")
    now = clock.get_app_now_utc()
    if week_start > clock.get_current_week_start(now):
        raise HTTPException(422, "Scores for future weeks are not allowed")
    measurable = db.query(Measurable).filter_by(id=measurable_id, team_id=team.id).first()
    if measurable is None:
        raise HTTPException(404, "Measurable not found")
    score = db.query(Score).filter_by(measurable_id=measurable_id, week_start=week_start).first()
    if score is None:
        score = Score(measurable_id=measurable_id, week_start=week_start, value=value)
        db.add(score)
    else:
        score.value = value
    db.commit()
    db.refresh(score)
    return {"id": score.id, "measurable_id": measurable.id, "week_start": score.week_start, "value": score.value, "status": compute_measurable_status(measurable.goal_type, measurable.goal_value, measurable.goal_min, measurable.goal_max, score.value, week_start < clock.get_current_week_start(now))}
