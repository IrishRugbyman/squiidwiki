# SquiidWiki — Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
│   React 18 + TanStack Router/Query + Zustand + shadcn/ui   │
│                    http://localhost:5173                     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/JSON (REST)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                           │
│                 http://localhost:8000                        │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Auth layer  │  │  API routers │  │   APScheduler    │  │
│  │  JWT + argon2│  │  /api/v1/... │  │  (stats refresh) │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────┘  │
│         │                 │                                  │
│  ┌──────▼─────────────────▼──────────────────────────────┐  │
│  │              SQLModel ORM (async SQLAlchemy)           │  │
│  └───────────────────────┬───────────────────────────────┘  │
└──────────────────────────┼──────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                                   ▼
┌─────────────────┐               ┌──────────────────┐
│  PostgreSQL 16  │               │    Redis 7        │
│  (primary data) │               │  (stat cache,     │
│                 │               │   future tasks)   │
│  - All entities │               └──────────────────┘
│  - Audit log    │
│  - Materialized │
│    views        │
└─────────────────┘

Monitoring (optional local stack):
  Prometheus → scrapes /metrics at :8000
  Grafana    → visualizes at :3000
```

## Request Flow

1. **Browser** → TanStack Query sends HTTP request with `Authorization: Bearer <jwt>`
2. **FastAPI** → JWT verified in `CurrentUser` dependency; `universe_id` scopes all DB queries
3. **CRUD layer** → async SQLAlchemy queries; writes go through `session.commit()`
4. **Audit listener** → SQLAlchemy event listener captures INSERT/UPDATE/DELETE and writes to `audit_log`
5. **Response** → Pydantic schema serializes the ORM object; `X-Request-ID` header added by middleware

## Multi-Tenancy (Universe Scoping)

Every entity except `users` and `universes` carries a `universe_id` column. The CRUD layer always includes `WHERE universe_id = :uid` in queries. API handlers extract `universe_id` from the query string and pass it to CRUD functions — there is no cross-universe query path from the API layer.

Users have global roles (`ADMIN` / `USER`) plus optional per-universe roles via `user_universe_access`. Global ADMIN bypasses per-universe checks.

## Auth Flow

```
POST /api/v1/auth/login
  → verify argon2 hash
  → issue access_token (JWT, 15 min, Bearer)
  → set refresh_token (opaque, 30 days, httpOnly cookie)

POST /api/v1/auth/refresh
  → verify refresh_token, rotate it
  → issue new access_token

POST /api/v1/auth/logout
  → delete refresh_token cookie
```

## Stat Caching

`member_stats` and `set_stats` are Postgres **materialized views** that aggregate kill/shooting counts. They are:

- Refreshed every **5 minutes** by APScheduler running in the backend process
- Refreshable on-demand via `POST /api/v1/admin/refresh-stats` (Admin only)
- Read via raw SQL `SELECT * FROM member_stats WHERE member_id = :id`
- Gracefully fallback to zeros if the view is missing (test DB scenario)

## Frontend State

| Concern | Tool |
|---|---|
| Auth (token, user info) | Zustand `auth` store |
| Active universe | Zustand `universe` store |
| Server data fetching/caching | TanStack Query |
| URL routing | TanStack Router v2 (file-based) |

## Key Design Constraints

- **FuzzyDate** is stored as JSONB — never `DATE`. This handles year-only, month-year, and unknown dates.
- **Bilateral set relationships** (friend/enemy) are stored once as `(min_id, max_id)` with a Postgres trigger enforcing the ordering. Both application and DB enforce normalization.
- **Incident participants** use a join table (`incident_participants`) with `role` and `outcome` enums — no dict-of-lists.
