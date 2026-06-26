from datetime import date

from pydantic import BaseModel


class ShiftRecommendation(BaseModel):
    shift: str
    date: date
    recommended_staff_count: int
    efficiency_score: float | None = None
