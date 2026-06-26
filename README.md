# AI-Powered Restaurant Analytics Dashboard

Multi-branch restaurant analytics platform with revenue forecasting (Prophet), inventory and staffing intelligence, and LLM-generated weekly insights (DeepSeek via OpenRouter). Built as an AI engineering course project.

## Stack

- **Backend:** FastAPI, SQLAlchemy 2.0, Prophet, JWT auth (python-jose + passlib/argon2), PostgreSQL (SQLite for local/demo)
- **Frontend:** Next.js 16 (App Router, TypeScript), Tailwind CSS 4, Recharts
- **LLM:** DeepSeek `deepseek-chat-v3-0324:free` via OpenRouter, with a deterministic rule-based fallback when no API key is set or the API call fails
- **Tests:** pytest (backend) — 47 tests covering auth, branches, uploads, forecasting, inventory, staffing, insights, dashboard, and security headers

## Features

- JWT-based register/login, multi-branch management, CSV sales upload (`Date, Item, Qty, Total` columns)
- 14-day revenue forecasting with confidence bounds (Prophet) and accuracy metrics (MAE%, RMSE%) against held-out history
- Inventory intelligence: stockout-risk and overstock alerts derived from sales-consumption analysis
- Shift staffing recommendations per time-of-day, with a weekend demand buffer
- Weekly AI-generated insights (summary, key risks, recommendations), cached for one hour per branch to respect rate limits
- Dashboard KPI summary (7-day revenue, order count, average order value) and peak-hour-by-day-of-week heatmap, both as live aggregation endpoints
- Frontend dashboard renders live backend data wherever it exists, and falls back to clearly-labelled showcase data only when a branch has no sales history yet

## API Endpoints

All routes are served from the FastAPI app (`backend/app/main.py`); interactive docs at `/docs`.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | API info (name, links to `/docs` and `/health`) |
| GET | `/health` | Health check |
| POST | `/register` | Create a user account |
| POST | `/login` | Obtain a JWT access token |
| GET | `/branches` | List branches |
| POST | `/branches` | Create a branch |
| POST | `/branches/{branch_id}/uploads` | Upload a CSV of sales transactions |
| POST | `/branches/{branch_id}/forecasts` | Generate a 14-day Prophet revenue forecast |
| GET | `/branches/{branch_id}/forecasts/accuracy` | Forecast accuracy (MAE%, RMSE%) |
| POST | `/branches/{branch_id}/inventory-items` | Register an inventory item |
| GET | `/branches/{branch_id}/inventory-items` | List inventory items |
| GET | `/branches/{branch_id}/inventory-alerts` | Stockout/overstock alerts |
| GET | `/branches/{branch_id}/staffing` | Shift staffing recommendations |
| POST | `/branches/{branch_id}/insights/weekly-summary` | Generate (or reuse cached) weekly AI insight |
| GET | `/branches/{branch_id}/dashboard/kpis` | KPI summary for a date range |
| GET | `/branches/{branch_id}/dashboard/heatmap` | Revenue heatmap by day-of-week/hour |

## Running locally

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL, or use sqlite:///./demo.db for a quick local run
python -m uvicorn app.main:app --reload --port 8000
```

Visit `http://127.0.0.1:8000/docs` for interactive Swagger UI, or `http://127.0.0.1:8000/` for a basic API info response.

Run the test suite:

```bash
cd backend
python -m pytest tests/ -v
```

Expected: `47 passed`.

### 2. (Optional) Generate synthetic demo data

Generates one year of realistic transaction history (with weekend/holiday demand multipliers) for three demo branches — useful for exercising forecasting, inventory, and staffing features without manual data entry:

```bash
cd backend
python scripts/generate_synthetic_data.py
```

Writes `Downtown.csv`, `Uptown.csv`, and `Riverside.csv` to `backend/scripts/output/` (git-ignored). Create a branch via `/branches`, then upload each CSV via `/branches/{branch_id}/uploads`.

### 3. Frontend

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000" > .env.local
npm run dev
```

Visit `http://localhost:3000` — it redirects to `/login` (demo credentials pre-filled) or `/dashboard` if already authenticated.

### 4. Docker Compose (Postgres + backend)

```bash
docker compose up --build
```

Starts a Postgres 16 container and the FastAPI backend on port 8000 (reads env vars from `backend/.env`). Run the frontend separately with `npm run dev`.

## Enabling live DeepSeek AI insights

Without an OpenRouter API key, the "Generate Weekly Summary" feature still works end-to-end but returns a deterministic rule-based summary instead of an LLM-generated one. To enable the real model:

1. Create a free account at [openrouter.ai](https://openrouter.ai) and generate an API key.
2. In `backend/.env`, set:
   ```
   OPENROUTER_API_KEY=sk-or-v1-...
   OPENROUTER_MODEL=deepseek/deepseek-chat-v3-0324:free
   ```
3. Restart the backend. The next "Generate Weekly Summary" click calls DeepSeek; any API error (rate limit, network) still falls back to the rule-based summary automatically — the feature never breaks for the user.

## Deploying for free

- **Backend + database:** [Render.com](https://render.com) — Docker-based Web Service from `backend/` plus a managed free PostgreSQL instance. Set `DATABASE_URL`, `JWT_SECRET`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, and `FRONTEND_ORIGIN` (your Vercel URL) as environment variables on the service.
- **Frontend:** [Vercel](https://vercel.com) — import the repo, set the root directory to `frontend/`, and set `NEXT_PUBLIC_API_BASE` to your Render backend URL.
- Keep `FRONTEND_ORIGIN` (backend) and `NEXT_PUBLIC_API_BASE` (frontend) in sync any time either deployed URL changes, or CORS/API calls will fail.

## Project structure

```
backend/
  app/
    api/         # FastAPI route modules (auth, branches, uploads, forecasts, inventory, staffing, insights, dashboard)
    services/     # forecasting (Prophet), inventory, staffing, insight, openrouter client, csv ingestion, auth
    schemas/      # Pydantic request/response models
    db/           # SQLAlchemy models and session setup
    config.py     # pydantic-settings env configuration
    main.py       # FastAPI app, middleware, router registration
  scripts/
    generate_synthetic_data.py   # one-year synthetic sales CSV generator
  tests/          # 47 pytest tests across services, API routes, and security headers
frontend/
  src/
    app/
      login/       # login page
      dashboard/   # main analytics dashboard (single scrollable page, no tabs)
    lib/api.ts     # typed API client (fetch wrappers, JWT token storage)
    components/    # shared UI components (e.g. AnimatedCounter)
```
