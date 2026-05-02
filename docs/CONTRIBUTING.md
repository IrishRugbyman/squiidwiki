# SquiidWiki — Contributing & Dev Setup

## Prerequisites

- Python via miniconda: `C:\Users\irish\miniconda3\envs\squiidwiki\python.exe`
- Node.js 20+ and npm
- Docker Desktop (for Postgres + Redis)

## Quick Start

```bash
# 1. Start infrastructure
docker compose up -d

# 2. Backend setup
PY="C:\Users\irish\miniconda3\envs\squiidwiki\python.exe"
cd backend
$PY -m pip install -r requirements-dev.txt
$PY -m alembic upgrade head
$PY -m app.seed                    # seed sample data (Metro Detroit universe)
$PY -m uvicorn app.main:app --reload  # → http://localhost:8000/docs

# 3. Frontend setup
cd frontend
npm install
npm run dev                        # → http://localhost:5173
```

## Environment Variables

Copy `.env.example` to `.env` and fill in the values. The backend reads `.env` from the repo root via `pydantic-settings`.

Required:
- `DATABASE_URL` — asyncpg DSN (`postgresql+asyncpg://...`)
- `SECRET_KEY` — random 32-byte hex (`python -c "import secrets; print(secrets.token_hex(32))"`)

Defaults (override in `.env` if needed):
- `REDIS_URL` → `redis://localhost:6379`
- `ACCESS_TOKEN_EXPIRE_MINUTES` → `15`
- `REFRESH_TOKEN_EXPIRE_DAYS` → `30`
- `CORS_ORIGINS` → `["http://localhost:5173"]`

## Running Tests

```bash
cd backend

# Full suite
$PY -m pytest --cov

# Single file
$PY -m pytest tests/test_members.py -v

# Single test
$PY -m pytest tests/test_incidents.py::test_create_incident_with_participants -v -s
```

Tests run against a separate `squiidwiki_test` database (configured in `tests/conftest.py`). Create it with:
```bash
docker exec squiidwiki-db-1 psql -U postgres -c "CREATE DATABASE squiidwiki_test;"
```

The test suite uses a **session-scoped** async DB session shared across all tests. Tests must not leave the session in an aborted state — stats functions that query materialized views must call `session.rollback()` in their exception handlers (not just `pass`).

## Database Migrations

```bash
cd backend

# Apply all pending migrations
$PY -m alembic upgrade head

# Generate a new migration after model changes
$PY -m alembic revision --autogenerate -m "Add foo column to bar"

# View migration history
$PY -m alembic history

# Downgrade one step
$PY -m alembic downgrade -1
```

**Rule:** every schema change must have an Alembic migration. Never modify `alembic/versions/` files by hand after they've been applied to any environment.

## Backups

```bash
# Create a backup
docker exec squiidwiki-db-1 pg_dump -U postgres squiidwiki_db \
  | gzip > backups/squiidwiki_$(date +%Y%m%d_%H%M%S).sql.gz

# Restore
gunzip -c backups/squiidwiki_TIMESTAMP.sql.gz \
  | docker exec -i squiidwiki-db-1 psql -U postgres squiidwiki_db
```

Store backup files outside Docker volumes. The `audit_log` table must be included in all backups.

## Code Style

**Backend:**
```bash
$PY -m ruff check app/      # lint
$PY -m ruff format app/     # format
$PY -m mypy app/            # type check
```

**Frontend:**
```bash
npm run lint                # eslint
npx tsc --noEmit            # type check
npm run build               # production build (catches errors)
```

Pre-commit hooks enforce both. Run `pre-commit install` once after cloning.

## Adding a New Entity

1. **Model** — add `backend/app/models/{entity}.py` (SQLModel table class)
2. **Schema** — add `backend/app/schemas/{entity}.py` (`Create`, `Update`, `Read`, `ReadDetail`, `ListItem`)
3. **CRUD** — add `backend/app/crud/{entity}.py` (async CRUD functions, cursor or offset pagination)
4. **Router** — add `backend/app/routers/{entity}.py`, register in `main.py`
5. **Migration** — `alembic revision --autogenerate -m "Add {entity} table"`
6. **Tests** — add `backend/tests/test_{entity}.py` covering CRUD + auth + 404 cases
7. **Frontend** — add `frontend/src/routes/_app.{entity}.tsx` (list) and `_app.{entity}.$id.tsx` (detail), add queries to `lib/queries.ts`, add nav entry in `_app.tsx`

## Monitoring Stack

```bash
# Start Prometheus + Grafana alongside the app
docker compose up -d prometheus grafana

# Access
# Prometheus:  http://localhost:9090
# Grafana:     http://localhost:3000  (admin / admin)
# Metrics:     http://localhost:8000/metrics
```

The Grafana Prometheus datasource is auto-provisioned from `infra/grafana/provisioning/datasources/prometheus.yml`.
