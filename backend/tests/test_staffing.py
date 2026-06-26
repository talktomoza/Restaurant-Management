from datetime import date, datetime

from app.db.models import Branch, SalesTransaction
from app.services.staffing import calculate_staffing


def test_calculate_staffing_buckets_by_shift(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()

    target_date = date(2026, 3, 2)  # Monday
    for hour, count in [(8, 30), (14, 45), (20, 15)]:
        for _ in range(count):
            db_session.add(SalesTransaction(
                branch_id=branch.id,
                timestamp=datetime(2026, 3, 2, hour, 0),
                item="Burger",
                quantity=1,
                amount=10.0,
            ))
    db_session.commit()

    recs = calculate_staffing(db_session, branch.id, target_date, orders_per_staff=15.0)

    by_shift = {r.shift: r for r in recs}
    assert by_shift["morning"].recommended_staff_count == 2
    assert by_shift["afternoon"].recommended_staff_count == 3
    assert by_shift["evening"].recommended_staff_count == 1


def test_weekend_buffer_increases_staffing(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()

    saturday = date(2026, 3, 7)
    for _ in range(30):
        db_session.add(SalesTransaction(
            branch_id=branch.id,
            timestamp=datetime(2026, 3, 7, 14, 0),
            item="Burger",
            quantity=1,
            amount=10.0,
        ))
    db_session.commit()

    recs = calculate_staffing(db_session, branch.id, saturday, orders_per_staff=15.0)
    afternoon = next(r for r in recs if r.shift == "afternoon")
    assert afternoon.recommended_staff_count == 3


def test_efficiency_score_computed_when_actual_staff_given(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()

    target_date = date(2026, 3, 2)
    for _ in range(30):
        db_session.add(SalesTransaction(
            branch_id=branch.id,
            timestamp=datetime(2026, 3, 2, 14, 0),
            item="Burger",
            quantity=1,
            amount=10.0,
        ))
    db_session.commit()

    recs = calculate_staffing(
        db_session, branch.id, target_date, orders_per_staff=15.0,
        actual_staff={"afternoon": 4},
    )
    afternoon = next(r for r in recs if r.shift == "afternoon")
    assert afternoon.efficiency_score == 50.0
