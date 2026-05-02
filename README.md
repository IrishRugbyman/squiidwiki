# SquiidWiki

A multi-tenant gang research wiki. Each isolated network of people lives inside a **Universe**. This document is the canonical schema and architecture reference.

---

## Build Status

| Phase | Status | Notes |
|---|---|---|
| 0 — Schema Design | ✅ Done | This README |
| 1 — Foundation & Tooling | ✅ Done | FastAPI + Vite + Docker + pre-commit |
| 2 — Database & Migrations | ✅ Done | SQLModel models, Alembic, FuzzyDate, bilateral trigger, seed |
| 3 — Auth & Authorization | ✅ Done | argon2, JWT access/refresh, per-universe roles |
| 4 — Backend API (vertical slices) | ✅ Done | All 7 entities, pg_trgm search, materialized view stats |
| 5 — Frontend Foundation | ✅ Done | shadcn-style design system, sidebar layout, Universe switcher |
| 6 — Frontend Screens | ✅ Done | List + detail + create for all 7 entities |
| 7 — Production Hardening | ⬜ Pending | |
| 8 — Documentation | ⬜ Pending | |

---

## Dev Quick-Start

**Python env:** `C:\Users\irish\miniconda3\envs\squiidwiki\python.exe`

```bash
# Infrastructure (Postgres + Redis)
docker compose up -d

# Backend (from backend/)
PY="C:\Users\irish\miniconda3\envs\squiidwiki\python.exe"
$PY -m alembic upgrade head   # apply migrations
$PY -m app.seed               # seed sample data (Metro Detroit universe)
$PY -m uvicorn app.main:app --reload   # → http://localhost:8000/docs

# Frontend (from frontend/)
npm run dev    # → http://localhost:5173

# Tests
cd backend && $PY -m pytest --cov

# Type-check frontend
cd frontend && npx tsc --noEmit
```

**Default admin credentials (after seed):** check `backend/app/seed.py`

---

---

## Architecture: The "Universe" Concept

A **Universe** is a fully isolated research namespace (e.g. "Metro Detroit", "Corsica"). Every core entity carries a `universe_id`. A single database can serve multiple completely separate wikis with no crossover.

---

## Schema

### Universe

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| name | str | e.g. "Metro Detroit" |
| slug | str | URL-safe, unique |
| description | str | optional |
| created_at | datetime | auto |
| created_by_id | UUID → User | FK |

---

### Municipality

Geographical areas within a Universe (cities, districts, townships).

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| universe_id | UUID → Universe | FK |
| name | str | e.g. "Ecorse" |
| parent_id | UUID → Municipality | nullable — for sub-districts |

---

### Alliances

Larger organizations that contain Sets (and optionally direct members).

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| universe_id | UUID → Universe | FK |
| name | str | |
| description | str | optional |
| status | AllianceStatusEnum | ACTIVE / EXTINCT / DORMANT |
| founded_at | FuzzyDate | optional |
| territories | UUID[] → Municipality | M2M |
| sets | UUID[] → Set | M2M |

---

### Sets

Gang crews / organizations.

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| universe_id | UUID → Universe | FK |
| name | str | |
| alias | str | optional |
| bio | str | optional |
| status | SetStatusEnum | ACTIVE / EXTINCT |
| territories | UUID[] → Municipality | M2M — a set can span multiple areas |
| alliance_id | UUID → Alliance | optional FK |
| founder_id | UUID → Member | optional FK |
| friends | Set[] | M2M via `set_relationships` — cannot overlap with enemies |
| enemies | Set[] | M2M via `set_relationships` — bilateral: if A↔B, then B↔A |

#### Bilateral relationship storage

Enemy/friend pairs stored once as `(set_a_id, set_b_id)` with a CHECK constraint `set_a_id < set_b_id` and a Postgres trigger enforcing insert ordering. A separate `relationship_type` column (`FRIEND` / `ENEMY`) on the join row. Application CRUD always normalizes pairs (min, max) before insert.

#### Stats (computed dynamically via materialized views)

- total shootings by all members
- total assists
- total kills
- number of dead members

---

### Members

Individual people tracked in the wiki.

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| universe_id | UUID → Universe | FK |
| nickname | str | optional if `legal_name` set |
| legal_name | str | optional if `nickname` set |
| nickname_unknown | bool | if true, use `legal_name` as display name |
| aliases | JSONB | list of alternative street names |
| biography | str | default "" |
| photo_url | str | optional, placeholder for V1 |
| set_id | UUID → Set | optional if `alliance_id` set |
| alliance_id | UUID → Alliance | optional if `set_id` set |
| status | MemberStatusEnum | see below |
| dob | FuzzyDate | optional |
| date_of_death | FuzzyDate | optional — only when status = DEAD |
| release_date | FuzzyDate \| "LIFE" | optional — only when status = LOCKED or ESCAPEE |
| family | JSONB | `{father?: id, sons?: [id], brothers?: [id], cousins?: [id], uncles?: [id], nephews?: [id]}` |
| social_media | JSONB | `{platform: handle}` dict |

**`display_name` rule:** show `nickname` by default; if `nickname_unknown = true`, show `legal_name` instead.

#### Stats (computed dynamically via materialized views)

- number of shootings (as shooter)
- number of assists
- number of kills
- times been shot (as victim, survived)
- current age, or age at death

---

### Incidents

Events — shootings, murders — with structured participants.

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| universe_id | UUID → Universe | FK |
| type | IncidentTypeEnum | SHOOTING / MURDER |
| date | FuzzyDate | |
| municipality_id | UUID → Municipality | optional FK |
| location_text | str | optional free-text location detail |
| narrative | str | optional markdown — context / description |
| verified | bool | default false |
| verified_by_id | UUID → User | optional FK |
| participants | IncidentParticipant[] | see below |
| sources | Source[] | M2M |

#### IncidentParticipant (join table)

Replaces the old dict-of-lists approach. Role and outcome are orthogonal fields.

| Field | Type | Notes |
|---|---|---|
| incident_id | UUID → Incident | PK part |
| member_id | UUID → Member | PK part |
| role | ParticipantRoleEnum | SHOOTER / ASSISTED / BYSTANDER / VICTIM |
| outcome | ParticipantOutcomeEnum | KILLED / INJURED / UNHARMED / UNKNOWN |
| notes | str | optional |

---

### Sources

Research citations. Many-to-many with Members and Incidents.

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| universe_id | UUID → Universe | FK |
| url | str | |
| title | str | |
| publication | str | optional — newspaper, channel, etc. |
| published_at | FuzzyDate | optional |
| accessed_at | date | when the URL was accessed |
| reliability | SourceReliabilityEnum | HIGH / MEDIUM / LOW / UNVERIFIED |
| notes | str | optional |
| archive_url | str | optional — Wayback Machine link |

---

### Auth Tables

#### User

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| email | str | unique |
| hashed_password | str | argon2 |
| global_role | GlobalRoleEnum | ADMIN / USER |
| created_at | datetime | auto |
| last_login_at | datetime | nullable |

#### UserUniverseAccess

Per-universe role assignment. A user can be Editor in one universe and Viewer in another.

| Field | Type | Notes |
|---|---|---|
| user_id | UUID → User | PK part |
| universe_id | UUID → Universe | PK part |
| role | UniverseRoleEnum | ADMIN / EDITOR / VIEWER |

#### AuditLog

Immutable append-only record of all writes.

| Field | Type | Notes |
|---|---|---|
| id | UUID | PK |
| user_id | UUID → User | FK |
| entity_type | str | "member", "set", etc. |
| entity_id | UUID | |
| action | AuditActionEnum | CREATE / UPDATE / DELETE |
| diff_json | JSONB | before/after diff |
| created_at | datetime | auto |

---

## Enums

### IncidentTypeEnum
- `SHOOTING`
- `MURDER`

### ParticipantRoleEnum
- `SHOOTER`
- `ASSISTED`
- `BYSTANDER`
- `VICTIM`

### ParticipantOutcomeEnum
- `KILLED`
- `INJURED`
- `UNHARMED`
- `UNKNOWN`

### MemberStatusEnum
- `FREE` — alive and free
- `LOCKED` — alive and incarcerated
- `DEAD`
- `UNKNOWN`
- `ESCAPEE` — escaped from a correctional facility
- `ABSCONDER` — paroled but evading supervision

### SetStatusEnum
- `ACTIVE`
- `EXTINCT`

### AllianceStatusEnum
- `ACTIVE`
- `EXTINCT`
- `DORMANT`

### SourceReliabilityEnum
- `HIGH`
- `MEDIUM`
- `LOW`
- `UNVERIFIED`

### GlobalRoleEnum
- `ADMIN`
- `USER`

### UniverseRoleEnum
- `ADMIN`
- `EDITOR`
- `VIEWER`

### AuditActionEnum
- `CREATE`
- `UPDATE`
- `DELETE`

---

## FuzzyDate

A custom type for dates with variable precision — used wherever a date may be partially known or unknown.

```json
{
  "year": 2019,
  "month": 3,       // optional
  "day": 15,        // optional
  "precision": "YMD",  // Y | YM | YMD | UNKNOWN
  "approx": false,     // if true, display "circa" prefix
  "circa_text": null   // optional override, e.g. "early 2019"
}
```

Stored as **JSONB** in Postgres. A generated `sortable_date` column stores the earliest-possible date for ordering (e.g. precision=Y → Jan 1 of that year). Never use a plain `DATE` column for event or biography dates.

---

## Tech Stack

**Backend (`backend/`):**
- FastAPI (async) + SQLModel + Alembic + asyncpg
- pydantic-settings for config
- redis-py (async) for stat caching
- argon2-cffi for password hashing
- APScheduler for materialized view refresh
- structlog for JSON logging

**Frontend (`frontend/`):**
- Vite + React 19 + TypeScript 6 (strict, `erasableSyntaxOnly`)
- TanStack Router v2 (file-based) + TanStack Query v5
- Radix UI primitives + shadcn-style components + Tailwind CSS v4 (dark zinc/violet theme)
- Zustand (auth store, active universe store with persistence)
- Inter font (UI) + JetBrains Mono (IDs/code)
- vis.js / react-flow for graph visualizations (Phase 7)

**Infrastructure:**
- PostgreSQL 16 (primary DB)
- Redis 7 (stat cache)
- Docker Compose (local dev)

**Python env:** `C:\Users\irish\miniconda3\envs\squiidwiki\python.exe`

---

## Recommended architecture notes

**Database: PostgreSQL** — your data is fundamentally relational: bilateral enemy constraints, family trees, stats that JOIN across members → incidents, universe-scoped queries everywhere. JSONB handles the flexible dicts (family, social_media, FuzzyDate) natively.

**Bilateral enemy constraint:** enforced at two levels — Postgres CHECK + trigger, plus application CRUD normalization. Neither alone is sufficient.

**Computed stats:** materialized views `member_stats` and `set_stats` joining incidents → incident_participants. Refreshed every 5 minutes via APScheduler. Admin endpoint for manual refresh.

**Family tree + enemy graph queries (V1):** Postgres recursive CTEs. Apache AGE (graph extension) deferred to V2 — can be added non-destructively alongside the relational schema when multi-hop graph queries become critical.

**FuzzyDate display examples:**
- `{precision: "Y", year: 2018, approx: true}` → "circa 2018"
- `{precision: "YM", year: 2019, month: 3}` → "Mar 2019"
- `{precision: "YMD", year: 2021, month: 6, day: 4}` → "Jun 4, 2021"
- `{precision: "UNKNOWN"}` → "unknown"
