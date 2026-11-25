from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ScoreUpsert(BaseModel):
    measurable_id: str
    week_start: date
    value: Decimal = Field(max_digits=12, decimal_places=2)


class ScoreOwner(BaseModel):
    id: str
    name: str


class ScorecardMeasurable(BaseModel):
    id: str
    name: str
    unit: str
    goal_type: str
    goal_value: Optional[Decimal]
    goal_min: Optional[Decimal]
    goal_max: Optional[Decimal]
    owner: ScoreOwner
    scores: dict[str, dict]
    current_week_score: Optional[dict]


class ScorecardOut(BaseModel):
    weeks: list[str]
    measurables: list[ScorecardMeasurable]


class ScoreOut(BaseModel):
    id: int
    measurable_id: str
    week_start: date
    value: Decimal
    status: str
