from datetime import datetime, timedelta

import pytest

from app.db.models import Branch, SalesTransaction
from app.services.forecasting import generate_forecast, evaluate_forecast_accuracy


def _seed_transactions(db_session, branch_id, num_days, base_amount=100.0):
    start = datetime.utcnow() - timedelta(days=num_days)
    for i in range(num_days):
        day = start + timedelta(days=i)
        amount = base_amount + (20.0 if day.weekday() >= 5 else 0.0)
        db_session.add(SalesTransaction(
            branch_id=branch_id,
            timestamp=day,
            item="Burger",
            quantity=1,
            amount=amount,
        ))
    db_session.commit()


def test_generate_forecast_requires_minimum_history(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    _seed_transactions(db_session, branch.id, num_days=5)

    with pytest.raises(ValueError):
        generate_forecast(db_session, branch.id, horizon_days=7)


def test_generate_forecast_returns_points_with_bounds(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    _seed_transactions(db_session, branch.id, num_days=60)

    points = generate_forecast(db_session, branch.id, horizon_days=7)

    assert len(points) == 7
    for point in points:
        assert point.lower_bound <= point.predicted_revenue <= point.upper_bound


def test_evaluate_forecast_accuracy_returns_none_with_insufficient_history(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    _seed_transactions(db_session, branch.id, num_days=10)

    result = evaluate_forecast_accuracy(db_session, branch.id)

    assert result["mae_pct"] is None
    assert result["rmse_pct"] is None


def test_evaluate_forecast_accuracy_returns_percentages(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    _seed_transactions(db_session, branch.id, num_days=60)

    result = evaluate_forecast_accuracy(db_session, branch.id)

    assert result["mae_pct"] is not None
    assert result["mae_pct"] >= 0
    assert result["rmse_pct"] >= 0
