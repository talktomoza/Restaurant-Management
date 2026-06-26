from datetime import datetime, date

from app.db.models import Branch, User, SalesTransaction, InventoryItem


def test_create_branch_and_transaction(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()

    txn = SalesTransaction(
        branch_id=branch.id,
        timestamp=datetime(2026, 1, 1, 12, 0),
        item="Burger",
        quantity=2,
        amount=19.98,
    )
    db_session.add(txn)
    db_session.commit()

    assert branch.id is not None
    assert txn.branch_id == branch.id


def test_create_user_and_inventory_item(db_session):
    user = User(email="owner@example.com", hashed_password="hashed")
    branch = Branch(name="Uptown", location="2nd Ave")
    db_session.add_all([user, branch])
    db_session.commit()

    item = InventoryItem(
        branch_id=branch.id,
        sku="BUN-001",
        name="Burger Bun",
        current_stock=100,
        reorder_threshold=20,
        unit_cost=0.5,
    )
    db_session.add(item)
    db_session.commit()

    assert user.id is not None
    assert item.id is not None
