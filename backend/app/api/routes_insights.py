from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db
from app.db.models import User
from app.services.insight_service import generate_weekly_insight
from app.services.openrouter_client import call_openrouter_chat

router = APIRouter(prefix="/branches", tags=["insights"])


@router.post("/{branch_id}/insights/weekly-summary")
def weekly_summary(
    branch_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    content = generate_weekly_insight(db, branch_id, llm_call=call_openrouter_chat)
    return content.model_dump()
