# AI-Powered Restaurant Analytics Dashboard Implementation Plan — Part 3 (Tasks 11-13)

> Continuation of Parts 1-2. Same Global Constraints apply.

---

## Task 11: Inventory intelligence service

**Files:**
- Create: `backend/app/services/inventory.py`
- Create: `backend/app/schemas/inventory.py`
- Test: `backend/tests/test_inventory.py`

**Interfaces:**
- Consumes: `app.db.models.InventoryItem`, `app.db.models.SalesTransaction`, a SQLAlchemy `Session`.
- Produces: `app.schemas.inventory.InventoryAlert(sku: str, name: str, alert_type: str, days_to_run_out: float | None, current_stock: float, suggested_reorder_qty: float)`. `alert_type` is one of `"stockout_risk"`, `"overstock"`.
- Produces: `analyze_inventory(db: Session, branch_id: int, lookback_days: int = 14, stockout_threshold_days: float = 3.0, overstock_threshold_days: float = 30.0) -> list[InventoryAlert]`.
  - For each `InventoryItem` of the branch, computes `avg_daily_consumption` from matching `SalesTransaction.quantity` (matched by `SalesTransaction.item == InventoryItem.name`) over `lookback_days`.
  - If `avg_daily_consumption == 0`: skip stockout/overstock check for that item (no sales signal), include it with `alert_type=None` results filtered out (i.e., item produces no alert).
  - `days_to_run_out = current_stock / avg_daily_consumption`.
  - If `days_to_run_out < stockout_threshold_days`: emit `"stockout_risk"` alert with `suggested_reorder_qty = (overstock_threshold_days * avg_daily_consumption) - current_stock` (clamped to >= 0).
  - Elif `days_to_run_out > overstock_threshold_days`: emit `"overstock"` alert with `suggested_reorder_qty = 0`.
  - Else: no alert for that item.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_inventory.py
from datetime import datetime, timedelta

from app.db.models import Branch, InventoryItem, SalesTransaction
from app.services.inventory import analyze_inventory


def _seed_sales(db_session, branch_id, item_name, daily_qty, num_days):
    now = datetime.utcnow()
    for i in range(num_days):
        db_session.add(SalesTransaction(
            branch_id=branch_id,
            timestamp=now - timedelta(days=i),
            item=item_name,
            quantity=daily_qty,
            amount=daily_qty * 5.0,
        ))
    db_session.commit()


def test_low_stock_item_triggers_stockout_alert(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    _seed_sales(db_session, branch.id, "Burger", daily_qty=10, num_days=14)
    db_session.add(InventoryItem(
        branch_id=branch.id, sku="BUR-001", name="Burger",
        current_stock=15, reorder_threshold=20, unit_cost=2.0,
    ))
    db_session.commit()

    alerts = analyze_inventory(db_session, branch.id)

    assert len(alerts) == 1
    assert alerts[0].alert_type == "stockout_risk"
    assert alerts[0].sku == "BUR-001"
    assert alerts[0].suggested_reorder_qty > 0


def test_overstocked_item_triggers_overstock_alert(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    _seed_sales(db_session, branch.id, "Fries", daily_qty=2, num_days=14)
    db_session.add(InventoryItem(
        branch_id=branch.id, sku="FRI-001", name="Fries",
        current_stock=500, reorder_threshold=20, unit_cost=1.0,
    ))
    db_session.commit()

    alerts = analyze_inventory(db_session, branch.id)

    assert len(alerts) == 1
    assert alerts[0].alert_type == "overstock"
    assert alerts[0].suggested_reorder_qty == 0


def test_healthy_stock_item_triggers_no_alert(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    _seed_sales(db_session, branch.id, "Soda", daily_qty=10, num_days=14)
    db_session.add(InventoryItem(
        branch_id=branch.id, sku="SOD-001", name="Soda",
        current_stock=100, reorder_threshold=20, unit_cost=0.5,
    ))
    db_session.commit()

    alerts = analyze_inventory(db_session, branch.id)

    assert alerts == []


def test_item_with_no_sales_history_produces_no_alert(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    db_session.add(InventoryItem(
        branch_id=branch.id, sku="NEW-001", name="New Item",
        current_stock=50, reorder_threshold=10, unit_cost=1.0,
    ))
    db_session.commit()

    alerts = analyze_inventory(db_session, branch.id)

    assert alerts == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_inventory.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.inventory'`

- [ ] **Step 3: Create `backend/app/schemas/inventory.py`**

```python
# backend/app/schemas/inventory.py
from pydantic import BaseModel


class InventoryAlert(BaseModel):
    sku: str
    name: str
    alert_type: str
    days_to_run_out: float | None
    current_stock: float
    suggested_reorder_qty: float
```

- [ ] **Step 4: Create `backend/app/services/inventory.py`**

```python
# backend/app/services/inventory.py
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import InventoryItem, SalesTransaction
from app.schemas.inventory import InventoryAlert


def analyze_inventory(
    db: Session,
    branch_id: int,
    lookback_days: int = 14,
    stockout_threshold_days: float = 3.0,
    overstock_threshold_days: float = 30.0,
) -> list[InventoryAlert]:
    items = db.query(InventoryItem).filter(InventoryItem.branch_id == branch_id).all()
    cutoff = datetime.utcnow() - timedelta(days=lookback_days)

    alerts: list[InventoryAlert] = []
    for item in items:
        total_qty = (
            db.query(func.sum(SalesTransaction.quantity))
            .filter(
                SalesTransaction.branch_id == branch_id,
                SalesTransaction.item == item.name,
                SalesTransaction.timestamp >= cutoff,
            )
            .scalar()
        ) or 0

        avg_daily_consumption = total_qty / lookback_days
        if avg_daily_consumption == 0:
            continue

        days_to_run_out = item.current_stock / avg_daily_consumption

        if days_to_run_out < stockout_threshold_days:
            target_stock = overstock_threshold_days * avg_daily_consumption
            suggested_qty = max(0.0, target_stock - item.current_stock)
            alerts.append(InventoryAlert(
                sku=item.sku,
                name=item.name,
                alert_type="stockout_risk",
                days_to_run_out=round(days_to_run_out, 1),
                current_stock=item.current_stock,
                suggested_reorder_qty=round(suggested_qty, 1),
            ))
        elif days_to_run_out > overstock_threshold_days:
            alerts.append(InventoryAlert(
                sku=item.sku,
                name=item.name,
                alert_type="overstock",
                days_to_run_out=round(days_to_run_out, 1),
                current_stock=item.current_stock,
                suggested_reorder_qty=0.0,
            ))

    return alerts
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_inventory.py -v`
Expected: PASS (4 tests)

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/inventory.py backend/app/schemas/inventory.py backend/tests/test_inventory.py
git commit -m "Add inventory intelligence service with stockout and overstock detection"
```

---

## Task 12: Inventory API routes (items CRUD-lite + alerts)

**Files:**
- Create: `backend/app/api/routes_inventory.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_api_inventory.py`

**Interfaces:**
- Consumes: `app.services.inventory.analyze_inventory`, `app.db.models.InventoryItem`.
- Produces: `POST /branches/{branch_id}/inventory-items` (create item), `GET /branches/{branch_id}/inventory-items` (list), `GET /branches/{branch_id}/inventory-alerts` (run `analyze_inventory` and return alerts). All require auth.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_api_inventory.py
from datetime import datetime, timedelta

from app.db.models import SalesTransaction


def _create_branch(client, auth_headers):
    response = client.post(
        "/branches", json={"name": "Downtown", "location": "Main St"}, headers=auth_headers
    )
    return response.json()["id"]


def test_create_and_list_inventory_items(client, auth_headers):
    branch_id = _create_branch(client, auth_headers)

    response = client.post(
        f"/branches/{branch_id}/inventory-items",
        json={"sku": "BUR-001", "name": "Burger", "current_stock": 50, "reorder_threshold": 10, "unit_cost": 2.0},
        headers=auth_headers,
    )
    assert response.status_code == 201

    response = client.get(f"/branches/{branch_id}/inventory-items", headers=auth_headers)
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["sku"] == "BUR-001"


def test_inventory_alerts_endpoint(client, auth_headers, db_session):
    branch_id = _create_branch(client, auth_headers)

    now = datetime.utcnow()
    for i in range(14):
        db_session.add(SalesTransaction(
            branch_id=branch_id,
            timestamp=now - timedelta(days=i),
            item="Burger",
            quantity=10,
            amount=50.0,
        ))
    db_session.commit()

    client.post(
        f"/branches/{branch_id}/inventory-items",
        json={"sku": "BUR-001", "name": "Burger", "current_stock": 15, "reorder_threshold": 10, "unit_cost": 2.0},
        headers=auth_headers,
    )

    response = client.get(f"/branches/{branch_id}/inventory-alerts", headers=auth_headers)
    assert response.status_code == 200
    alerts = response.json()
    assert len(alerts) == 1
    assert alerts[0]["alert_type"] == "stockout_risk"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_api_inventory.py -v`
Expected: FAIL with 404 (no inventory routes)

- [ ] **Step 3: Add `InventoryItemCreate`/`InventoryItemOut` schemas to `backend/app/schemas/inventory.py`**

```python
# backend/app/schemas/inventory.py — append below InventoryAlert
class InventoryItemCreate(BaseModel):
    sku: str
    name: str
    current_stock: float
    reorder_threshold: float
    unit_cost: float


class InventoryItemOut(InventoryItemCreate):
    id: int

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Create `backend/app/api/routes_inventory.py`**

```python
# backend/app/api/routes_inventory.py
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
```

- [ ] **Step 5: Wire the router into `backend/app/main.py`**

```python
# backend/app/main.py
from fastapi import FastAPI

from app.api.routes_auth import router as auth_router
from app.api.routes_branches import router as branches_router
from app.api.routes_uploads import router as uploads_router
from app.api.routes_forecasts import router as forecasts_router
from app.api.routes_inventory import router as inventory_router

app = FastAPI(title="Restaurant Analytics API")
app.include_router(auth_router)
app.include_router(branches_router)
app.include_router(uploads_router)
app.include_router(forecasts_router)
app.include_router(inventory_router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_api_inventory.py -v`
Expected: PASS (2 tests)

- [ ] **Step 7: Run full backend suite**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add backend/app/api/routes_inventory.py backend/app/main.py backend/app/schemas/inventory.py backend/tests/test_api_inventory.py
git commit -m "Add inventory items and alerts API endpoints"
```

---

## Task 13: Staffing service + API

**Files:**
- Create: `backend/app/services/staffing.py`
- Create: `backend/app/schemas/staffing.py`
- Create: `backend/app/api/routes_staffing.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_staffing.py`
- Test: `backend/tests/test_api_staffing.py`

**Interfaces:**
- Consumes: `app.db.models.SalesTransaction`, `app.db.models.StaffingRecommendation`, `app.db.models.Forecast`.
- Produces: `app.schemas.staffing.ShiftRecommendation(shift: str, date: date, recommended_staff_count: int, efficiency_score: float | None)`. `shift` is one of `"morning"` (6-12), `"afternoon"` (12-18), `"evening"` (18-23).
- Produces: `calculate_staffing(db: Session, branch_id: int, target_date: date, orders_per_staff: float = 15.0, actual_staff: dict[str, int] | None = None) -> list[ShiftRecommendation]`.
  - Buckets `SalesTransaction` rows for `target_date` (falls back across all history matching that date if present, else uses the most recent `Forecast.predicted_revenue` for that date divided by an assumed average order value of 12.0 as a proxy for order volume when no transactions exist for that date) by shift based on `timestamp.hour`.
  - `recommended_staff_count = max(1, ceil(shift_order_count / orders_per_staff))`.
  - If `actual_staff` provided for a shift: `efficiency_score = round(recommended / actual * 100, 1)` (capped at 200.0); else `None`.
  - Applies a 1.3x multiplier to `recommended_staff_count` if `target_date.weekday() >= 5` (weekend buffer) — applied before the `ceil`.
  - Persists each `ShiftRecommendation` as a `StaffingRecommendation` row (replacing any existing rows for that branch+date+shift).

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_staffing.py
from datetime import date, datetime

from app.db.models import Branch, SalesTransaction
from app.services.staffing import calculate_staffing


def test_calculate_staffing_buckets_by_shift(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()

    target_date = date(2026, 3, 2)  # Monday
    for hour, count in [(8, 30), (14, 45), (20, 15)]:
        for _ in range(count):
            db_session.add(SalesTransaction(
                branch_id=branch.id,
                timestamp=datetime(2026, 3, 2, hour, 0),
                item="Burger",
                quantity=1,
                amount=10.0,
            ))
    db_session.commit()

    recs = calculate_staffing(db_session, branch.id, target_date, orders_per_staff=15.0)

    by_shift = {r.shift: r for r in recs}
    assert by_shift["morning"].recommended_staff_count == 2
    assert by_shift["afternoon"].recommended_staff_count == 3
    assert by_shift["evening"].recommended_staff_count == 1


def test_weekend_buffer_increases_staffing(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()

    saturday = date(2026, 3, 7)
    for _ in range(30):
        db_session.add(SalesTransaction(
            branch_id=branch.id,
            timestamp=datetime(2026, 3, 7, 14, 0),
            item="Burger",
            quantity=1,
            amount=10.0,
        ))
    db_session.commit()

    recs = calculate_staffing(db_session, branch.id, saturday, orders_per_staff=15.0)
    afternoon = next(r for r in recs if r.shift == "afternoon")
    # 30 orders / 15 = 2, * 1.3 weekend buffer = 2.6 -> ceil -> 3
    assert afternoon.recommended_staff_count == 3


def test_efficiency_score_computed_when_actual_staff_given(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()

    target_date = date(2026, 3, 2)
    for _ in range(30):
        db_session.add(SalesTransaction(
            branch_id=branch.id,
            timestamp=datetime(2026, 3, 2, 14, 0),
            item="Burger",
            quantity=1,
            amount=10.0,
        ))
    db_session.commit()

    recs = calculate_staffing(
        db_session, branch.id, target_date, orders_per_staff=15.0,
        actual_staff={"afternoon": 4},
    )
    afternoon = next(r for r in recs if r.shift == "afternoon")
    assert afternoon.efficiency_score == 50.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_staffing.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.staffing'`

- [ ] **Step 3: Create `backend/app/schemas/staffing.py`**

```python
# backend/app/schemas/staffing.py
from datetime import date

from pydantic import BaseModel


class ShiftRecommendation(BaseModel):
    shift: str
    date: date
    recommended_staff_count: int
    efficiency_score: float | None = None
```

- [ ] **Step 4: Create `backend/app/services/staffing.py`**

```python
# backend/app/services/staffing.py
import math
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.db.models import SalesTransaction, StaffingRecommendation, Forecast
from app.schemas.staffing import ShiftRecommendation

SHIFT_HOURS = {
    "morning": range(6, 12),
    "afternoon": range(12, 18),
    "evening": range(18, 23),
}
ASSUMED_AVG_ORDER_VALUE = 12.0
WEEKEND_BUFFER_MULTIPLIER = 1.3


def _order_counts_by_shift(db: Session, branch_id: int, target_date: date) -> dict[str, int]:
    day_start = datetime(target_date.year, target_date.month, target_date.day)
    day_end = day_start + timedelta(days=1)

    transactions = (
        db.query(SalesTransaction)
        .filter(
            SalesTransaction.branch_id == branch_id,
            SalesTransaction.timestamp >= day_start,
            SalesTransaction.timestamp < day_end,
        )
        .all()
    )

    counts = {shift: 0 for shift in SHIFT_HOURS}
    if transactions:
        for txn in transactions:
            for shift, hours in SHIFT_HOURS.items():
                if txn.timestamp.hour in hours:
                    counts[shift] += 1
                    break
        return counts

    forecast = (
        db.query(Forecast)
        .filter(Forecast.branch_id == branch_id, Forecast.date == target_date)
        .first()
    )
    if forecast:
        total_orders = forecast.predicted_revenue / ASSUMED_AVG_ORDER_VALUE
        per_shift = total_orders / len(SHIFT_HOURS)
        return {shift: per_shift for shift in SHIFT_HOURS}

    return counts


def calculate_staffing(
    db: Session,
    branch_id: int,
    target_date: date,
    orders_per_staff: float = 15.0,
    actual_staff: dict[str, int] | None = None,
) -> list[ShiftRecommendation]:
    actual_staff = actual_staff or {}
    counts = _order_counts_by_shift(db, branch_id, target_date)
    is_weekend = target_date.weekday() >= 5

    db.query(StaffingRecommendation).filter(
        StaffingRecommendation.branch_id == branch_id,
        StaffingRecommendation.date == target_date,
    ).delete()

    recommendations = []
    for shift, order_count in counts.items():
        raw_count = order_count / orders_per_staff
        if is_weekend:
            raw_count *= WEEKEND_BUFFER_MULTIPLIER
        recommended = max(1, math.ceil(raw_count))

        efficiency_score = None
        if shift in actual_staff and actual_staff[shift] > 0:
            efficiency_score = round(min(200.0, recommended / actual_staff[shift] * 100), 1)

        rec = ShiftRecommendation(
            shift=shift,
            date=target_date,
            recommended_staff_count=recommended,
            efficiency_score=efficiency_score,
        )
        recommendations.append(rec)
        db.add(StaffingRecommendation(
            branch_id=branch_id,
            shift=rec.shift,
            date=rec.date,
            recommended_staff_count=rec.recommended_staff_count,
            efficiency_score=rec.efficiency_score,
        ))

    db.commit()
    return recommendations
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_staffing.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Write the failing API test**

```python
# backend/tests/test_api_staffing.py
from datetime import datetime


def test_staffing_endpoint_returns_recommendations(client, auth_headers, db_session):
    response = client.post(
        "/branches", json={"name": "Downtown", "location": "Main St"}, headers=auth_headers
    )
    branch_id = response.json()["id"]

    from app.db.models import SalesTransaction
    for _ in range(30):
        db_session.add(SalesTransaction(
            branch_id=branch_id,
            timestamp=datetime(2026, 3, 2, 14, 0),
            item="Burger",
            quantity=1,
            amount=10.0,
        ))
    db_session.commit()

    response = client.get(
        f"/branches/{branch_id}/staffing?target_date=2026-03-02", headers=auth_headers
    )
    assert response.status_code == 200
    recs = response.json()
    assert len(recs) == 3
    shifts = {r["shift"] for r in recs}
    assert shifts == {"morning", "afternoon", "evening"}
```

- [ ] **Step 7: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_api_staffing.py -v`
Expected: FAIL with 404 (no `/branches/{branch_id}/staffing` route)

- [ ] **Step 8: Create `backend/app/api/routes_staffing.py`**

```python
# backend/app/api/routes_staffing.py
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
```

- [ ] **Step 9: Wire the router into `backend/app/main.py`**

```python
# backend/app/main.py
from fastapi import FastAPI

from app.api.routes_auth import router as auth_router
from app.api.routes_branches import router as branches_router
from app.api.routes_uploads import router as uploads_router
from app.api.routes_forecasts import router as forecasts_router
from app.api.routes_inventory import router as inventory_router
from app.api.routes_staffing import router as staffing_router

app = FastAPI(title="Restaurant Analytics API")
app.include_router(auth_router)
app.include_router(branches_router)
app.include_router(uploads_router)
app.include_router(forecasts_router)
app.include_router(inventory_router)
app.include_router(staffing_router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 10: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_api_staffing.py -v`
Expected: PASS (1 test)

- [ ] **Step 11: Run full backend suite**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 12: Commit**

```bash
git add backend/app/services/staffing.py backend/app/schemas/staffing.py backend/app/api/routes_staffing.py backend/app/main.py backend/tests/test_staffing.py backend/tests/test_api_staffing.py
git commit -m "Add staffing recommendation service and API endpoint"
```

---

**Continued in Part 4** (`docs/superpowers/plans/2026-06-25-restaurant-ai-dashboard-part4.md`): Tasks 14-16 — LLM insight layer (OpenRouter/DeepSeek client, prompt + schema validation + fallback, rate limiting), Dashboard aggregation API (KPIs + heatmap).
