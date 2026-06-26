from datetime import datetime

from app.db.models import SalesTransaction


def test_kpis_endpoint(client, auth_headers, db_session):
    response = client.post(
        "/branches", json={"name": "Downtown", "location": "Main St"}, headers=auth_headers
    )
    branch_id = response.json()["id"]

    db_session.add_all([
        SalesTransaction(branch_id=branch_id, timestamp=datetime(2026, 3, 2, 12, 0), item="Burger", quantity=2, amount=20.0),
        SalesTransaction(branch_id=branch_id, timestamp=datetime(2026, 3, 2, 18, 0), item="Fries", quantity=1, amount=4.0),
    ])
    db_session.commit()

    response = client.get(
        f"/branches/{branch_id}/dashboard/kpis?start_date=2026-03-01&end_date=2026-03-03",
        headers=auth_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_revenue"] == 24.0
    assert body["order_count"] == 2
    assert body["average_order_value"] == 12.0


def test_heatmap_endpoint(client, auth_headers, db_session):
    response = client.post(
        "/branches", json={"name": "Downtown", "location": "Main St"}, headers=auth_headers
    )
    branch_id = response.json()["id"]

    db_session.add(SalesTransaction(
        branch_id=branch_id, timestamp=datetime(2026, 3, 2, 12, 0), item="Burger", quantity=2, amount=20.0
    ))
    db_session.commit()

    response = client.get(
        f"/branches/{branch_id}/dashboard/heatmap?start_date=2026-03-01&end_date=2026-03-03",
        headers=auth_headers,
    )
    assert response.status_code == 200
    cells = response.json()
    assert len(cells) == 1
    assert cells[0]["hour"] == 12
    assert cells[0]["revenue"] == 20.0
