from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db
from app.db.models import Branch, User
from app.schemas.branch import BranchCreate, BranchOut

router = APIRouter(prefix="/branches", tags=["branches"])


@router.post("", response_model=BranchOut, status_code=status.HTTP_201_CREATED)
def create_branch(
    payload: BranchCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    branch = Branch(name=payload.name, location=payload.location)
    db.add(branch)
    db.commit()
    return branch


@router.get("", response_model=list[BranchOut])
def list_branches(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return db.query(Branch).all()
