from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db
from app.db.models import InventoryItem, User
from app.schemas.inventory import InventoryItemCreate, InventoryItemOut
from app.services.inventory import analyze_inventory

router = APIRouter(prefix="/branches", tags=["inventory"])


@router.post(
    "/{branch_id}/inventory-items", response_model=InventoryItemOut, status_code=status.HTTP_201_CREATED
)
def create_inventory_item(
    branch_id: int,
    payload: InventoryItemCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    item = InventoryItem(branch_id=branch_id, **payload.model_dump())
    db.add(item)
    db.commit()
    return item


@router.get("/{branch_id}/inventory-items", response_model=list[InventoryItemOut])
def list_inventory_items(
    branch_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    return db.query(InventoryItem).filter(InventoryItem.branch_id == branch_id).all()


@router.get("/{branch_id}/inventory-alerts")
def inventory_alerts(
    branch_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    alerts = analyze_inventory(db, branch_id)
    return [a.model_dump() for a in alerts]
