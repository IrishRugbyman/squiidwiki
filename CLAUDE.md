# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Subdirectory guides** (auto-loaded when you touch files in those trees):
- `backend/CLAUDE.md` — code layout, route + CRUD conventions, Alembic migrations, backend pitfalls
- `frontend/CLAUDE.md` — code layout, shared UI primitives, keyboard shortcuts, Recents, performance, frontend pitfalls

## Verification Requirements

- After making a UI or navigation change, state exactly: (1) what URL to visit, (2) what to click, (3) what to expect — then wait for user confirmation before declaring done
- Never mark work complete based on type-checks or compilation alone; `tsc --noEmit` passing is necessary but not sufficient
- Do not move to the next task until the user confirms the fix works in the browser
- **Frontend changes need `npm run build`** — the user serves the production build, not the Vite dev server. After any frontend edit, tell the user to run `npm run build` (from `frontend/`) before reloading.
- After implementing something from `ideas.md`, check it off (`- [ ]` → `- [x]`).

## Cloudflare R2 (media storage)

- Bucket: `squiidwiki-prod` (single bucket; both `R2_BUCKET_PROD` and `R2_BUCKET_TEST` point to it)
- Endpoint: `https://2274e774b94707d729b8ca16df8c5fec.r2.cloudflarestorage.com`
- Credentials live in `.env` (`R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`). Without them the upload endpoint throws 500 immediately.
- Photos are supported on **members, sets, and alliances** — the `media` table has `member_id`, `set_id`, `alliance_id` (plus `incident_id`/`source_id` for schema completeness, but no UI for those).
- For the `media.kind` SQLModel typing quirk and the `attach_primary_photos()` Pydantic v2 workaround, see `backend/CLAUDE.md`.

## Hard rules

- **NEVER MODIFY DATA IN PROD DB** without explicit instruction. The exception currently baked in is municipalities (see Architecture → DB toggle).
- **Never name the French source in wiki prose, and never hedge a claim in it.** No entity text that renders on a page - biography, set bio, narrative, participant or incarceration note - may name `privedatabase` / privedatabase.wordpress.com, and none may argue with itself ("X adds that ..., which nothing corroborates", "this rests on one forum thread", "no press account names a shooter"). This database *is* the research: state the fact and stop. Reliability lives in the `source` row's rating, not in prose caveats. The site keeps one source row for traceability, titled "French-language gang research wiki" with its URL intact; that row is the only place the URL appears. `research/privedatabase/tools/strip_source_attributions.py` did the cleanup and shows the shape of the rewrite.
- **A biography says only what no other column holds.** Never write into `biography` (or any free-text field) something the page already renders from a column: the set, the gang, the alliance, the family, the aliases, the bare status, the legal name, the dates, or the incident a member died in. The test is **state versus circumstance** - "he is incarcerated" is a column and is banned, "took the charges for his members" is a fact no column holds. Same sentence, opposite verdicts. An empty bio is the correct answer when nothing survives the strip, and more output is not better output. This applies to prose written by hand as much as to agent-drafted batches; `research/privedatabase/tools/verify_bios.py` mechanises the check, and the reasoning is in `research/privedatabase/README.md` under "Biographies, and the rule that makes them worth having".

## Development Environment (Linux server)

- Backend venv: `/home/lbzgiu/squiidape/squiidwiki/backend/.venv/` — invoke as `.venv/bin/python` or `.venv/bin/uvicorn`.
- Postgres 16 runs natively on `localhost:5432` as user `lbzgiu`. Databases: `squiidwiki_prod` (always present) and `squiidwiki_test` (may not exist — check before migrating).
- `.env` lives at the **repo root** (`/home/lbzgiu/squiidape/squiidwiki/.env`), not in `backend/`. `DATABASE_URL_PROD` and `DATABASE_URL_TEST` are defined there.
- Restart uvicorn with `pgrep -af "uvicorn app.main"` → `kill <pid>` → relaunch in background. `--reload` is fine here, but production-style runs use `--workers 2` (note: in-process DB-mode toggle is inconsistent across workers — single-worker is cleaner for local dev).
- Alembic: `env.py` reads `settings.database_url_prod` from `.env` and **ignores** the stale `sqlalchemy.url` in `alembic.ini`. To migrate the test DB, run `DATABASE_URL_PROD=<test-url> .venv/bin/python -m alembic upgrade head` (do not try `Config.set_main_option` — `%`-encoded passwords trip configparser interpolation).
- New Alembic revision IDs: pick a fresh random hex (`python -c "import secrets; print(secrets.token_hex(6))"`). The existing repo IDs are heavily patterned and easy to collide with.
- If a bash command fails twice, stop retrying: summarize what was tried, state the hypothesis, and ask the user how to proceed.

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
- Vite + React 19 + TypeScript (strict)
- TanStack Router v1 (file-based, fully typed routes — `routeTree.gen.ts` is generated by `@tanstack/router-plugin`)
- TanStack Query v5 (data fetching, caching; global error toasts wired in `main.tsx`)
- Tailwind CSS v4 + shadcn/Radix primitives (dark-themed)
- Zustand (auth state, active universe, recents; persisted to localStorage)
- sonner — toast notifications
- cmdk — global command palette (⌘K)
- recharts — dashboard analytics charts (lazy-loaded)
- reactflow — set relationship network graph (lazy-loaded)
- maplibre-gl — choropleth municipality map (lazy-loaded)

**Infrastructure**
- PostgreSQL — primary database (native Postgres on Windows; not Docker for local dev)
- Redis — stat cache + (future) task queue
- Cloudflare R2 — image/media storage (S3-compatible); credentials in `.env` (see R2 section below)
- docker-compose for service orchestration

**Auth:** JWT access tokens + rotating refresh tokens. `GlobalRole` is `'ADMIN' | 'USER'`. Admins can view audit logs, manage universes, change user roles, and delete entities. Audit log on all writes.

## Development Commands

**Python env:** `/home/lbzgiu/squiidape/squiidwiki/backend/.venv/bin/python` — always invoke via this path (no venv activation needed).

**Easiest local dev:** `./dev.sh` from repo root — kills anything on :8001 / :5173, then runs backend (uvicorn on **:8001**) and frontend (Vite on :5173) together.

```bash
# Manual backend (from backend/) — note port 8001, the Vite proxy targets it
PY=.venv/bin/python
$PY -m uvicorn app.main:app --port 8001     # → http://localhost:8001/docs
$PY -m alembic upgrade head                 # apply migrations to PROD DB (squiidwiki_prod)
$PY -m app.seed                             # seed sample data (Metro Detroit)
$PY -m app.seed --test                      # wipe + seed TEST DB
$PY -m pytest --cov                         # run tests
$PY -m pip install -r requirements-dev.txt  # install deps

# Frontend (from frontend/)
npm run dev          # → http://localhost:5173
npm run build        # full type-check (tsc -b) + production build
npm run lint
npx tsc --noEmit     # fast type check (misses unused-import errors)

# Infrastructure (only Redis here is actually needed if Postgres runs natively)
docker compose up -d
```

**Local admin login (after seed):** `admin@squiidwiki.dev` / `admin1234`. The seed.py-created user has a placeholder password hash and cannot log in — use the admin credentials instead.

**Commit style:** recent history uses `feat(<scope>): <short summary>` (e.g. `feat(frontend): ...`, `fix: ...`) with a multi-line body describing what changed and why.

## Architecture

### Data Model Hierarchy

```
Universe → Municipality
         → Gangs → Alliances → Sets → Members → Incidents → Sources
         → ResearchNote (per-universe scratchpad)
```

- **Universe** — top-level isolation container; every entity carries `universe_id`
- **Municipality** — geographic entity (cities, districts) within a Universe — see DB toggle exception below
- **Gangs** (`gang` table, `Gang` model) - top-level gang nation (Bloods, Latin Kings). The broad affiliation spanning multiple sets and alliances. `Set`, `Alliance` and `Member` each carry an **independent nullable `gang_id`**, so a member can be tagged to the nation without belonging to a known set. `ON DELETE SET NULL` on all three.
- **Sets** — gang crews; allies/enemies are bilateral (normalized `set_a_id < set_b_id`). Note the model is `GangSet` and the table is `sets`, not `set`.
- **Alliances** — organizations of Sets

The three tiers are a hierarchy by convention, not by constraint: nothing forces a Set's `gang_id` to agree with its Alliance's, and every link is nullable. `create_universe` seeds only the reserved sets (Police, Civilian, Unknown), **not** gangs. **Unknown** is the holding pen for members whose set has not been worked out yet - park them there rather than leaving them setless, so the gap reads as a queue instead of an absence. Reserved sets cannot be created by name, deleted, or edited beyond their bio. But migration `33ac22d53ce8` (2026-05-08) backfilled five Chicago nations into *every universe existing at the time*, which is wrong for any non-US universe - check `gang` and clear it before seeding real data. (Cleared for Corsica on 2026-08-20; Detroit and Chicago still carry theirs.)
- **Members** — nickname-first identity; `display_name` property always used (nickname default, legal name when `nickname_unknown=True`); `social_media` JSONB stores `{facebook?, instagram?, twitter?}` handles or URLs; `death_incident_id` FK auto-populated when a participant in any incident has `outcome=KILLED` (see "Incident-driven death sync" below)
- **Incidents** — events with a typed participant table (`incident_participant`: member_id + role + outcome + acquitted); no shooter/killer dict
- **Sources** — citations with reliability rating; M2M with Members and Incidents
- **ResearchNote** — per-universe freeform note (title + content); URLs auto-link in display

### Key Design Decisions

- **FuzzyDate** — JSONB `{year, month?, day?, precision: Y|YM|YMD|UNKNOWN, approx: bool}`. Custom SQLAlchemy TypeDecorator. Never use a plain `DATE` column for event/biography dates.
- **Bilateral relationships** — stored once as `(set_a_id < set_b_id)` with a Postgres trigger enforcing the ordering. Application CRUD always normalizes pairs before insert.
- **Incident participants** — `incident_participant` join table (singular) with `role ∈ {SHOOTER, ASSISTED, BYSTANDER, VICTIM}` and `outcome ∈ {KILLED, INJURED, UNHARMED, UNKNOWN}`. Do not use dict-of-lists.
- **`incident_set_participant` is for attribution without a name** — use it only when a set is known to be involved and **no individual member can be named** (an unidentified shooter from a known set). If every actor is already a member row, the set rows add nothing: each member carries their set, so the page just repeats itself and the participant counter inflates. It contributes nothing to `set_stats` either, which derives entirely from `member_stats` via `incident_participant`. Note also that `outcome` on a set row is meaningless — "Hustle Boyz / Victim / Killed" reads as the organisation being killed.
- **`incident_participant.acquitted`** - a court affirmatively cleared this person of this role. `False` means **attributed by research**, NOT **convicted**: nearly every participant row here comes from press or street sourcing and was never tested in court, so "alleged" is already the baseline meaning of a role. `member_stats` excludes flagged rows from `shootings`, `assists` and `kills`, so an acquitted man keeps the role on his page but shows no red "Kills" tile. Detail goes in the participant `notes`, which the incident page renders. Deliberately a boolean, not a disposition enum - finer shades (suspected, charged but never tried) belong in `notes`. Any code that rebuilds a participants payload must carry `acquitted` through, or it silently clears the flag on every existing row.
- **Incident-driven death sync** — saving an incident with a participant `outcome=KILLED` runs `_sync_killed_participants` in `app/crud/incident.py` after `_sync_participants`. For each killed member it sets `status=DEAD`, copies `incident.date` to `member.date_of_death` (only when the incident date has at least year precision), and assigns `member.death_incident_id=incident.id` (first death wins; never overrides an existing link to a *different* incident). Fires on both create and update. Audit listeners on `member` capture the changes for free. Reverting (un-kill) is **never automatic** — clear status manually on the member to undo. The FK uses `ON DELETE SET NULL`, so deleting an incident unlinks but does not change the member's status.
- **Computed stats** — materialized views `member_stats` and `set_stats`; refreshed every 5 min via APScheduler + manual admin endpoint. List endpoints return live data; stat tiles can show stale counts briefly after edits.
- **Universe scoping** — all CRUD functions take `universe_id`; no cross-universe queries from API handlers.
- **Slug vs UUID in routes** — GET single-resource endpoints (`/members/{id_or_slug}`, sets, alliances) accept either a UUID or a slug. **PATCH and DELETE require UUID.** On detail pages, mutation hooks (`useUpdateMember`, etc.) must be passed the loaded `entity.id`, never the route param `$id` (which is the slug). Passing a slug to PATCH yields a Pydantic UUID validation error.

### DB toggle (prod ↔ test)

There are two databases (`squiidwiki_db` = prod, `squiidwiki_test` = test). The active DB is in-process global state in `app/core/database.py` (`_active_db`), toggled via `/api/v1/admin/db-mode` (admin only). The frontend has a sidebar-footer toggle that nullifies the active universe before switching, so the user re-picks a universe in the new DB.

- **Auth always uses prod** (`get_prod_session` dep) — switching mode does NOT invalidate JWTs.
- **Municipalities always use prod** — they're shared geo reference data. The router uses `resolve_prod_universe(active_session, prod_session, universe_id)` from `app/core/database.py` to translate the active-DB universe id to the matching prod-DB universe id by slug, then operates on `prod_session`. Reuse this helper for any future feature that should also be prod-only.
- **In-process state**: switching mode persists until backend restart. Multi-worker uvicorn would be inconsistent — local dev uses single-worker.

### Enums

- Member status: `FREE`, `LOCKED`, `DEAD`, `UNKNOWN`, `ESCAPEE`, `ABSCONDER`
- Set status: `ACTIVE`, `EXTINCT`
- Alliance status: `ACTIVE`, `EXTINCT`, `DORMANT`
- Source reliability: `HIGH`, `MEDIUM`, `LOW`, `UNVERIFIED`
- Incident type: `SHOOTING`, `MURDER`
- Incident participant role: `SHOOTER`, `ASSISTED`, `BYSTANDER`, `VICTIM`
- Incident participant outcome: `KILLED`, `INJURED`, `UNHARMED`, `UNKNOWN`
- Global role: `ADMIN`, `USER`

## External consumer: `~/squiidape/ig`

`~/squiidape/ig` reads this repo's database and imports from its venv, so changes
here can silently break it - and the wiki instance's privacy constrains what may
leave this machine. Both are documented once, a level up, in
`~/squiidape/CLAUDE.md`. **Read it before touching `app/core/storage.py`, the
`member` / `media` / `incident` tables or the `FuzzyDate` shape.**

## Research

`research/README.md` is the entry point: what the tree holds and how material
moves through it. Which sources exist for a universe, how far each one reaches
and how to read it is per-universe - Detroit's is
`research/detroit/README.md` ("Where the material comes from"). Read that before
starting a round of research, not this file.
