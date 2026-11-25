from pydantic import BaseModel


class RockOut(BaseModel):
    id: str
    title: str
    quarter: str
    owner: dict
    computed_status: str
    progress: dict
    milestones: list[dict]
