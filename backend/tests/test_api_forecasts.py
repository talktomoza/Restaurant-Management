from datetime import datetime, timedelta

from app.db.models import Branch, SalesTransaction


def _seed_branch_with_history(db_session, num_days=60):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    start = datetime.utcnow() - timedelta(days=num_days)
    for i in range(num_days):
        db_session.add(SalesTransaction(
            branch_id=branch.id,
            timestamp=start + timedelta(days=i),
            item="Burger",
            quantity=1,
            amount=100.0,
        ))
    db_session.commit()
    return branch.id


def test_generate_forecast_endpoint(client, auth_headers, db_session):
    branch_id = _seed_branch_with_history(db_session)

    response = client.post(
        f"/branches/{branch_id}/forecasts?horizon_days=7", headers=auth_headers
    )
    assert response.status_code == 200
    points = response.json()
    assert len(points) == 7


def test_forecast_endpoint_insufficient_history_returns_422(client, auth_headers, db_session):
    branch_id = _seed_branch_with_history(db_session, num_days=5)

    response = client.post(
        f"/branches/{branch_id}/forecasts?horizon_days=7", headers=auth_headers
    )
    assert response.status_code == 422
