# AI-Powered Restaurant Analytics Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an end-to-end restaurant analytics platform: CSV ingestion, Prophet-based revenue forecasting, inventory intelligence, staffing recommendations, an LLM (DeepSeek via OpenRouter) insight layer, and a Next.js dashboard, backed by FastAPI + PostgreSQL.

**Architecture:** FastAPI backend organized as `api/` (routes) → `services/` (forecasting, inventory, staffing, insights business logic) → `db/` (SQLAlchemy models). Next.js frontend consumes the REST API. PostgreSQL via Docker Compose for local dev. Synthetic data generator script seeds realistic multi-branch sales history.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, Prophet, pytest, PostgreSQL, Next.js (React, TypeScript), TailwindCSS, Recharts, Vitest + React Testing Library, OpenRouter API (DeepSeek free tier), Docker Compose, pip + requirements.txt, npm.

## Global Constraints

- Backend dependency management: pip + `requirements.txt` (no Poetry).
- Frontend package manager: npm (no pnpm/yarn).
- Synthetic data generator lives at `backend/scripts/generate_synthetic_data.py`.
- Secrets (DB credentials, `OPENROUTER_API_KEY`) live in `.env`, excluded via `.gitignore`. Never hardcode.
- LLM calls go through OpenRouter to a DeepSeek free-tier model; system prompt fixes role + JSON output schema; user data passed as labeled fields, never as instructions.
- All LLM JSON responses validated against a Pydantic schema before storage/display; on validation failure, retry once, then fall back to a rule-based templated summary.
- Insight generation is rate-limited to once per hour per branch.
- Auth: JWT-protected API routes, bcrypt-hashed passwords, single-tenant (one owner, multiple branches).
- Every task ends in a commit. Follow TDD: failing test → minimal implementation → passing test → commit.

---

## File Structure

```
backend/
  app/
    main.py                      # FastAPI app factory, router includes
    config.py                    # Settings (env vars) via pydantic-settings
    db/
      base.py                    # SQLAlchemy engine/session/Base
      models.py                  # All ORM models
    schemas/
      auth.py                    # Pydantic: UserCreate, Token, etc.
      branch.py
      upload.py
      forecast.py
      inventory.py
      staffing.py
      insight.py
    services/
      auth_service.py            # password hashing, JWT issue/verify
      csv_ingestion.py           # CSV parse + column mapping + validation
      forecasting.py             # Prophet wrapper
      inventory.py               # stockout/overstock/reorder logic
      staffing.py                # shift staffing calculation
      insight_service.py         # LLM prompt build, call, validate, fallback
      openrouter_client.py       # thin HTTP client for OpenRouter
    api/
      deps.py                    # get_db, get_current_user dependencies
      routes_auth.py
      routes_branches.py
      routes_uploads.py
      routes_forecasts.py
      routes_inventory.py
      routes_staffing.py
      routes_insights.py
      routes_dashboard.py        # KPI + heatmap aggregation endpoints
  scripts/
    generate_synthetic_data.py
  tests/
    conftest.py
    test_csv_ingestion.py
    test_forecasting.py
    test_inventory.py
    test_staffing.py
    test_insight_service.py
    test_auth_service.py
    test_api_integration.py
  requirements.txt
  Dockerfile
  .env.example

frontend/
  app/
    layout.tsx
    page.tsx                     # Dashboard page
    login/page.tsx
    upload/page.tsx
  components/
    KpiCard.tsx
    PeakHourHeatmap.tsx
    ForecastChart.tsx
    InventoryPanel.tsx
    StaffingPanel.tsx
    InsightPanel.tsx
    BranchDateFilter.tsx
    CsvUploadWizard.tsx
  lib/
    api.ts                       # fetch wrapper, typed API calls
    types.ts                     # shared TS types mirroring backend schemas
    auth.ts                      # token storage/retrieval
  tests/
    KpiCard.test.tsx
    ForecastChart.test.tsx
    InsightPanel.test.tsx
  package.json
  tailwind.config.ts
  Dockerfile
  .env.local.example

docker-compose.yml
README.md
.gitignore (already created)
```

---

## Task 1: Backend project scaffolding and config

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/config.py`
- Create: `backend/app/main.py`
- Create: `backend/.env.example`
- Test: `backend/tests/test_config.py`

**Interfaces:**
- Produces: `app.config.Settings` class with fields `database_url: str`, `jwt_secret: str`, `openrouter_api_key: str`, `openrouter_model: str = "deepseek/deepseek-chat-v3-0324:free"`, loaded via `pydantic-settings` from `.env`. Exposes singleton `get_settings()`.
- Produces: `app.main.app` — a `FastAPI()` instance with a `/health` GET route returning `{"status": "ok"}`.

- [ ] **Step 1: Create `backend/requirements.txt`**

```
fastapi==0.115.6
uvicorn[standard]==0.32.1
sqlalchemy==2.0.36
psycopg2-binary==2.9.10
pydantic==2.10.3
pydantic-settings==2.7.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
prophet==1.1.6
pandas==2.2.3
httpx==0.28.1
python-multipart==0.0.20
pytest==8.3.4
pytest-asyncio==0.25.0
```

- [ ] **Step 2: Create `backend/.env.example`**

```
DATABASE_URL=postgresql://restaurant:restaurant@localhost:5432/restaurant_db
JWT_SECRET=change-me-to-a-random-secret
OPENROUTER_API_KEY=
OPENROUTER_MODEL=deepseek/deepseek-chat-v3-0324:free
```

- [ ] **Step 3: Write the failing test for config**

```python
# backend/tests/test_config.py
import os

def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5432/db")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    from app.config import get_settings
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.database_url == "postgresql://u:p@localhost:5432/db"
    assert settings.jwt_secret == "test-secret"
    assert settings.openrouter_api_key == "test-key"
    assert settings.openrouter_model == "deepseek/deepseek-chat-v3-0324:free"
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app'` or `app.config`

- [ ] **Step 5: Create `backend/app/__init__.py` (empty) and `backend/app/config.py`**

```python
# backend/app/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    jwt_secret: str
    openrouter_api_key: str = ""
    openrouter_model: str = "deepseek/deepseek-chat-v3-0324:free"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 7: Create `backend/app/main.py` with health route**

```python
# backend/app/main.py
from fastapi import FastAPI

app = FastAPI(title="Restaurant Analytics API")


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 8: Add a smoke test for the health route**

```python
# backend/tests/test_main.py
from fastapi.testclient import TestClient
from app.main import app


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 9: Run all backend tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All PASS (2 tests). Note: `test_main.py` needs `DATABASE_URL`/`JWT_SECRET` env vars set or a `.env` file present — create a local `backend/.env` (not committed) copied from `.env.example` with dummy values before running.

- [ ] **Step 10: Commit**

```bash
git add backend/requirements.txt backend/.env.example backend/app/__init__.py backend/app/config.py backend/app/main.py backend/tests/test_config.py backend/tests/test_main.py
git commit -m "Scaffold FastAPI backend with settings and health endpoint"
```

---

## Task 2: Database models and session management

**Files:**
- Create: `backend/app/db/__init__.py`
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/models.py`
- Test: `backend/tests/test_models.py`
- Modify: `backend/tests/conftest.py`

**Interfaces:**
- Consumes: `app.config.get_settings()` from Task 1.
- Produces: `app.db.base.Base` (declarative base), `app.db.base.engine`, `app.db.base.SessionLocal`, `app.db.base.get_db()` generator dependency.
- Produces ORM models in `app.db.models`: `Branch`, `User`, `SalesTransaction`, `InventoryItem`, `Forecast`, `StaffingRecommendation`, `CsvUpload`, `AiInsight`, each with `id: int` primary key.

- [ ] **Step 1: Write `backend/tests/conftest.py` with a SQLite test DB fixture**

```python
# backend/tests/conftest.py
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
```

- [ ] **Step 2: Write the failing test for models**

```python
# backend/tests/test_models.py
from datetime import datetime, date

from app.db.models import Branch, User, SalesTransaction, InventoryItem


def test_create_branch_and_transaction(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()

    txn = SalesTransaction(
        branch_id=branch.id,
        timestamp=datetime(2026, 1, 1, 12, 0),
        item="Burger",
        quantity=2,
        amount=19.98,
    )
    db_session.add(txn)
    db_session.commit()

    assert branch.id is not None
    assert txn.branch_id == branch.id


def test_create_user_and_inventory_item(db_session):
    user = User(email="owner@example.com", hashed_password="hashed")
    branch = Branch(name="Uptown", location="2nd Ave")
    db_session.add_all([user, branch])
    db_session.commit()

    item = InventoryItem(
        branch_id=branch.id,
        sku="BUN-001",
        name="Burger Bun",
        current_stock=100,
        reorder_threshold=20,
        unit_cost=0.5,
    )
    db_session.add(item)
    db_session.commit()

    assert user.id is not None
    assert item.id is not None
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.db'`

- [ ] **Step 4: Create `backend/app/db/__init__.py` (empty) and `backend/app/db/base.py`**

```python
# backend/app/db/base.py
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 5: Create `backend/app/db/models.py`**

```python
# backend/app/db/models.py
from datetime import datetime, date

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, ForeignKey, JSON, Text
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class Branch(Base):
    __tablename__ = "branches"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)


class SalesTransaction(Base):
    __tablename__ = "sales_transactions"

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    item = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    sku = Column(String, nullable=False)
    name = Column(String, nullable=False)
    current_stock = Column(Float, nullable=False)
    reorder_threshold = Column(Float, nullable=False)
    unit_cost = Column(Float, nullable=False)


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    date = Column(Date, nullable=False)
    predicted_revenue = Column(Float, nullable=False)
    lower_bound = Column(Float, nullable=False)
    upper_bound = Column(Float, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)


class StaffingRecommendation(Base):
    __tablename__ = "staffing_recommendations"

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    shift = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    recommended_staff_count = Column(Integer, nullable=False)
    efficiency_score = Column(Float, nullable=True)


class CsvUpload(Base):
    __tablename__ = "csv_uploads"

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    filename = Column(String, nullable=False)
    column_mapping = Column(JSON, nullable=False)
    status = Column(String, nullable=False, default="pending")
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class AiInsight(Base):
    __tablename__ = "ai_insights"

    id = Column(Integer, primary_key=True)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=False)
    type = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_models.py -v`
Expected: PASS (2 tests)

- [ ] **Step 7: Commit**

```bash
git add backend/app/db backend/tests/conftest.py backend/tests/test_models.py
git commit -m "Add SQLAlchemy models and test database fixtures"
```

---

## Task 3: Auth service (password hashing + JWT)

**Files:**
- Create: `backend/app/services/auth_service.py`
- Create: `backend/app/schemas/auth.py`
- Test: `backend/tests/test_auth_service.py`

**Interfaces:**
- Consumes: `app.config.get_settings()`.
- Produces: `hash_password(password: str) -> str`, `verify_password(password: str, hashed: str) -> bool`, `create_access_token(subject: str) -> str`, `decode_access_token(token: str) -> str` (returns subject, raises `ValueError` on invalid/expired token).
- Produces: `app.schemas.auth.UserCreate(email: str, password: str)`, `app.schemas.auth.Token(access_token: str, token_type: str = "bearer")`.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_auth_service.py
import pytest

from app.services.auth_service import (
    hash_password, verify_password, create_access_token, decode_access_token
)


def test_hash_and_verify_password():
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert verify_password("secret123", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_token():
    token = create_access_token("owner@example.com")
    subject = decode_access_token(token)
    assert subject == "owner@example.com"


def test_decode_invalid_token_raises():
    with pytest.raises(ValueError):
        decode_access_token("not-a-real-token")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_auth_service.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services'`

- [ ] **Step 3: Create `backend/app/services/__init__.py` (empty) and `backend/app/services/auth_service.py`**

```python
# backend/app/services/auth_service.py
from datetime import datetime, timedelta, timezone

from jose import jwt, JWTError
from passlib.context import CryptContext

from app.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return _pwd_context.verify(password, hashed)


def create_access_token(subject: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
    subject = payload.get("sub")
    if subject is None:
        raise ValueError("Token missing subject")
    return subject
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_auth_service.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Create `backend/app/schemas/__init__.py` (empty) and `backend/app/schemas/auth.py`**

```python
# backend/app/schemas/auth.py
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/__init__.py backend/app/services/auth_service.py backend/app/schemas/__init__.py backend/app/schemas/auth.py backend/tests/test_auth_service.py
git commit -m "Add auth service with password hashing and JWT handling"
```

---

## Task 4: Auth API routes (register/login) + current-user dependency

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/deps.py`
- Create: `backend/app/api/routes_auth.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_api_auth.py`

**Interfaces:**
- Consumes: `app.db.base.get_db`, `app.db.models.User`, `app.services.auth_service.*`, `app.schemas.auth.UserCreate`, `app.schemas.auth.Token`.
- Produces: `app.api.deps.get_current_user(token, db) -> User` (FastAPI dependency, raises HTTP 401 on invalid token).
- Produces: `POST /auth/register`, `POST /auth/login` routes mounted on `app.main.app`.

- [ ] **Step 1: Write the failing API integration test**

```python
# backend/tests/test_api_auth.py
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base, get_db


def _override_get_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


def test_register_and_login():
    response = client.post(
        "/auth/register", json={"email": "owner@example.com", "password": "secret123"}
    )
    assert response.status_code == 201

    response = client.post(
        "/auth/login", json={"email": "owner@example.com", "password": "secret123"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password_returns_401():
    client.post("/auth/register", json={"email": "a@example.com", "password": "right"})
    response = client.post("/auth/login", json={"email": "a@example.com", "password": "wrong"})
    assert response.status_code == 401
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_api_auth.py -v`
Expected: FAIL (404 — no `/auth/register` route exists yet)

- [ ] **Step 3: Create `backend/app/api/deps.py`**

```python
# backend/app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import User
from app.services.auth_service import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    try:
        email = decode_access_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
```

- [ ] **Step 4: Create `backend/app/api/routes_auth.py`**

```python
# backend/app/api/routes_auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import User
from app.schemas.auth import UserCreate, Token
from app.services.auth_service import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    return {"id": user.id, "email": user.email}


@router.post("/login", response_model=Token)
def login(payload: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = create_access_token(user.email)
    return Token(access_token=token)
```

- [ ] **Step 5: Wire the router into `backend/app/main.py`**

```python
# backend/app/main.py
from fastapi import FastAPI

from app.api.routes_auth import router as auth_router

app = FastAPI(title="Restaurant Analytics API")
app.include_router(auth_router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_api_auth.py -v`
Expected: PASS (2 tests)

- [ ] **Step 7: Run full backend test suite**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add backend/app/api backend/app/main.py backend/tests/test_api_auth.py
git commit -m "Add auth API routes with register/login and current-user dependency"
```

---

## Task 5: Branches API (CRUD-lite) and dashboard scaffolding dependency

**Files:**
- Create: `backend/app/schemas/branch.py`
- Create: `backend/app/api/routes_branches.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_api_branches.py`
- Modify: `backend/tests/test_api_auth.py` (extract shared override into conftest)
- Modify: `backend/tests/conftest.py`

**Interfaces:**
- Consumes: `app.api.deps.get_current_user`, `app.db.models.Branch`.
- Produces: `app.schemas.branch.BranchCreate(name: str, location: str | None)`, `app.schemas.branch.BranchOut(id: int, name: str, location: str | None)`.
- Produces: `POST /branches`, `GET /branches` (both require auth via `get_current_user`).
- Produces (for reuse by later tasks' tests): a `client` fixture in `conftest.py` that yields an authenticated `TestClient` with `Authorization` header already set, plus a `db_session`-backed override.

- [ ] **Step 1: Extend `backend/tests/conftest.py` with a shared API client fixture**

```python
# backend/tests/conftest.py (append to existing file from Task 2)
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import get_db


@pytest.fixture
def api_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def client(api_engine):
    TestingSessionLocal = sessionmaker(bind=api_engine)

    def _override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    client.post("/auth/register", json={"email": "owner@example.com", "password": "secret123"})
    response = client.post(
        "/auth/login", json={"email": "owner@example.com", "password": "secret123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

- [ ] **Step 2: Simplify `backend/tests/test_api_auth.py` to use the new `client` fixture**

```python
# backend/tests/test_api_auth.py
def test_register_and_login(client):
    response = client.post(
        "/auth/register", json={"email": "owner@example.com", "password": "secret123"}
    )
    assert response.status_code == 201

    response = client.post(
        "/auth/login", json={"email": "owner@example.com", "password": "secret123"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client):
    client.post("/auth/register", json={"email": "a@example.com", "password": "right"})
    response = client.post("/auth/login", json={"email": "a@example.com", "password": "wrong"})
    assert response.status_code == 401
```

- [ ] **Step 3: Run test to verify existing auth tests still pass**

Run: `cd backend && python -m pytest tests/test_api_auth.py -v`
Expected: PASS (2 tests)

- [ ] **Step 4: Write the failing test for branches**

```python
# backend/tests/test_api_branches.py
def test_create_and_list_branches(client, auth_headers):
    response = client.post(
        "/branches", json={"name": "Downtown", "location": "Main St"}, headers=auth_headers
    )
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "Downtown"

    response = client.get("/branches", headers=auth_headers)
    assert response.status_code == 200
    branches = response.json()
    assert len(branches) == 1
    assert branches[0]["name"] == "Downtown"


def test_branches_requires_auth(client):
    response = client.get("/branches")
    assert response.status_code == 401
```

- [ ] **Step 5: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_api_branches.py -v`
Expected: FAIL with 404 (no `/branches` route)

- [ ] **Step 6: Create `backend/app/schemas/branch.py`**

```python
# backend/app/schemas/branch.py
from pydantic import BaseModel


class BranchCreate(BaseModel):
    name: str
    location: str | None = None


class BranchOut(BaseModel):
    id: int
    name: str
    location: str | None = None

    model_config = {"from_attributes": True}
```

- [ ] **Step 7: Create `backend/app/api/routes_branches.py`**

```python
# backend/app/api/routes_branches.py
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
```

- [ ] **Step 8: Wire the router into `backend/app/main.py`**

```python
# backend/app/main.py
from fastapi import FastAPI

from app.api.routes_auth import router as auth_router
from app.api.routes_branches import router as branches_router

app = FastAPI(title="Restaurant Analytics API")
app.include_router(auth_router)
app.include_router(branches_router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 9: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_api_branches.py -v`
Expected: PASS (2 tests)

- [ ] **Step 10: Run full backend suite**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 11: Commit**

```bash
git add backend/app/schemas/branch.py backend/app/api/routes_branches.py backend/app/main.py backend/tests/conftest.py backend/tests/test_api_auth.py backend/tests/test_api_branches.py
git commit -m "Add branches API and shared authenticated test client fixtures"
```

---

## Task 6: CSV ingestion service (parsing, column mapping, validation)

**Files:**
- Create: `backend/app/schemas/upload.py`
- Create: `backend/app/services/csv_ingestion.py`
- Test: `backend/tests/test_csv_ingestion.py`

**Interfaces:**
- Consumes: `app.db.models.SalesTransaction`, `app.db.models.CsvUpload`, a SQLAlchemy `Session`.
- Produces: `app.schemas.upload.ColumnMapping(date_column: str, item_column: str, quantity_column: str, amount_column: str)`.
- Produces: `app.services.csv_ingestion.ParseResult` dataclass with fields `rows_imported: int`, `rows_rejected: int`, `errors: list[str]`.
- Produces: `parse_and_store_csv(db: Session, branch_id: int, filename: str, csv_text: str, mapping: ColumnMapping) -> ParseResult`. Validates: required columns present, max 50,000 rows, rejects rows with non-numeric quantity/amount or unparseable date (collects per-row error message, continues), writes valid rows as `SalesTransaction`, writes one `CsvUpload` record with `status="completed"` (or `"failed"` if zero rows imported).

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_csv_ingestion.py
from app.db.models import Branch, SalesTransaction, CsvUpload
from app.schemas.upload import ColumnMapping
from app.services.csv_ingestion import parse_and_store_csv

MAPPING = ColumnMapping(
    date_column="Date", item_column="Item", quantity_column="Qty", amount_column="Total"
)


def test_parse_valid_csv_stores_transactions(db_session):
    branch = Branch(name="Downtown", location="Main St")
    db_session.add(branch)
    db_session.commit()

    csv_text = (
        "Date,Item,Qty,Total\n"
        "2026-01-01 12:00,Burger,2,19.98\n"
        "2026-01-01 12:05,Fries,1,3.99\n"
    )

    result = parse_and_store_csv(db_session, branch.id, "sales.csv", csv_text, MAPPING)

    assert result.rows_imported == 2
    assert result.rows_rejected == 0
    transactions = db_session.query(SalesTransaction).all()
    assert len(transactions) == 2
    upload = db_session.query(CsvUpload).one()
    assert upload.status == "completed"
    assert upload.filename == "sales.csv"


def test_parse_csv_rejects_bad_rows_but_keeps_good_ones(db_session):
    branch = Branch(name="Uptown", location="2nd Ave")
    db_session.add(branch)
    db_session.commit()

    csv_text = (
        "Date,Item,Qty,Total\n"
        "2026-01-01 12:00,Burger,2,19.98\n"
        "not-a-date,Fries,1,3.99\n"
        "2026-01-01 12:10,Soda,abc,2.50\n"
    )

    result = parse_and_store_csv(db_session, branch.id, "sales.csv", csv_text, MAPPING)

    assert result.rows_imported == 1
    assert result.rows_rejected == 2
    assert len(result.errors) == 2


def test_parse_csv_missing_required_column_fails_fast(db_session):
    branch = Branch(name="Midtown", location="3rd Ave")
    db_session.add(branch)
    db_session.commit()

    csv_text = "Date,Item,Qty\n2026-01-01,Burger,2\n"

    result = parse_and_store_csv(db_session, branch.id, "sales.csv", csv_text, MAPPING)

    assert result.rows_imported == 0
    assert result.rows_rejected == 0
    assert any("Total" in e for e in result.errors)
    upload = db_session.query(CsvUpload).one()
    assert upload.status == "failed"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_csv_ingestion.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.schemas.upload'`

- [ ] **Step 3: Create `backend/app/schemas/upload.py`**

```python
# backend/app/schemas/upload.py
from pydantic import BaseModel


class ColumnMapping(BaseModel):
    date_column: str
    item_column: str
    quantity_column: str
    amount_column: str
```

- [ ] **Step 4: Create `backend/app/services/csv_ingestion.py`**

```python
# backend/app/services/csv_ingestion.py
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_csv_ingestion.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/upload.py backend/app/services/csv_ingestion.py backend/tests/test_csv_ingestion.py
git commit -m "Add CSV ingestion service with column mapping and row-level validation"
```

---

**Plan continues in a second file due to length** — see `docs/superpowers/plans/2026-06-25-restaurant-ai-dashboard-part2.md` for Tasks 7–16 (uploads API, synthetic data generator, forecasting, inventory, staffing, LLM insights, dashboard aggregation API, Docker Compose, frontend, README).
