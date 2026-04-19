# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SquiidWiki is a gang research database wiki that tracks social networks, incidents, and relationships in metropolitan areas. It uses a **Universe** concept where each city/metro area is an isolated namespace. See `README.md` for the full schema reference.

## Tech Stack

**Backend (`backend/`)**
- FastAPI (async) + Pydantic 2 — API layer
- SQLModel — ORM (Pydantic + SQLAlchemy 2.0 fusion; models defined once for DB + API validation)
- Alembic — migrations
- asyncpg — async Postgres driver
- Redis — computed stat caching (kill counts, shooting stats)
- argon2 — password hashing; JWT access tokens + rotating refresh tokens

**Frontend (`frontend/`)**
- Vite + React 18 + TypeScript (strict)
- TanStack Router v2 (file-based, fully typed routes)
- TanStack Query v5 (data fetching, caching, optimistic updates)
- shadcn/ui + Tailwind CSS (dark-themed)
- Zustand (auth state, active universe)
- vis.js / react-flow — network graph visualizations

**Infrastructure**
- PostgreSQL 16 — primary database
- Redis 7 — stat cache + (future) task queue
- docker-compose for local dev

**Auth:** Multi-user with roles (Admin / Editor / Viewer); per-universe permissions via `user_universe_access` table; audit log on all writes.

## Development Commands

```bash
# Backend
cd backend
uv run alembic upgrade head          # apply migrations
uv run python -m app.seed            # seed sample data
uv run uvicorn app.main:app --reload # start dev server → http://localhost:8000/docs

# Generate migration after model change
uv run alembic revision --autogenerate -m "Description"

# Tests
uv run pytest --cov

# Frontend
cd frontend
pnpm dev    # → http://localhost:5173
pnpm build
pnpm test
pnpm tsc --noEmit   # type check
```

## Architecture

### Data Model Hierarchy

```
Universe → Municipality
         → Sets / Alliances → Members → Incidents → Sources
```

- **Universe** — top-level isolation container; every entity carries `universe_id`
- **Municipality** — geographic entity (cities, districts) within a Universe
- **Sets** — gang crews; allies/enemies are bilateral (normalized `set_a_id < set_b_id`)
- **Alliances** — organizations of Sets
- **Members** — nickname-first identity; `display_name` property always used (nickname default, legal name when `nickname_unknown=True`)
- **Incidents** — events with a typed participant table (`incident_participants`: member_id + role + outcome); no shooter/killer dict
- **Sources** — citations with reliability rating; M2M with Members and Incidents

### Key Design Decisions

- **FuzzyDate** — JSONB `{year, month?, day?, precision: Y|YM|YMD|UNKNOWN, approx: bool}`. Custom SQLAlchemy TypeDecorator. Never use a plain `DATE` column for event/biography dates.
- **Bilateral relationships** — stored once as `(set_a_id < set_b_id)` with a Postgres trigger enforcing the ordering. Application CRUD always normalizes pairs before insert.
- **Incident participants** — `incident_participants` join table with `role ∈ {SHOOTER, ASSISTED, BYSTANDER, VICTIM}` and `outcome ∈ {KILLED, INJURED, UNHARMED, UNKNOWN}`. Do not use dict-of-lists.
- **Computed stats** — materialized views `member_stats` and `set_stats`; refreshed every 5 min via APScheduler + manual admin endpoint.
- **Universe scoping** — all CRUD functions take `universe_id`; no cross-universe queries from API handlers.

### Code Organization

```
backend/app/
├── models/       # SQLModel ORM models (one file per aggregate)
├── schemas/      # Pydantic schemas: Create / Update / Read / ReadDetail / ListItem
├── crud/         # Async DB operations — one file per entity
├── routers/v1/   # FastAPI routers (/api/v1/{entity})
├── auth/         # JWT logic, dependencies, role guards
├── config.py     # pydantic-settings (env loading)
├── database.py   # Async engine, session dependency
└── main.py       # App init, middleware, router registration

frontend/src/
├── features/     # One folder per entity (set, member, incident, ...)
├── components/   # Shared: FuzzyDate, MemberIdentity, UniverseSwitcher, ...
├── router.tsx    # TanStack Router root
└── stores/       # Zustand stores (auth, universe)
```

### Route Conventions

- `/api/v1/{entity}` — JSON API; Pydantic `ReadDetail` on single-resource, `ListItem` on collections
- All endpoints require auth; role checked per operation; universe_id always from auth context or path

### CRUD Conventions

Each entity module: `create_X`, `get_X`, `get_Xs` (cursor-paginated), `search_Xs` (trigram), `update_X`, `delete_X`.

### Enums

- Member status: `FREE`, `LOCKED`, `DEAD`, `UNKNOWN`, `ESCAPEE`, `ABSCONDER`
- Set/Alliance status: `ACTIVE`, `EXTINCT`, `DORMANT`
- Source reliability: `HIGH`, `MEDIUM`, `LOW`, `UNVERIFIED`
- Incident participant role: `SHOOTER`, `ASSISTED`, `BYSTANDER`, `VICTIM`
- Incident participant outcome: `KILLED`, `INJURED`, `UNHARMED`, `UNKNOWN`
