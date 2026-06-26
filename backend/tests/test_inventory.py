from datetime import datetime, timedelta

from app.db.models import Branch, InventoryItem, SalesTransaction
from app.services.inventory import analyze_inventory


def _seed_sales(db_session, branch_id, item_name, daily_qty, num_days):
    now = datetime.utcnow()
    for i in range(num_days):
        db_session.add(SalesTransaction(
            branch_id=branch_id,
            timestamp=now - timedelta(days=i),
            item=item_name,
            quantity=daily_qty,
            amount=daily_qty * 5.0,
        ))
    db_session.commit()


def test_low_stock_item_triggers_stockout_alert(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    _seed_sales(db_session, branch.id, "Burger", daily_qty=10, num_days=14)
    db_session.add(InventoryItem(
        branch_id=branch.id, sku="BUR-001", name="Burger",
        current_stock=15, reorder_threshold=20, unit_cost=2.0,
    ))
    db_session.commit()

    alerts = analyze_inventory(db_session, branch.id)

    assert len(alerts) == 1
    assert alerts[0].alert_type == "stockout_risk"
    assert alerts[0].sku == "BUR-001"
    assert alerts[0].suggested_reorder_qty > 0


def test_overstocked_item_triggers_overstock_alert(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    _seed_sales(db_session, branch.id, "Fries", daily_qty=2, num_days=14)
    db_session.add(InventoryItem(
        branch_id=branch.id, sku="FRI-001", name="Fries",
        current_stock=500, reorder_threshold=20, unit_cost=1.0,
    ))
    db_session.commit()

    alerts = analyze_inventory(db_session, branch.id)

    assert len(alerts) == 1
    assert alerts[0].alert_type == "overstock"
    assert alerts[0].suggested_reorder_qty == 0


def test_healthy_stock_item_triggers_no_alert(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    _seed_sales(db_session, branch.id, "Soda", daily_qty=10, num_days=14)
    db_session.add(InventoryItem(
        branch_id=branch.id, sku="SOD-001", name="Soda",
        current_stock=100, reorder_threshold=20, unit_cost=0.5,
    ))
    db_session.commit()

    alerts = analyze_inventory(db_session, branch.id)

    assert alerts == []


def test_item_with_no_sales_history_produces_no_alert(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    db_session.add(InventoryItem(
        branch_id=branch.id, sku="NEW-001", name="New Item",
        current_stock=50, reorder_threshold=10, unit_cost=1.0,
    ))
    db_session.commit()

    alerts = analyze_inventory(db_session, branch.id)

    assert alerts == []
