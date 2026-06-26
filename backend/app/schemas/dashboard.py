from pydantic import BaseModel


class KpiSummary(BaseModel):
    total_revenue: float
    order_count: int
    average_order_value: float


class HeatmapCell(BaseModel):
    day_of_week: int
    hour: int
    revenue: float
