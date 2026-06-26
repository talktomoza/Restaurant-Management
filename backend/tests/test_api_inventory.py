from datetime import datetime, timedelta

from app.db.models import SalesTransaction


def _create_branch(client, auth_headers):
    response = client.post(
        "/branches", json={"name": "Downtown", "location": "Main St"}, headers=auth_headers
    )
    return response.json()["id"]


def test_create_and_list_inventory_items(client, auth_headers):
    branch_id = _create_branch(client, auth_headers)

    response = client.post(
        f"/branches/{branch_id}/inventory-items",
        json={"sku": "BUR-001", "name": "Burger", "current_stock": 50, "reorder_threshold": 10, "unit_cost": 2.0},
        headers=auth_headers,
    )
    assert response.status_code == 201

    response = client.get(f"/branches/{branch_id}/inventory-items", headers=auth_headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["sku"] == "BUR-001"


def test_inventory_alerts_endpoint(client, auth_headers, db_session):
    branch_id = _create_branch(client, auth_headers)

    now = datetime.utcnow()
    for i in range(14):
        db_session.add(SalesTransaction(
            branch_id=branch_id,
            timestamp=now - timedelta(days=i),
            item="Burger",
            quantity=10,
            amount=50.0,
        ))
    db_session.commit()

    client.post(
        f"/branches/{branch_id}/inventory-items",
        json={"sku": "BUR-001", "name": "Burger", "current_stock": 15, "reorder_threshold": 10, "unit_cost": 2.0},
        headers=auth_headers,
    )

    response = client.get(f"/branches/{branch_id}/inventory-alerts", headers=auth_headers)
    assert response.status_code == 200
    alerts = response.json()
    assert len(alerts) == 1
    assert alerts[0]["alert_type"] == "stockout_risk"
