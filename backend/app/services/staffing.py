import math
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models import SalesTransaction, StaffingRecommendation, Forecast
from app.schemas.staffing import ShiftRecommendation

SHIFT_HOURS = {
    "morning": range(6, 12),
    "afternoon": range(12, 18),
    "evening": range(18, 23),
}
ASSUMED_AVG_ORDER_VALUE = 12.0
WEEKEND_BUFFER_MULTIPLIER = 1.3


def _order_counts_by_shift(db: Session, branch_id: int, target_date: date) -> dict[str, float]:
    day_start = datetime(target_date.year, target_date.month, target_date.day)
    day_end = day_start + timedelta(days=1)

    transactions = (
        db.query(SalesTransaction)
        .filter(
            SalesTransaction.branch_id == branch_id,
            SalesTransaction.timestamp >= day_start,
            SalesTransaction.timestamp < day_end,
        )
        .all()
    )

    counts: dict[str, float] = {shift: 0 for shift in SHIFT_HOURS}
    if transactions:
        for txn in transactions:
            for shift, hours in SHIFT_HOURS.items():
                if txn.timestamp.hour in hours:
                    counts[shift] += 1
                    break
        return counts

    forecast = (
        db.query(Forecast)
        .filter(Forecast.branch_id == branch_id, Forecast.date == target_date)
        .first()
    )
    if forecast:
        total_orders = forecast.predicted_revenue / ASSUMED_AVG_ORDER_VALUE
        per_shift = total_orders / len(SHIFT_HOURS)
        return {shift: per_shift for shift in SHIFT_HOURS}

    return counts


def calculate_staffing(
    db: Session,
    branch_id: int,
    target_date: date,
    orders_per_staff: float = 15.0,
    actual_staff: dict[str, int] | None = None,
) -> list[ShiftRecommendation]:
    actual_staff = actual_staff or {}
    counts = _order_counts_by_shift(db, branch_id, target_date)
    is_weekend = target_date.weekday() >= 5

    db.query(StaffingRecommendation).filter(
        StaffingRecommendation.branch_id == branch_id,
        StaffingRecommendation.date == target_date,
    ).delete()

    recommendations = []
    for shift, order_count in counts.items():
        raw_count = order_count / orders_per_staff
        if is_weekend:
            raw_count *= WEEKEND_BUFFER_MULTIPLIER
        recommended = max(1, math.ceil(raw_count))

        efficiency_score = None
        if shift in actual_staff and actual_staff[shift] > 0:
            efficiency_score = round(min(200.0, recommended / actual_staff[shift] * 100), 1)

        rec = ShiftRecommendation(
            shift=shift,
            date=target_date,
            recommended_staff_count=recommended,
            efficiency_score=efficiency_score,
        )
        recommendations.append(rec)
        db.add(StaffingRecommendation(
            branch_id=branch_id,
            shift=rec.shift,
            date=rec.date,
            recommended_staff_count=rec.recommended_staff_count,
            efficiency_score=rec.efficiency_score,
        ))

    db.commit()
    return recommendations
