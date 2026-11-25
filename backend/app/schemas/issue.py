from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class IssueCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    priority: Optional[int] = Field(default=None, ge=1, le=5)


class PriorityUpdate(BaseModel):
    priority: Optional[int] = Field(ge=1, le=5)


class IssueSolve(BaseModel):
    resolution_note: str = Field(min_length=1, max_length=10000)


class IssueTodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    owner_id: Optional[str] = None
    due_date: Optional[date] = None
