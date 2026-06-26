from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import InventoryItem, SalesTransaction
from app.schemas.inventory import InventoryAlert


def analyze_inventory(
    db: Session,
    branch_id: int,
    lookback_days: int = 14,
    stockout_threshold_days: float = 3.0,
    overstock_threshold_days: float = 30.0,
) -> list[InventoryAlert]:
    items = db.query(InventoryItem).filter(InventoryItem.branch_id == branch_id).all()
    cutoff = datetime.utcnow() - timedelta(days=lookback_days)

    alerts: list[InventoryAlert] = []
    for item in items:
        total_qty = (
            db.query(func.sum(SalesTransaction.quantity))
            .filter(
                SalesTransaction.branch_id == branch_id,
                SalesTransaction.item == item.name,
                SalesTransaction.timestamp >= cutoff,
            )
            .scalar()
        ) or 0

        avg_daily_consumption = total_qty / lookback_days
        if avg_daily_consumption == 0:
            continue

        days_to_run_out = item.current_stock / avg_daily_consumption

        if days_to_run_out < stockout_threshold_days:
            target_stock = overstock_threshold_days * avg_daily_consumption
            suggested_qty = max(0.0, target_stock - item.current_stock)
            alerts.append(InventoryAlert(
                sku=item.sku,
                name=item.name,
                alert_type="stockout_risk",
                days_to_run_out=round(days_to_run_out, 1),
                current_stock=item.current_stock,
                suggested_reorder_qty=round(suggested_qty, 1),
            ))
        elif days_to_run_out > overstock_threshold_days:
            alerts.append(InventoryAlert(
                sku=item.sku,
                name=item.name,
                alert_type="overstock",
                days_to_run_out=round(days_to_run_out, 1),
                current_stock=item.current_stock,
                suggested_reorder_qty=0.0,
            ))

    return alerts
