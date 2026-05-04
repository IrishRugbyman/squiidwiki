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
2. **Apply to both DBs.** The CLI (`alembic upgrade head`) only hits prod. `env.py` reads `settings.database_url_prod`, so override it via env var to migrate the test DB:
   ```bash
   DATABASE_URL_PROD='<test-db-url-from-.env>' .venv/bin/python -m alembic upgrade head
   ```
   Do **not** try `Config.set_main_option('sqlalchemy.url', ...)` — the `%`-encoded password in our URLs trips configparser interpolation. Skip silently if `squiidwiki_test` doesn't exist locally.
3. **Register new models in `app/models/__init__.py`** — `alembic/env.py` does `import app.models` and relies on that file to register everything with `SQLModel.metadata`.

4. **Pick a fresh random revision ID** — `python -c "import secrets; print(secrets.token_hex(6))"`. The existing IDs in `alembic/versions/` follow obvious sequential hex patterns and any "next in sequence" guess has a real chance of colliding (`alembic` will refuse with `CycleDetected`).

## Audit log & death sync

- All write operations on tracked entities are captured by SQLAlchemy event listeners (see `app/core/audit.py`). The `member` listener captures changes for free, including those triggered by `_sync_killed_participants`.
- **Incident-driven death sync** is implemented in `app/crud/incident.py`: `_sync_killed_participants` runs after `_sync_participants` on both create and update. For semantics (when it fires, what it does, irreversibility, FK behavior on incident delete), see the root `CLAUDE.md` → "Incident-driven death sync".

## Media / SQLModel quirks

- **`media.kind` is `VARCHAR`, not a Postgres ENUM.** The SQLModel field must use `sa_column=Column(String, ...)` — do **not** let SQLModel infer the type from the `MediaKind` Python enum, or asyncpg will cast as `::mediakind` and blow up on INSERT.
- **`attach_primary_photos()`** sets transient attributes (`primary_photo_url`, `primary_photo_thumb_url`) on `Member` ORM instances. Pydantic v2 rejects unknown field assignment via `__setattr__`, so use `object.__setattr__(m, 'primary_photo_url', url)`.

## Backend pitfalls

- **Alembic autogenerate produces drift.** See Migrations above — trim before applying.
- **`asyncpg` does not support multi-statement `execute()` calls** — split into separate statements.
- **SQLModel JSON fields** require `sa_column=Column(JSONB)`; circular foreign keys need `use_alter=True` in Alembic.
- **Stats lag.** `member_stats` and `set_stats` are materialized views refreshed every 5 min via APScheduler + manual admin endpoint — see root `CLAUDE.md` "Computed stats".
