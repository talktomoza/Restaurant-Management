from datetime import date

from pydantic import BaseModel


class ForecastPoint(BaseModel):
    date: date
    predicted_revenue: float
    lower_bound: float
    upper_bound: float
