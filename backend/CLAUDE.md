# Backend — CLAUDE.md

Backend-specific guidance. The repo root `CLAUDE.md` covers cross-cutting rules, the data model, and the prod ↔ test DB toggle — read it first.

## Code Organization

```
backend/app/
├── models/       # SQLModel ORM models (one file per aggregate); __init__.py is the registry alembic walks
├── schemas/      # Pydantic schemas: Create / Update / Read / ReadDetail / ListItem
├── crud/         # Async DB operations — one file per entity
├── routers/      # FastAPI routers (flat; no /v1 subdir) — registered in app/main.py
├── auth/         # JWT logic, dependencies, role guards
├── core/         # config.py (pydantic-settings), database.py (engines, sessions, resolve_prod_universe), audit.py
└── main.py       # App init, middleware, router registration
```

## Route Conventions

- `/api/v1/{entity}` — JSON API; Pydantic `ReadDetail` on single-resource, `ListItem` on collections
- All endpoints require auth; role checked per operation; universe_id always from query/body or path
- Vite dev server proxies `/api` → `http://localhost:8001`. If frontend can't reach backend, **check that uvicorn started on :8001, not :8000.**

## CRUD Conventions

Each entity module: `create_X`, `get_X`, `get_Xs` (cursor- or offset-paginated), `search_Xs` (trigram for indexed entities), `update_X`, `delete_X`. Deletes that need to break FK dependencies (e.g. `delete_member`) clean up join tables and null out FKs explicitly first.

## Migrations

Alembic config (`alembic.ini`) targets the prod DB by default. After autogenerate:

1. **Always trim drift.** Autogen flags pre-existing manual SQL (trgm indexes, ad-hoc constraints) as "removed" — these would actually drop production indexes. Inspect the generated file and keep only the intended changes.
2. **Apply to both DBs.** The CLI (`alembic upgrade head`) only hits prod. For the test DB, run programmatically:
   ```python
   from alembic.config import Config
   from alembic import command
   cfg = Config('alembic.ini')
   cfg.set_main_option('sqlalchemy.url', 'postgresql+asyncpg://postgres:<pass>@localhost:5432/squiidwiki_test')
   command.upgrade(cfg, 'head')
   ```
3. **Register new models in `app/models/__init__.py`** — `alembic/env.py` does `import app.models` and relies on that file to register everything with `SQLModel.metadata`.

## Backend pitfalls

- **Alembic autogenerate produces drift.** See Migrations above — trim before applying.
- **`asyncpg` does not support multi-statement `execute()` calls** — split into separate statements.
- **SQLModel JSON fields** require `sa_column=Column(JSONB)`; circular foreign keys need `use_alter=True` in Alembic.
- **Stats lag.** `member_stats` and `set_stats` are materialized views refreshed every 5 min via APScheduler + manual admin endpoint. List endpoints return live data; stat tiles can show stale counts briefly after edits.
