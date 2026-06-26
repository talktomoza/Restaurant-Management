# AI-Powered Restaurant Analytics Dashboard Implementation Plan — Part 2 (Tasks 7-11)

> Continuation of `2026-06-25-restaurant-ai-dashboard.md`. Same Global Constraints apply. Continue using superpowers:subagent-driven-development or superpowers:executing-plans.

---

## Task 7: CSV upload API route

**Files:**
- Create: `backend/app/api/routes_uploads.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_api_uploads.py`

**Interfaces:**
- Consumes: `app.services.csv_ingestion.parse_and_store_csv`, `app.schemas.upload.ColumnMapping`, `app.api.deps.get_current_user`.
- Produces: `POST /branches/{branch_id}/uploads` — multipart form with `file` (CSV) and JSON-encoded `mapping` field; returns `{"rows_imported": int, "rows_rejected": int, "errors": list[str]}` with HTTP 201 if `rows_imported > 0`, else HTTP 422 with the errors.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_api_uploads.py
import json


def _create_branch(client, auth_headers):
    response = client.post(
        "/branches", json={"name": "Downtown", "location": "Main St"}, headers=auth_headers
    )
    return response.json()["id"]


def test_upload_csv_success(client, auth_headers):
    branch_id = _create_branch(client, auth_headers)
    csv_content = (
        "Date,Item,Qty,Total\n"
        "2026-01-01 12:00,Burger,2,19.98\n"
        "2026-01-01 12:05,Fries,1,3.99\n"
    )
    mapping = {
        "date_column": "Date",
        "item_column": "Item",
        "quantity_column": "Qty",
        "amount_column": "Total",
    }
    response = client.post(
        f"/branches/{branch_id}/uploads",
        files={"file": ("sales.csv", csv_content, "text/csv")},
        data={"mapping": json.dumps(mapping)},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["rows_imported"] == 2
    assert body["rows_rejected"] == 0


def test_upload_csv_missing_columns_returns_422(client, auth_headers):
    branch_id = _create_branch(client, auth_headers)
    mapping = {
        "date_column": "Date",
        "item_column": "Item",
        "quantity_column": "Qty",
        "amount_column": "Total",
    }
    response = client.post(
        f"/branches/{branch_id}/uploads",
        files={"file": ("sales.csv", "Date,Item,Qty\n2026-01-01,Burger,2\n", "text/csv")},
        data={"mapping": json.dumps(mapping)},
        headers=auth_headers,
    )
    assert response.status_code == 422
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_api_uploads.py -v`
Expected: FAIL with 404 (no `/branches/{branch_id}/uploads` route)

- [ ] **Step 3: Create `backend/app/api/routes_uploads.py`**

```python
# backend/app/api/routes_uploads.py
import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db
from app.db.models import User
from app.schemas.upload import ColumnMapping
from app.services.csv_ingestion import parse_and_store_csv

router = APIRouter(prefix="/branches", tags=["uploads"])

MAX_FILE_BYTES = 10 * 1024 * 1024


@router.post("/{branch_id}/uploads", status_code=status.HTTP_201_CREATED)
async def upload_csv(
    branch_id: int,
    file: UploadFile = File(...),
    mapping: str = Form(...),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
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
```

- [ ] **Step 4: Wire the router into `backend/app/main.py`**

```python
# backend/app/main.py
from fastapi import FastAPI

from app.api.routes_auth import router as auth_router
from app.api.routes_branches import router as branches_router
from app.api.routes_uploads import router as uploads_router

app = FastAPI(title="Restaurant Analytics API")
app.include_router(auth_router)
app.include_router(branches_router)
app.include_router(uploads_router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_api_uploads.py -v`
Expected: PASS (2 tests)

- [ ] **Step 6: Run full backend suite**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/routes_uploads.py backend/app/main.py backend/tests/test_api_uploads.py
git commit -m "Add CSV upload API endpoint with size/type validation"
```

---

## Task 8: Synthetic data generator script

**Files:**
- Create: `backend/scripts/__init__.py`
- Create: `backend/scripts/generate_synthetic_data.py`
- Test: `backend/tests/test_generate_synthetic_data.py`

**Interfaces:**
- Produces: `generate_branch_sales(branch_name: str, start_date: date, num_days: int, base_daily_revenue: float, seed: int) -> pandas.DataFrame` with columns `Date, Item, Qty, Total`, modeling weekly seasonality (weekend uplift), a small set of menu items, and holiday spikes on a fixed list of dates (New Year's Day, Christmas Eve/Day, Valentine's Day, Thanksgiving — all falling within `start_date`..`start_date+num_days`).
- Produces: CLI entry point (`if __name__ == "__main__":`) that writes one CSV per branch to `backend/scripts/output/<branch_name>.csv` for branches `["Downtown", "Uptown", "Riverside"]`, 365 days of history ending today.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_generate_synthetic_data.py
from datetime import date

from scripts.generate_synthetic_data import generate_branch_sales


def test_generate_branch_sales_shape_and_columns():
    df = generate_branch_sales(
        branch_name="Downtown",
        start_date=date(2026, 1, 1),
        num_days=30,
        base_daily_revenue=1000.0,
        seed=42,
    )
    assert list(df.columns) == ["Date", "Item", "Qty", "Total"]
    assert len(df) > 0
    assert (df["Qty"] > 0).all()
    assert (df["Total"] > 0).all()


def test_generate_branch_sales_is_deterministic_with_seed():
    df1 = generate_branch_sales("Downtown", date(2026, 1, 1), 30, 1000.0, seed=7)
    df2 = generate_branch_sales("Downtown", date(2026, 1, 1), 30, 1000.0, seed=7)
    assert df1["Total"].sum() == df2["Total"].sum()


def test_weekend_revenue_exceeds_weekday_on_average():
    df = generate_branch_sales("Downtown", date(2026, 1, 1), 90, 1000.0, seed=1)
    df["Date"] = df["Date"].astype("datetime64[ns]")
    df["dow"] = df["Date"].dt.dayofweek
    weekday_avg = df[df["dow"] < 5].groupby(df["Date"].dt.date)["Total"].sum().mean()
    weekend_avg = df[df["dow"] >= 5].groupby(df["Date"].dt.date)["Total"].sum().mean()
    assert weekend_avg > weekday_avg
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_generate_synthetic_data.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'scripts'`

- [ ] **Step 3: Create `backend/scripts/__init__.py` (empty) and `backend/scripts/generate_synthetic_data.py`**

```python
# backend/scripts/generate_synthetic_data.py
import os
import random
from datetime import date, timedelta

import pandas as pd

MENU_ITEMS = [
    ("Burger", 9.99),
    ("Fries", 3.99),
    ("Soda", 2.50),
    ("Salad", 7.49),
    ("Pizza Slice", 4.99),
    ("Pasta", 11.99),
]

HOLIDAY_MONTH_DAY = {(1, 1), (12, 24), (12, 25), (2, 14), (11, 27)}


def _is_holiday(d: date) -> bool:
    return (d.month, d.day) in HOLIDAY_MONTH_DAY


def generate_branch_sales(
    branch_name: str,
    start_date: date,
    num_days: int,
    base_daily_revenue: float,
    seed: int = 0,
) -> pd.DataFrame:
    rng = random.Random(seed)
    rows = []

    for day_offset in range(num_days):
        current_date = start_date + timedelta(days=day_offset)
        is_weekend = current_date.weekday() >= 5
        multiplier = 1.0
        if is_weekend:
            multiplier *= 1.4
        if _is_holiday(current_date):
            multiplier *= 1.8

        target_revenue = base_daily_revenue * multiplier
        revenue_so_far = 0.0
        # Generate transactions until we roughly hit the day's target revenue.
        while revenue_so_far < target_revenue:
            item, price = rng.choice(MENU_ITEMS)
            quantity = rng.randint(1, 4)
            hour = rng.randint(10, 21)
            minute = rng.randint(0, 59)
            amount = round(price * quantity, 2)
            rows.append({
                "Date": f"{current_date.isoformat()} {hour:02d}:{minute:02d}",
                "Item": item,
                "Qty": quantity,
                "Total": amount,
            })
            revenue_so_far += amount

    return pd.DataFrame(rows, columns=["Date", "Item", "Qty", "Total"])


if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)

    branches = [
        ("Downtown", 1200.0),
        ("Uptown", 900.0),
        ("Riverside", 1500.0),
    ]
    start = date.today() - timedelta(days=365)

    for branch_name, base_revenue in branches:
        df = generate_branch_sales(branch_name, start, 365, base_revenue, seed=hash(branch_name) % 1000)
        path = os.path.join(output_dir, f"{branch_name}.csv")
        df.to_csv(path, index=False)
        print(f"Wrote {len(df)} rows to {path}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_generate_synthetic_data.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Manually generate sample CSVs for later manual testing**

Run: `cd backend && python -m scripts.generate_synthetic_data`
Expected: Prints "Wrote N rows to .../output/Downtown.csv" etc. for 3 branches.

- [ ] **Step 6: Add generated output to `.gitignore`**

```
# Append to .gitignore at repo root
backend/scripts/output/
```

- [ ] **Step 7: Commit**

```bash
git add backend/scripts/__init__.py backend/scripts/generate_synthetic_data.py backend/tests/test_generate_synthetic_data.py .gitignore
git commit -m "Add synthetic restaurant sales data generator with seasonality and holiday spikes"
```

---

## Task 9: Forecasting service (Prophet wrapper)

**Files:**
- Create: `backend/app/services/forecasting.py`
- Create: `backend/app/schemas/forecast.py`
- Test: `backend/tests/test_forecasting.py`

**Interfaces:**
- Consumes: `app.db.models.SalesTransaction`, `app.db.models.Forecast`, a SQLAlchemy `Session`.
- Produces: `app.schemas.forecast.ForecastPoint(date: date, predicted_revenue: float, lower_bound: float, upper_bound: float)`.
- Produces: `generate_forecast(db: Session, branch_id: int, horizon_days: int) -> list[ForecastPoint]`. Aggregates `SalesTransaction.amount` by day for the branch, requires at least 14 distinct days of history (raises `ValueError` otherwise), fits a `prophet.Prophet` model with weekly seasonality enabled, predicts `horizon_days` into the future, deletes any existing `Forecast` rows for that branch with `date >= today`, persists new `Forecast` rows, and returns the `ForecastPoint` list.
- Produces: `evaluate_forecast_accuracy(db: Session, branch_id: int) -> dict` with keys `mae_pct: float`, `rmse_pct: float`, computed by holding out the last 14 days of history, fitting on the rest, predicting those 14 days, and comparing — returns `{"mae_pct": None, "rmse_pct": None}` if fewer than 28 days of history exist.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_forecasting.py
from datetime import datetime, timedelta

import pytest

from app.db.models import Branch, SalesTransaction
from app.services.forecasting import generate_forecast, evaluate_forecast_accuracy


def _seed_transactions(db_session, branch_id, num_days, base_amount=100.0):
    start = datetime.utcnow() - timedelta(days=num_days)
    for i in range(num_days):
        day = start + timedelta(days=i)
        amount = base_amount + (20.0 if day.weekday() >= 5 else 0.0)
        db_session.add(SalesTransaction(
            branch_id=branch_id,
            timestamp=day,
            item="Burger",
            quantity=1,
            amount=amount,
        ))
    db_session.commit()


def test_generate_forecast_requires_minimum_history(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    _seed_transactions(db_session, branch.id, num_days=5)

    with pytest.raises(ValueError):
        generate_forecast(db_session, branch.id, horizon_days=7)


def test_generate_forecast_returns_points_with_bounds(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    _seed_transactions(db_session, branch.id, num_days=60)

    points = generate_forecast(db_session, branch.id, horizon_days=7)

    assert len(points) == 7
    for point in points:
        assert point.lower_bound <= point.predicted_revenue <= point.upper_bound


def test_evaluate_forecast_accuracy_returns_none_with_insufficient_history(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    _seed_transactions(db_session, branch.id, num_days=10)

    result = evaluate_forecast_accuracy(db_session, branch.id)

    assert result["mae_pct"] is None
    assert result["rmse_pct"] is None


def test_evaluate_forecast_accuracy_returns_percentages(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    _seed_transactions(db_session, branch.id, num_days=60)

    result = evaluate_forecast_accuracy(db_session, branch.id)

    assert result["mae_pct"] is not None
    assert result["mae_pct"] >= 0
    assert result["rmse_pct"] >= 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_forecasting.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.forecasting'`

- [ ] **Step 3: Create `backend/app/schemas/forecast.py`**

```python
# backend/app/schemas/forecast.py
from datetime import date

from pydantic import BaseModel


class ForecastPoint(BaseModel):
    date: date
    predicted_revenue: float
    lower_bound: float
    upper_bound: float
```

- [ ] **Step 4: Create `backend/app/services/forecasting.py`**

```python
# backend/app/services/forecasting.py
from datetime import date, datetime, timedelta

import pandas as pd
from prophet import Prophet
from sqlalchemy.orm import Session

from app.db.models import SalesTransaction, Forecast
from app.schemas.forecast import ForecastPoint

MIN_HISTORY_DAYS = 14
MIN_EVAL_HISTORY_DAYS = 28
EVAL_HOLDOUT_DAYS = 14


def _daily_revenue_df(db: Session, branch_id: int) -> pd.DataFrame:
    rows = (
        db.query(SalesTransaction)
        .filter(SalesTransaction.branch_id == branch_id)
        .all()
    )
    df = pd.DataFrame([{"ds": r.timestamp.date(), "y": r.amount} for r in rows])
    if df.empty:
        return df
    daily = df.groupby("ds", as_index=False)["y"].sum()
    daily["ds"] = pd.to_datetime(daily["ds"])
    return daily.sort_values("ds")


def generate_forecast(db: Session, branch_id: int, horizon_days: int) -> list[ForecastPoint]:
    daily = _daily_revenue_df(db, branch_id)
    if len(daily) < MIN_HISTORY_DAYS:
        raise ValueError(
            f"Need at least {MIN_HISTORY_DAYS} days of history, found {len(daily)}"
        )

    model = Prophet(weekly_seasonality=True, daily_seasonality=False)
    model.fit(daily)

    future = model.make_future_dataframe(periods=horizon_days)
    forecast = model.predict(future)
    forecast_tail = forecast.tail(horizon_days)

    today = date.today()
    db.query(Forecast).filter(
        Forecast.branch_id == branch_id, Forecast.date >= today
    ).delete()

    points = []
    for _, row in forecast_tail.iterrows():
        point_date = row["ds"].date()
        point = ForecastPoint(
            date=point_date,
            predicted_revenue=max(0.0, float(row["yhat"])),
            lower_bound=max(0.0, float(row["yhat_lower"])),
            upper_bound=max(0.0, float(row["yhat_upper"])),
        )
        points.append(point)
        db.add(Forecast(
            branch_id=branch_id,
            date=point.date,
            predicted_revenue=point.predicted_revenue,
            lower_bound=point.lower_bound,
            upper_bound=point.upper_bound,
            generated_at=datetime.utcnow(),
        ))

    db.commit()
    return points


def evaluate_forecast_accuracy(db: Session, branch_id: int) -> dict:
    daily = _daily_revenue_df(db, branch_id)
    if len(daily) < MIN_EVAL_HISTORY_DAYS:
        return {"mae_pct": None, "rmse_pct": None}

    train = daily.iloc[:-EVAL_HOLDOUT_DAYS]
    holdout = daily.iloc[-EVAL_HOLDOUT_DAYS:]

    model = Prophet(weekly_seasonality=True, daily_seasonality=False)
    model.fit(train)

    future = model.make_future_dataframe(periods=EVAL_HOLDOUT_DAYS)
    forecast = model.predict(future)
    predicted = forecast.tail(EVAL_HOLDOUT_DAYS)["yhat"].to_numpy()
    actual = holdout["y"].to_numpy()

    errors = predicted - actual
    mae = abs(errors).mean()
    rmse = (errors ** 2).mean() ** 0.5
    mean_actual = actual.mean() if actual.mean() != 0 else 1.0

    return {
        "mae_pct": round(float(mae / mean_actual * 100), 2),
        "rmse_pct": round(float(rmse / mean_actual * 100), 2),
    }
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_forecasting.py -v`
Expected: PASS (4 tests). Note: Prophet fitting is slow (a few seconds per test) — this is expected.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/forecasting.py backend/app/schemas/forecast.py backend/tests/test_forecasting.py
git commit -m "Add Prophet-based forecasting service with accuracy evaluation"
```

---

## Task 10: Forecasts API route

**Files:**
- Create: `backend/app/api/routes_forecasts.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_api_forecasts.py`

**Interfaces:**
- Consumes: `app.services.forecasting.generate_forecast`, `app.services.forecasting.evaluate_forecast_accuracy`.
- Produces: `POST /branches/{branch_id}/forecasts?horizon_days=7` — runs forecast generation, returns list of forecast points; `GET /branches/{branch_id}/forecasts/accuracy` — returns accuracy dict. Both require auth. Returns HTTP 422 with detail message if `ValueError` raised (insufficient history).

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_api_forecasts.py
from datetime import datetime, timedelta

from app.db.models import Branch, SalesTransaction


def _seed_branch_with_history(db_session, num_days=60):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()
    start = datetime.utcnow() - timedelta(days=num_days)
    for i in range(num_days):
        db_session.add(SalesTransaction(
            branch_id=branch.id,
            timestamp=start + timedelta(days=i),
            item="Burger",
            quantity=1,
            amount=100.0,
        ))
    db_session.commit()
    return branch.id


def test_generate_forecast_endpoint(client, auth_headers, db_session):
    branch_id = _seed_branch_with_history(db_session)

    response = client.post(
        f"/branches/{branch_id}/forecasts?horizon_days=7", headers=auth_headers
    )
    assert response.status_code == 200
    points = response.json()
    assert len(points) == 7


def test_forecast_endpoint_insufficient_history_returns_422(client, auth_headers, db_session):
    branch_id = _seed_branch_with_history(db_session, num_days=5)

    response = client.post(
        f"/branches/{branch_id}/forecasts?horizon_days=7", headers=auth_headers
    )
    assert response.status_code == 422
```

- [ ] **Step 2: Note on test fixture dependency**

This test needs `db_session` to write into the same database the `client` fixture uses. Update `backend/tests/conftest.py`'s `client` fixture to also expose its session-maker so tests can seed data through it directly:

```python
# backend/tests/conftest.py — replace the `client` and add a `db_session` that shares api_engine
@pytest.fixture
def db_session(api_engine):
    TestingSessionLocal = sessionmaker(bind=api_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
```

Remove the standalone `db_session` fixture defined earlier in Task 2 that created its own isolated in-memory engine, since `test_models.py` and `test_csv_ingestion.py` and `test_forecasting.py` must now receive `db_session` built from the same `api_engine` fixture used by `client` so that API tests and direct-DB-seeding tests share state within a single test function. Since `api_engine` is function-scoped (default), this is safe — each test still gets an isolated database, but within one test, `db_session` and `client` now see the same data.

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_api_forecasts.py -v`
Expected: FAIL with 404 (no `/branches/{branch_id}/forecasts` route)

- [ ] **Step 4: Run the full existing suite to confirm the conftest change didn't break earlier tests**

Run: `cd backend && python -m pytest tests/test_models.py tests/test_csv_ingestion.py tests/test_forecasting.py -v`
Expected: All PASS (the `db_session` fixture signature is unchanged from the caller's perspective — only its internal wiring changed)

- [ ] **Step 5: Create `backend/app/api/routes_forecasts.py`**

```python
# backend/app/api/routes_forecasts.py
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
```

- [ ] **Step 6: Wire the router into `backend/app/main.py`**

```python
# backend/app/main.py
from fastapi import FastAPI

from app.api.routes_auth import router as auth_router
from app.api.routes_branches import router as branches_router
from app.api.routes_uploads import router as uploads_router
from app.api.routes_forecasts import router as forecasts_router

app = FastAPI(title="Restaurant Analytics API")
app.include_router(auth_router)
app.include_router(branches_router)
app.include_router(uploads_router)
app.include_router(forecasts_router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 7: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_api_forecasts.py -v`
Expected: PASS (2 tests)

- [ ] **Step 8: Run full backend suite**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 9: Commit**

```bash
git add backend/app/api/routes_forecasts.py backend/app/main.py backend/tests/test_api_forecasts.py backend/tests/conftest.py
git commit -m "Add forecasts API endpoint with accuracy evaluation route"
```

---

**Continued in Part 3** (`docs/superpowers/plans/2026-06-25-restaurant-ai-dashboard-part3.md`): Tasks 11-13 — Inventory intelligence service + API, Staffing service + API.
