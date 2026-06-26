from app.db.models import Branch, SalesTransaction, CsvUpload
from app.schemas.upload import ColumnMapping
from app.services.csv_ingestion import parse_and_store_csv

MAPPING = ColumnMapping(
    date_column="Date", item_column="Item", quantity_column="Qty", amount_column="Total"
)


def test_parse_valid_csv_stores_transactions(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()

    csv_text = (
        "Date,Item,Qty,Total\n"
        "2026-01-01 12:00,Burger,2,19.98\n"
        "2026-01-01 12:05,Fries,1,3.99\n"
    )

    result = parse_and_store_csv(db_session, branch.id, "sales.csv", csv_text, MAPPING)

    assert result.rows_imported == 2
    assert result.rows_rejected == 0
    transactions = db_session.query(SalesTransaction).all()
    assert len(transactions) == 2
    upload = db_session.query(CsvUpload).one()
    assert upload.status == "completed"
    assert upload.filename == "sales.csv"


def test_parse_csv_rejects_bad_rows_but_keeps_good_ones(db_session):
    branch = Branch(name="Uptown", location="2nd Ave")
    db_session.add(branch)
    db_session.commit()

    csv_text = (
        "Date,Item,Qty,Total\n"
        "2026-01-01 12:00,Burger,2,19.98\n"
        "not-a-date,Fries,1,3.99\n"
        "2026-01-01 12:10,Soda,abc,2.50\n"
    )

    result = parse_and_store_csv(db_session, branch.id, "sales.csv", csv_text, MAPPING)

    assert result.rows_imported == 1
    assert result.rows_rejected == 2
    assert len(result.errors) == 2


def test_parse_csv_missing_required_column_fails_fast(db_session):
    branch = Branch(name="Midtown", location="3rd Ave")
    db_session.add(branch)
    db_session.commit()

    csv_text = "Date,Item,Qty\n2026-01-01,Burger,2\n"

    result = parse_and_store_csv(db_session, branch.id, "sales.csv", csv_text, MAPPING)

    assert result.rows_imported == 0
    assert result.rows_rejected == 0
    assert any("Total" in e for e in result.errors)
    upload = db_session.query(CsvUpload).one()
    assert upload.status == "failed"
