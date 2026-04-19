# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status

This is a **target-architecture document**. The repo is mid-migration from the current stack to the target described below. When code in the repo conflicts with the target, **the code is correct for now** — but all new work must follow the target patterns. See [Current state](#current-state-what-exists-today) for an honest inventory of what's actually here.

---

## Commands

### Current (works today)

```bash
# Install deps
pip install -r requirements.txt
npm install

# Run (auto-selects port starting at 8002)
python main.py

# Build Tailwind CSS
npm run css:build
npm run css:watch       # watch mode

# Migrations
alembic upgrade head

# Tests (in-memory SQLite — no Postgres needed)
python -m pytest tests/ -v
python -m pytest tests/test_business_rules.py::TestVitalStateValidation -v
```

### Target (post-migration)

```bash
# Infrastructure (Postgres 16 + Redis 7)
docker compose up -d

# Backend (from backend/)
alembic upgrade head
python -m app.seed                              # seed sample universe
uvicorn app.main:app --reload                   # → http://localhost:8000/docs

# Frontend (from frontend/)
npm run dev                                     # → http://localhost:5173

# Tests
cd backend && python -m pytest --cov

# Type-check frontend
cd frontend && npx tsc --noEmit
```

---

## Target architecture

### Multi-tenancy: the Universe

Every domain entity carries `universe_id`. A **Universe** is a fully isolated research namespace (e.g. "Metro Detroit", "Corsica"). All queries are universe-scoped — a single database hosts multiple wikis with no crossover. Per-universe roles live in `UserUniverseAccess` (ADMIN / EDITOR / VIEWER), separate from the global role (ADMIN / USER) on `User`.

### Target backend stack

FastAPI (async) + SQLModel + Alembic + asyncpg, `pydantic-settings` for config, `structlog` for JSON logging, APScheduler for materialized-view refresh.

### Target frontend stack

Vite + React 19 + TypeScript (strict, `erasableSyntaxOnly`), TanStack Router v2 (file-based) + TanStack Query v5, Radix UI + shadcn-style components + Tailwind CSS v4, Zustand for auth store and active-universe store. Replaces the current Jinja2 + Alpine templates.

### Infrastructure

PostgreSQL 16 (primary) + Redis 7 (stat cache), managed locally via Docker Compose.

### Entities (target schema)

**Universe** — `id`, `name`, `slug`, `created_by_id`

**Municipality** — geographic areas within a Universe; self-referential `parent_id` for sub-districts.

**Alliance** — `universe_id`, `name`, `status` (ACTIVE / EXTINCT / DORMANT), M2M territories → Municipality, M2M sets → Set.

**Set** — `universe_id`, `name`, `alias`, `status` (ACTIVE / EXTINCT), M2M territories, optional `alliance_id`, optional `founder_id`. Friends/enemies via `set_relationships` (see bilateral rules below).

**Member** — `universe_id`, `nickname` / `legal_name` / `nickname_unknown`, `aliases` JSONB, `biography`, `set_id` or `alliance_id`, `status` (FREE / LOCKED / DEAD / UNKNOWN / ESCAPEE / ABSCONDER), FuzzyDate fields for `dob` / `date_of_death` / `release_date`, `family` JSONB `{father, sons, brothers, cousins, uncles, nephews}`, `social_media` JSONB. Display rule: show `nickname` by default; if `nickname_unknown = true`, show `legal_name`.

**Incident** — `universe_id`, `type` (SHOOTING / MURDER), FuzzyDate `date`, optional `municipality_id`, `narrative` markdown, `verified`, `participants` → `IncidentParticipant[]`, M2M `sources` → Source.

**IncidentParticipant** (join table) — `incident_id`, `member_id`, `role` (SHOOTER / ASSISTED / BYSTANDER / VICTIM), `outcome` (KILLED / INJURED / UNHARMED / UNKNOWN). Role and outcome are orthogonal — do not conflate them.

**Source** — `universe_id`, `url`, `title`, `publication`, FuzzyDate `published_at`, `accessed_at`, `reliability` (HIGH / MEDIUM / LOW / UNVERIFIED), `archive_url`. M2M with Member and Incident.

**AuditLog** — immutable append-only: `user_id`, `entity_type`, `entity_id`, `action` (CREATE / UPDATE / DELETE), `diff_json` JSONB.

### FuzzyDate

Custom JSONB type for dates with variable precision:

```json
{ "year": 2019, "month": 3, "day": 15, "precision": "YMD", "approx": false, "circa_text": null }
```

`precision` is one of `Y | YM | YMD | UNKNOWN`. A companion generated `sortable_date` column stores the earliest-possible date for ordering (precision `Y` → Jan 1 of that year). **Never use a plain `DATE` or `datetime` column for domain dates.**

Display examples: `{precision: "Y", approx: true}` → `"circa 2018"` · `{precision: "YM"}` → `"Mar 2019"` · `{precision: "UNKNOWN"}` → `"unknown"`

### Auth (target)

- Password hashing: **argon2-cffi** (not bcrypt)
- Tokens: **access + refresh pair** (not a single JWT)
- Global role on `User`; per-universe role in `UserUniverseAccess`

### Caching & stats (target)

- **Redis 7** backs the stat cache.
- **Materialized views** `member_stats` and `set_stats` JOIN incidents → incident_participants and are refreshed every 5 minutes via APScheduler. An admin endpoint exists for manual refresh.
- Do **not** compute aggregated stats live on the request path.

### Bilateral set relationships

Enemy/friend pairs stored once as `(set_a_id, set_b_id)` with `CHECK set_a_id < set_b_id`. A Postgres trigger enforces insert ordering. Application code always normalizes to `(min_id, max_id)` before insert. A `relationship_type` column (FRIEND / ENEMY) lives on the join row.

---

## Current state (what exists today)

| Area | Current |
|---|---|
| Backend ORM | SQLAlchemy 2.0 (not SQLModel) |
| Frontend | Jinja2 templates + Alpine.js 3.13 + Tailwind (Webpack build) |
| Auth | bcrypt 12 rounds, single JWT cookie |
| Multi-tenancy | None — no `universe_id` anywhere |
| Redis / Docker | Not present |
| Materialized views | Not present — stats computed live |
| AuditLog / Sources | Not present |
| Date fields | Plain `datetime` columns |
| Events model | Separate murders/shootings/assists tables with dict-of-lists participants |
| App mount | FastAPI dual-mount: HTML at `/`, JSON API at `/api` |
| Entry points | `main.py` → uvicorn, `backend/server.py` → app factory |
| DB init / seed | `backend/database/db_init.py` auto-creates tables and seeds admin user on startup |
| Tests | pytest + in-memory SQLite, 35 tests in `tests/test_business_rules.py` |

---

## Migration principles

New work in this repo must follow these rules regardless of what the surrounding code does:

1. **New entities** include `universe_id` and are always queried universe-scoped.
2. **New date columns** use FuzzyDate JSONB + `sortable_date`. Never `datetime`.
3. **New event-like entities** use the `Incident` + `IncidentParticipant` pattern — orthogonal role/outcome, not dict-of-lists.
4. **New auth code** uses argon2 + access/refresh tokens. Do not add new bcrypt call sites.
5. **New frontend work** goes in the React/Vite tree. Extend existing Jinja2 templates only for bug fixes.
6. **Stats** go through materialized views / Redis cache, not live JOINs on the request path.
7. **Bilateral relationships** normalize to `(min_id, max_id)` before insert; Postgres trigger enforces the constraint.
8. **Soft deletes only** — `deleted_at` timestamp, never hard deletes.
9. **All writes** emit an `AuditLog` entry once that table exists.

---

## Domain business rules

Enforced at the service layer via `backend/validators/business_rules.py`. These are domain rules independent of the tech stack — they survive migration unchanged:

1. Deceased members cannot participate in events after their death date.
2. Incarcerated members may only participate in facility-type events.
3. Events cannot predate set founding; members cannot join before their birth date.
4. Warn when forming an alliance with a rival-aligned set.
5. All deletes are soft (`deleted_at`).

Test coverage: `tests/test_business_rules.py` (35 tests, SQLite in-memory).
