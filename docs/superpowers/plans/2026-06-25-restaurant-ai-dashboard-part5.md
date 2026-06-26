# AI-Powered Restaurant Analytics Dashboard Implementation Plan — Part 5 (Tasks 17-18)

> Continuation of Parts 1-4. Same Global Constraints apply.

---

## Task 17: CORS + security headers middleware

**Files:**
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_security_headers.py`

**Interfaces:**
- Produces: `app.main.app` configured with `CORSMiddleware` (allowing `http://localhost:3000` and an env-configurable `FRONTEND_ORIGIN`), and a custom middleware that adds `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` to every response.
- Modify: `app.config.Settings` — add `frontend_origin: str = "http://localhost:3000"`.

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_security_headers.py
def test_health_response_has_security_headers(client):
    response = client.get("/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_security_headers.py -v`
Expected: FAIL — headers missing

- [ ] **Step 3: Add `frontend_origin` to `backend/app/config.py`**

```python
# backend/app/config.py — add field to Settings
    frontend_origin: str = "http://localhost:3000"
```

- [ ] **Step 4: Update `backend/app/main.py` with CORS and security headers middleware**

```python
# backend/app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.routes_auth import router as auth_router
from app.api.routes_branches import router as branches_router
from app.api.routes_uploads import router as uploads_router
from app.api.routes_forecasts import router as forecasts_router
from app.api.routes_inventory import router as inventory_router
from app.api.routes_staffing import router as staffing_router
from app.api.routes_insights import router as insights_router
from app.api.routes_dashboard import router as dashboard_router

settings = get_settings()

app = FastAPI(title="Restaurant Analytics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


app.include_router(auth_router)
app.include_router(branches_router)
app.include_router(uploads_router)
app.include_router(forecasts_router)
app.include_router(inventory_router)
app.include_router(staffing_router)
app.include_router(insights_router)
app.include_router(dashboard_router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_security_headers.py -v`
Expected: PASS (1 test)

- [ ] **Step 6: Run full backend suite**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/main.py backend/app/config.py backend/tests/test_security_headers.py
git commit -m "Add CORS configuration and security response headers"
```

---

## Task 18: Docker Compose for local dev (Postgres + backend)

**Files:**
- Create: `backend/Dockerfile`
- Create: `docker-compose.yml`
- Test: manual verification (no automated test — infra task)

**Interfaces:**
- Produces: `docker-compose.yml` at repo root with services `db` (postgres:16, exposes 5432, persistent volume, env `POSTGRES_USER=restaurant`, `POSTGRES_PASSWORD=restaurant`, `POSTGRES_DB=restaurant_db`) and `backend` (build from `backend/Dockerfile`, exposes 8000, depends on `db`, reads `backend/.env`).
- Produces: `backend/Dockerfile` — `python:3.11-slim` base, installs `requirements.txt`, copies `app/` and `scripts/`, runs `uvicorn app.main:app --host 0.0.0.0 --port 8000`.

- [ ] **Step 1: Create `backend/Dockerfile`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY scripts/ ./scripts/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Create `docker-compose.yml` at repo root**

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: restaurant
      POSTGRES_PASSWORD: restaurant
      POSTGRES_DB: restaurant_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U restaurant"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - backend/.env
    depends_on:
      db:
        condition: service_healthy

volumes:
  postgres_data:
```

- [ ] **Step 3: Update `backend/.env.example` to point at the compose db service when run via Docker**

```
# backend/.env.example
DATABASE_URL=postgresql://restaurant:restaurant@db:5432/restaurant_db
JWT_SECRET=change-me-to-a-random-secret
OPENROUTER_API_KEY=
OPENROUTER_MODEL=deepseek/deepseek-chat-v3-0324:free
FRONTEND_ORIGIN=http://localhost:3000
```

Note: when running the backend directly on the host (not via Docker) for local `pytest`/`uvicorn` development, use `localhost` instead of `db` in a local (uncommitted) `backend/.env` copy.

- [ ] **Step 4: Manually verify the stack boots**

Run: `docker compose up --build -d`
Expected: Both `db` and `backend` containers report healthy/running. Then run:
Run: `curl http://localhost:8000/health`
Expected: `{"status":"ok"}`
Then: `docker compose down`

- [ ] **Step 5: Commit**

```bash
git add backend/Dockerfile docker-compose.yml backend/.env.example
git commit -m "Add Docker Compose setup for Postgres and backend services"
```

---

**Continued in Part 6** (`docs/superpowers/plans/2026-06-25-restaurant-ai-dashboard-part6.md`): Tasks 19-26 — Next.js frontend scaffolding, API client, auth pages, CSV upload wizard, dashboard components (KPI cards, heatmap, forecast chart, inventory panel, staffing panel, insight panel), frontend Dockerfile, and README.
