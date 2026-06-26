import csv
import io
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import SalesTransaction, CsvUpload
from app.schemas.upload import ColumnMapping

MAX_ROWS = 50_000


@dataclass
class ParseResult:
    rows_imported: int = 0
    rows_rejected: int = 0
    errors: list[str] = field(default_factory=list)


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.strip())


def parse_and_store_csv(
    db: Session,
    branch_id: int,
    filename: str,
    csv_text: str,
    mapping: ColumnMapping,
) -> ParseResult:
    result = ParseResult()
    reader = csv.DictReader(io.StringIO(csv_text))

    required = [
        mapping.date_column,
        mapping.item_column,
        mapping.quantity_column,
        mapping.amount_column,
    ]
    fieldnames = reader.fieldnames or []
    missing = [col for col in required if col not in fieldnames]
    if missing:
        result.errors.append(f"Missing required column(s): {', '.join(missing)}")
        db.add(CsvUpload(
            branch_id=branch_id,
            filename=filename,
            column_mapping=mapping.model_dump(),
            status="failed",
        ))
        db.commit()
        return result

    for row_number, row in enumerate(reader, start=2):
        if row_number - 1 > MAX_ROWS:
            result.errors.append(f"Row {row_number}: exceeded max row limit of {MAX_ROWS}")
            break
        try:
            timestamp = _parse_timestamp(row[mapping.date_column])
            quantity = int(row[mapping.quantity_column])
            amount = float(row[mapping.amount_column])
            item = row[mapping.item_column].strip()
        except (ValueError, KeyError) as exc:
            result.rows_rejected += 1
            result.errors.append(f"Row {row_number}: {exc}")
            continue

        db.add(SalesTransaction(
            branch_id=branch_id,
            timestamp=timestamp,
            item=item,
            quantity=quantity,
            amount=amount,
        ))
        result.rows_imported += 1

    status = "completed" if result.rows_imported > 0 else "failed"
    db.add(CsvUpload(
        branch_id=branch_id,
        filename=filename,
        column_mapping=mapping.model_dump(),
        status=status,
    ))
    db.commit()
    return result
