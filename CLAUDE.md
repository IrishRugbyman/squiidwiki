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
- After implementing something from `ideas.md`, **delete the entry**. That file's own header says "Open items only. Implemented ideas are in git history", and none of its 90 entries is ticked - so a `- [x]` there would be the first, and would misread as "still listed, therefore still open".

## Cloudflare R2 (media storage)

- Bucket: `squiidwiki-prod` (single bucket; both `R2_BUCKET_PROD` and `R2_BUCKET_TEST` point to it)
- Endpoint: `https://2274e774b94707d729b8ca16df8c5fec.r2.cloudflarestorage.com`
- Credentials live in `.env` (`R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`). Without them the upload endpoint throws 500 immediately.
- Photos are supported on **members, sets, alliances, incidents and municipalities**: the `media` table has one FK per entity and a CHECK that exactly one is set (`source_id` has no UI). **Municipality photos always live in prod**, like municipalities themselves: `routers/media.py` routes `municipality_id` to the prod session and prod universe whatever the DB mode, and their R2 keys always start `prod/`.
- For the `media.kind` SQLModel typing quirk and the `attach_primary_photos()` Pydantic v2 workaround, see `backend/CLAUDE.md`.

## Hard rules

- **NEVER MODIFY DATA IN PROD DB** without explicit instruction. The exception currently baked in is municipalities (see Architecture → DB toggle).
- **Never name the French source in wiki prose, and never hedge a claim in it.** No entity text that renders on a page - biography, set bio, narrative, participant or incarceration note - may name `privedatabase` / privedatabase.wordpress.com, and none may argue with itself ("X adds that ..., which nothing corroborates", "this rests on one forum thread", "no press account names a shooter"). This database *is* the research: state the fact and stop. Reliability lives in the `source` row's rating, not in prose caveats. The site keeps one source row for traceability, titled "French-language gang research wiki" with its URL intact; that row is the only place the URL appears. `~/squiidape/research/privedatabase/tools/strip_source_attributions.py` did the cleanup and shows the shape of the rewrite.
- **A biography says only what no other column holds.** Never write into `biography` (or any free-text field) something the page already renders from a column: the set, the gang, the alliance, the family, the aliases, the bare status, the legal name, the dates, or the incident a member died in. The test is **state versus circumstance** - "he is incarcerated" is a column and is banned, "took the charges for his members" is a fact no column holds. Same sentence, opposite verdicts. An empty bio is the correct answer when nothing survives the strip, and more output is not better output. This applies to prose written by hand as much as to agent-drafted batches; `~/squiidape/research/privedatabase/tools/verify_bios.py` mechanises the check after the fact, and `~/squiidape/research/tools/wikilib/prose.py` now enforces it **before the write** for anything written through the `wiki` CLI: naming a source, hedging, or a moderation-safe spelling refuses the write outright, while restating a column only warns. That split is calibrated, not arbitrary: a refusing version was run against every biography on file and rejected roughly a third of them, mostly wrongly, because these biographies routinely name other people and no text-only rule can tell whose status a sentence describes. The reasoning is in `~/squiidape/research/privedatabase/README.md` under "Biographies, and the rule that makes them worth having".

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

**`./deploy.sh` from the repo root is PRODUCTION**, not dev: it runs `npm run build`
and `sudo systemctl restart squiidwiki`, the live service behind wiki.lbzgiu.xyz.
It was called `dev.sh` until 2026-08-25 and this line described it as a dev server,
which it stopped being in May 2026. For local work use the commands below.

```bash
# Manual backend (from backend/) — note port 8001, the Vite proxy targets it
PY=.venv/bin/python
$PY -m uvicorn app.main:app --port 8001     # → http://localhost:8001/docs
$PY -m alembic upgrade head                 # apply migrations to PROD DB (squiidwiki_prod)
$PY seed.py --test                          # wipe + seed TEST DB
$PY seed.py                                 # DANGER: writes mock data to PROD
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

`seed.py` parses no arguments beyond looking for `--test` in `sys.argv`, so
`--help` or any typo is silently ignored and it runs against **prod**. Only
`--test` truncates; a prod run inserts, and its single trailing commit means a
mid-run failure rolls everything back (which is what saves you).

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
- **Municipality** - geographic entity within a Universe, see DB toggle exception below. Since 2026-09-29 (migration `01b045fa156b`) it carries `kind` (CITY at the top level; under a city, DISTRICT for a sub-division that partitions it, like Detroit's ZIP codes, or NEIGHBORHOOD for a named area that may overlap districts, like Dexter-Linwood), `aliases` (street names), `region` ("Downriver"), `description`, sources (`municipality_source`) and photos. The hierarchy is one level deep, enforced in `crud/municipality.py`. A neighborhood is a child of its city, never of a ZIP, because some cross ZIP lines (Dexter-Linwood: 70% 48206, 29% 48238); the link between the two layers is `municipality_overlap` (migration `2d5a7ab2c470`), computed from the outlines with shapely by `sync_overlaps` on every sub-area write, both shares stored, slivers under 2% dropped as boundary-dataset noise. A neighborhood page reads "in 48206 (70%) and 48238 (29%)"; a district page lists its neighborhoods. After changing outlines in SQL, run `$PY -m app.scripts.recompute_overlaps`. Neighborhood outlines come from the City of Detroit's "Current City of Detroit Neighborhoods" layer (ArcGIS, `Current_City_of_Detroit_Neighborhoods/FeatureServer/0`), saved under `research/maps/geojson/places/`. The description follows the biography rule: the page already lists the place's sets, sub-areas and incidents from their own rows, so a community map's crew list becomes set rows, never prose. Written from research with `wiki muni edit`. `population` / `population_year` / `population_source` (migration `18ab21ff07f0`) are written only by `$PY -m app.scripts.import_populations [--go]`: US Census annual estimates (newest `sub-estYYYY.csv`) for US cities and townships, ACS 5-year table B01003 for ZIP districts and CDPs, through api.census.gov with `CENSUS_API_KEY` from `.env` (keyless requests are refused), falling back to the bulk summary file when the key is unset, INSEE populations légales via geo.api.gouv.fr for Corsica, whose `INSEE_MILLESIME` is pinned and needs bumping each January. Re-run it when a new vintage comes out (Census: May; ACS 5-year: December; INSEE: late December); a place its name does not match needs a `PEP_OVERRIDES` / `ACS_PLACES` entry, as Clinton Township, Augusta and Fort Campbell North have.
- **Gang cards** (`gang_card` table, `GangCard` model, since 2026-09-28) - what a gang *is*, once for every universe: colours, `nation` (FOLK = the 6, PEOPLE = the 5, Chicago lineages only), origin, `founded_at`, symbols, the national history (`description`) and its own parent card. Every `gang` row points at one through `card_id`; the card's reference fields are **mirrored** onto the gang row, and each universe's gang sits under the local gang that holds its card's parent card. Both are written only by `sync_card_to_gangs` and `sync_hierarchy` in `crud/gang.py`, so never set those columns on a linked gang in SQL. Through the API, a PATCH of a reference field, of `parent_id` or of `card_description` on any universe's gang edits the card and so every universe; `name`, `aliases` and `description` (the local note: "in Detroit it rides under the 6") stay per universe. Creating a gang links it to the oldest card of the same name, or makes a new card. The researched reference data and its sources are in `~/squiidape/research/sources/gang-cards-reference-2026-09-28.json`. Pages: `/gangs` (grouped by nation, cards with their branch trees) and `/gangs/$id`; gang pills link there.
- **Gangs** (`gang` table, `Gang` model) - top-level gang nation (Bloods, Latin Kings). The broad affiliation spanning multiple sets and alliances. `Set`, `Alliance` and `Member` each carry an **independent nullable `gang_id`**, so a member can be tagged to the nation without belonging to a known set. `ON DELETE SET NULL` on all three. **A set can claim several gangs** (NBD is Gangster Disciples and Satan Disciples): since 2026-09-28 they live in `set_gang` (`set_id`, `gang_id`, `position`, 0 = primary, both ends `ON DELETE CASCADE`), and `sets.gang_id` is only the mirror of the position-0 row, kept for the map colours, stats and every older reader. Write gangs with `gang_ids` (the complete ordered list) on `POST`/`PATCH /sets`, never by setting `sets.gang_id` in SQL: `_sync_set_gangs` in `crud/gang_set.py` is the one place that keeps the two in step. A legacy `gang_id` on PATCH makes that gang the primary and keeps the others; `null` clears them all. The `gang_id` list filter matches a set on any of its gangs, and deleting a gang promotes each affected set's next gang to primary.
- **Sets** — gang crews; allies/enemies are bilateral (normalized `set_a_id < set_b_id`). Note the model is `GangSet` and the table is `sets`, not `set`. **`sets.name` is derived, never set on its own**: it is the display of the primary entry in `name_variants`, computed by `app/core/set_names.py` on every create and update (mirrored for the form in `frontend/src/lib/setDisplay.ts`, and for the `wiki` CLI in `research/tools/wikilib/identity.py`). A variant holds one name in slots (`name`, `initials`, `number`); its `lead` is one slot or an ordered list of them, so "CFP 2400" is `lead: ["initials", "number"]` and "051 Young Money" is `["number", "name"]`. Combine slots only when the combination is the name the set goes by and it tells sibling crews apart; never initials plus the name they abbreviate ("TNO Trust No One") or plus the number that spells them on a keypad ("TMC 862"), since the other slots already show beside the name. A rename is a change to `name_variants`; a POST or PATCH whose `name` disagrees with the primary's display is a 422, and a PATCH of `name` alone is refused. Only a real rename re-slugs. Before 2026-10-02 the two could drift, and the set form's Save renamed 35 sets to their variant's display (four Cash Flow Posse sets to "CFP"); `$PY -m app.scripts.derive_set_names [--db test] [--go]` aligned every set's variants with its stored name, renaming nothing, and is idempotent.
- **Alliances** — organizations of Sets. **A set can be in several** (TMC is in TMCNE and helped form RHN; 264 and 752 are TankMafia and 4Gang): since 2026-09-30 membership lives in `alliance_set` (`alliance_id`, `set_id`, `position`, 0 = primary, both ends `ON DELETE CASCADE`), the table that had sat empty since the first schema, and `sets.alliance_id` is only the mirror of the position-0 row. Write with `alliance_ids` (the complete ordered list) on `POST`/`PATCH /sets`, never `sets.alliance_id` in SQL: `_sync_set_alliances` in `crud/gang_set.py` keeps the two in step, and joining an alliance befriends its sets. A legacy `alliance_id` makes that alliance primary and keeps the others; `null` clears them all. Editing an alliance's `set_ids` adds or drops only that alliance, and deleting one promotes each set's next alliance. The `alliance_id` list filter, the alliance's sets, members and incidents, and the "Through alliances" panel all count every membership. An alliance holds allies and enemies of its own in `alliance_relationship`: the far side is another alliance or one set outside it, never both (CHECK), alliance pairs stored once in UUID order, both ends `ON DELETE CASCADE`. A set page shows its alliance's links read-only ("Through alliances"). Members who rep an alliance without a named clique carry `member.alliance_id` directly: there is no core set named after the alliance.

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
- **The universe is in the URL** (since 2026-10-02): every page showing one universe's data lives under `/$universe/...` (`/michigan/members/ralph`), from route files named `_app.$universe.*`. Slugs are unique only within a universe (`uq_member_universe_slug` and friends; 301 member slugs recur across universes), so before this a shared link opened whichever universe the viewer had selected. `routes/_app.$universe.tsx` resolves the slug in its `beforeLoad` and writes the store every query reads its universe id from; `routes/_app.tsx` reconciles the persisted store with the server on every load (a renamed universe keeps a stale slug otherwise). `/` redirects to the last universe used. An old link (`/members/x`) parses as a universe named after its section and is redirected into the active one, which is why `RESERVED_UNIVERSE_SLUGS` in `app/schemas/universe.py` refuses page names as universe slugs; keep it in step with `SCOPED_SECTIONS` in `frontend/src/lib/universeRoutes.ts`. Links rendered inside a universe page carry `from="/$universe"` and inherit the param; anything rendered outside one (sidebar, shortcuts, palette, recents) names the universe explicitly. Recents record the universe they were visited in and are listed per universe.
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

The research tree is **not in this repository**. It lives in `~/squiidape/research`,
its own **private** repo, because this one is public and that material names living
people. It was split out on 2026-08-25 with its full history.

Nothing here depends on it, but it depends on this, in two different ways:

- most of its tools drive the backend over **HTTP on :8001**, so the wiki has to be
  running before any of them are, and an API contract change breaks them. Since
  2026-08-29 the supported write path is the `wiki` CLI at `research/tools/wiki`,
  whose `wikilib` package owns one identity resolver per entity type. If you rename
  a column it reads (`member.aliases`, `member.slug`, `member.mdoc_number`,
  `member.bop_register_number`, `member.status`, `member_custody_id`) or change what `PATCH /members/{id}` returns, fix
  `research/tools/wikilib/api.py` in the same change: it is the one module that
  knows this schema, and its 91-test suite runs in under a second;
- `research/corsica/tools/` (ten seeders that used to be `backend/app/scripts/seed_corsica*.py`,
  moved out on 2026-08-25 because they name 57 people) **import `app.core`, `app.crud`
  and `app.schemas` directly**, bootstrapping `sys.path` the way `ig` does. A moved
  schema, a renamed CRUD function or a changed enum breaks them silently.

Start at `~/squiidape/research/README.md`.

**History rewritten 2026-10-02.** The research tree had reached `master` after all
(478 paths, not the one file this note used to claim), along with the ten
`seed_corsica*` scripts and members' names in code comments, tests and commit
messages. `git filter-repo` removed `research/` and the Corsica scripts from every
commit, replaced every legal name on file with neutral text, and replaced the body of
16 commit messages that identified people; `master` and `refactor` were then
force-pushed (both at `db45c84`). The pre-rewrite history is in
`~/backups/squiidwiki-before-history-rewrite-2026-10-02.bundle` and on the Storage
Box under `backups/`. GitHub still serves old commits by SHA through merged PRs #1
and #2 until GitHub Support purges them. **Before every push, nothing here may name
a person**: no legal name, nickname or custody number in code, tests, docs or commit
messages.
