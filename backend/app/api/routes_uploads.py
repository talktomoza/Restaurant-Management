import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db
from app.db.models import Branch, User
from app.schemas.upload import ColumnMapping
from app.services.csv_ingestion import parse_and_store_csv

router = APIRouter(prefix="/branches", tags=["uploads"])

MAX_FILE_BYTES = 10 * 1024 * 1024


@router.post("/{branch_id}/uploads", status_code=status.HTTP_201_CREATED)
async def upload_csv(
    branch_id: int,
    request: Request,
    file: UploadFile = File(...),
    mapping: str = Form(...),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    # Check Content-Length header before reading body
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_FILE_BYTES:
                raise HTTPException(status_code=413, detail="File exceeds 10MB limit")
        except ValueError:
            pass

    # Validate branch exists
    branch = db.get(Branch, branch_id)
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    raw = await file.read()
    if len(raw) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 10MB limit")
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=422, detail="Only .csv files are accepted")

    try:
        mapping_obj = ColumnMapping(**json.loads(mapping))
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Invalid mapping: {exc}")

    csv_text = raw.decode("utf-8", errors="replace")
    result = parse_and_store_csv(db, branch_id, file.filename, csv_text, mapping_obj)

    body = {
        "rows_imported": result.rows_imported,
        "rows_rejected": result.rows_rejected,
        "errors": result.errors,
    }
    if result.rows_imported == 0:
        raise HTTPException(status_code=422, detail=body)
    return body
