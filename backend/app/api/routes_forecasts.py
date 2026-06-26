from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db
from app.db.models import User
from app.services.forecasting import generate_forecast, evaluate_forecast_accuracy

router = APIRouter(prefix="/branches", tags=["forecasts"])


@router.post("/{branch_id}/forecasts")
def create_forecast(
    branch_id: int,
    horizon_days: int = 7,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    try:
        points = generate_forecast(db, branch_id, horizon_days)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return [p.model_dump() for p in points]


@router.get("/{branch_id}/forecasts/accuracy")
def forecast_accuracy(
    branch_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return evaluate_forecast_accuracy(db, branch_id)
