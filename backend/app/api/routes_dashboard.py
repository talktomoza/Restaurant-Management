from collections import defaultdict
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db
from app.db.models import SalesTransaction, User
from app.schemas.dashboard import KpiSummary, HeatmapCell

router = APIRouter(prefix="/branches", tags=["dashboard"])


def _transactions_in_range(db: Session, branch_id: int, start_date: date, end_date: date):
    start_dt = datetime(start_date.year, start_date.month, start_date.day)
    end_dt = datetime(end_date.year, end_date.month, end_date.day) + timedelta(days=1)
    return (
        db.query(SalesTransaction)
        .filter(
            SalesTransaction.branch_id == branch_id,
            SalesTransaction.timestamp >= start_dt,
            SalesTransaction.timestamp < end_dt,
        )
        .all()
    )


@router.get("/{branch_id}/dashboard/kpis", response_model=KpiSummary)
def get_kpis(
    branch_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    transactions = _transactions_in_range(db, branch_id, start_date, end_date)
    total_revenue = sum(t.amount for t in transactions)
    order_count = len(transactions)
    average_order_value = round(total_revenue / order_count, 2) if order_count else 0.0
    return KpiSummary(
        total_revenue=round(total_revenue, 2),
        order_count=order_count,
        average_order_value=average_order_value,
    )


@router.get("/{branch_id}/dashboard/heatmap", response_model=list[HeatmapCell])
def get_heatmap(
    branch_id: int,
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    transactions = _transactions_in_range(db, branch_id, start_date, end_date)
    buckets: dict[tuple[int, int], float] = defaultdict(float)
    for t in transactions:
        key = (t.timestamp.weekday(), t.timestamp.hour)
        buckets[key] += t.amount

    return [
        HeatmapCell(day_of_week=dow, hour=hour, revenue=round(revenue, 2))
        for (dow, hour), revenue in sorted(buckets.items())
    ]
