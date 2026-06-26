from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db
from app.db.models import User
from app.services.staffing import calculate_staffing

router = APIRouter(prefix="/branches", tags=["staffing"])


@router.get("/{branch_id}/staffing")
def get_staffing(
    branch_id: int,
    target_date: date,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    recs = calculate_staffing(db, branch_id, target_date)
    return [r.model_dump() for r in recs]
