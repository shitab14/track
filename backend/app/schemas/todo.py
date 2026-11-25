from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class TodoOut(BaseModel):
    id: str
    title: str
    owner: dict
    due_date: date
    done: bool
    overdue: bool
    source_issue_id: Optional[str]
    created_at: datetime
