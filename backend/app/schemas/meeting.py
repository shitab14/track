from pydantic import BaseModel, Field


class RatingInput(BaseModel):
    rating: int = Field(ge=1, le=10)
