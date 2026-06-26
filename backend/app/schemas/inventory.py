from pydantic import BaseModel


class InventoryAlert(BaseModel):
    sku: str
    name: str
    alert_type: str
    days_to_run_out: float | None
    current_stock: float
    suggested_reorder_qty: float


class InventoryItemCreate(BaseModel):
    sku: str
    name: str
    current_stock: float
    reorder_threshold: float
    unit_cost: float


class InventoryItemOut(InventoryItemCreate):
    id: int

    model_config = {"from_attributes": True}
