from datetime import datetime


def test_staffing_endpoint_returns_recommendations(client, auth_headers, db_session):
    response = client.post(
        "/branches", json={"name": "Downtown", "location": "Main St"}, headers=auth_headers
    )
    branch_id = response.json()["id"]

    from app.db.models import SalesTransaction
    for _ in range(30):
        db_session.add(SalesTransaction(
            branch_id=branch_id,
            timestamp=datetime(2026, 3, 2, 14, 0),
            item="Burger",
            quantity=1,
            amount=10.0,
        ))
    db_session.commit()

    response = client.get(
        f"/branches/{branch_id}/staffing?target_date=2026-03-02", headers=auth_headers
    )
    assert response.status_code == 200
    recs = response.json()
    assert len(recs) == 3
    shifts = {r["shift"] for r in recs}
    assert shifts == {"morning", "afternoon", "evening"}
