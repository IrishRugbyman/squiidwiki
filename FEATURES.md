# SquiidWiki — Features Overview

A living document to track what’s **done**, **planned**, **to do**, and **ideas**.  
Use this to prioritise work and keep the build plan in sync with the codebase.

---

## Done

### Phase 1: Foundation
- [x] Project structure (app/, alembic/, run.py, requirements.txt)
- [x] **requirements.txt** — FastAPI, uvicorn, SQLAlchemy ≥2.0, Alembic, Pydantic ≥2.0, pydantic-settings, Jinja2, python-multipart, itsdangerous, passlib[bcrypt]
- [x] **app/config.py** — Pydantic Settings (DATABASE_URL, SECRET_KEY, ADMIN_PASSWORD)
- [x] **app/database.py** — SQLAlchemy engine, SessionLocal, get_db dependency
- [x] **run.py** — Uvicorn launcher
- [x] **FuzzyDate** (app/models/base.py) — Composite type (year, month?, day?), `__composite_values__`, `__str__`, comparison, validation (month 1–12, day valid for month, no day without month)
- [x] **Auth** — Session-based password gate: login page, signed cookie (itsdangerous), check on protected routes; passlib bcrypt in auth.py (hashing helpers present)
- [x] **.env.example** — Env vars documented

### Phase 2: Data layer
- [x] **Association tables** (associations.py) — set_allies, set_enemies (self-ref M2M), member_sources, set_sources, alliance_sources, incident_sources
- [x] **Source model** — id (UUID), type enum, title, url, FuzzyDate, notes
- [x] **Alliance model** — id, name, status, founded FuzzyDate, bio, relationships, hybrid properties (all_members, total_kills)
- [x] **Set model** — id, primary_name, names (JSON), status, alliance_id, FuzzyDate, territory, colors, bio, members, allies, enemies, sources, computed fields
- [x] **Set allies/enemies bidirectional** — Normalized storage (set_a < set_b); `allies` and `enemies` properties query both directions; conflict prevention (can't be both ally and enemy)
- [x] **Member model** — id, name fields, nicknames (JSON), status, DOB/DOD/release FuzzyDate, affiliation_type, set_id, alliance_id, bio, photo_url, social_media (JSON), relationships, computed fields
- [x] **Incident + IncidentParticipant** — type, FuzzyDate, location, description; participant role, outcome, notes
- [x] **Alembic** — Initialised, env configured, initial migration; tables created on app startup

### Phase 2.5: Street-life naming logic
- [x] **`nickname_unknown` flag** — Boolean field on Member; when True, display uses real name (first + last); when False (default), nickname takes priority
- [x] **`display_name` property** — Dynamic property on Member model: returns primary nickname if available and nickname not flagged unknown; otherwise returns first + last name; used everywhere (lists, cards, graph nodes)
- [x] **Real name only on detail page** — Member detail page shows `display_name` as title; separately shows "Real name: First Last" when available; elsewhere (lists, cards) only `display_name` is shown
- [x] **Validation** — When `nickname_unknown=True`, schema requires `first_name` (real name must be provided); otherwise requires either `first_name` or at least one nickname
- [x] **Migration** — Alembic migration adds `nickname_unknown` column (default False) to members table

### Phase 3: Schemas & CRUD
- [x] **Pydantic schemas** — Create/Update/Read (and list where used) for Member, Set, Alliance, Incident (with participants), Source; FuzzyDate schema with validation
- [x] **CRUD modules** — create, get, get_all/search, update, delete per entity; member stats; set ally/enemy handling; incident with participants in transaction

### Phase 4: API & pages
- [x] **JSON API** — GET list (with search), GET by id, POST create, PUT update, DELETE for members, sets, alliances, incidents, sources
- [x] **Set allies/enemies** — POST/DELETE `/api/sets/{id}/allies/{other_id}`, `/api/sets/{id}/enemies/{other_id}`
- [x] **GET /api/graph** — Nodes (alliances, sets, members) and edges (ally, enemy, membership, alliance)
- [x] **Page routes** — `/`, `/login`, `/logout`, `/dashboard`, list + detail for members, sets, alliances, incidents, sources, `/graph`
- [x] Auth required on all pages except `/login` and static

### Phase 5: Frontend (partial)
- [x] **base.html** — Dark theme (Tailwind), sidebar nav (Dashboard, Members, Sets, Alliances, Incidents, Sources, Graph), Tailwind + HTMX CDN, responsive layout
- [x] **Dashboard** — Stat cards (members, sets, alliances, incidents), recent incidents table (last 10)
- [x] **List pages** — Table, search bar with HTMX (hx-get + delay, swaps target), link to “Add” (currently points to API)
- [x] **Detail pages** — Member, Set, Alliance, Incident, Source detail templates with key fields and relationships
- [x] **Graph page** — Full-page vis.js network; nodes (sets, alliances, members), edges (ally/enemy/member-of); toggles (Show Members, Show Alliances); click node → detail page; legend; data from `/api/graph`
- [x] **Login page** — Form, error message
- [x] **seed.py** — Sample data for testing

### Phase 5.5: UX refinements
- [x] **Member list simplified** — Removed redundant "Nicknames" column; now shows only Name (display_name), Status, Affiliation, Actions
- [x] **Status labels cleaned** — Removed redundant "ALIVE" prefix: `ALIVE_FREE` → `FREE`, `ALIVE_LOCKED_UP` → `LOCKED UP`; applied across all templates (member list/detail, set/alliance member cards)
- [x] **Nickname display on detail page** — Shows "AKA: ..." list of all nicknames separately from the display name and real name

---

## Planned (from build plan, not yet implemented)

### Frontend & UX
- [ ] **Create/Edit forms (HTML)** — `/members/new`, `/members/{id}/edit`, and same pattern for sets, alliances, incidents, sources (HTMX forms that POST to API and redirect)
- [ ] **Partials** — `partials/member_card.html`, `set_badge.html`, `stats_bar.html`, `fuzzy_date_input.html`, `search_results.html`
- [ ] **FuzzyDate input** — Reusable partial: year + optional month + optional day (month enabled when year set, day when month set)
- [ ] **Member form** — Set/alliance dropdown depends on `affiliation_type`
- [ ] **Incident form** — Dynamic participant rows (add/remove inline)
- [ ] **Set detail** — Autocomplete to add allies/enemies from UI
- [ ] **List pages** — Sortable columns; filter dropdowns (status, affiliation type, etc.); pagination; HTMX target = table body only (not whole table)
- [ ] **Dashboard** — Status breakdowns (members: free/locked/dead; sets: active/extinct); quick-add buttons
- [ ] **Flash messages** — Success/error feedback area in base layout
- [ ] **Delete confirmation** — HTMX `hx-confirm` (or modal) for delete actions

### Error handling & polish
- [ ] **Custom error pages** — 404 and 500 styled like the rest of the app
- [ ] **README** — Setup instructions, data model summary, screenshot placeholders

### Auth
- [ ] **Login using bcrypt** — Use `verify_password(plain, hashed)` in login route; store hashed password in config or DB (currently login compares plain text to `ADMIN_PASSWORD`)

---

## To do (actionable)

1. **Forms**  
   Add `form.html` per entity under `templates/{members,sets,alliances,incidents,sources}/`, plus routes `GET/POST /entity/new` and `GET/PUT /entity/{id}/edit`. Forms submit to existing API, then redirect to detail.

2. **Partials & FuzzyDate input**  
   Create `templates/partials/` and fuzzy date partial; use it in all forms that have dates.

3. **List UX**  
   - Wrap table body in an `id="tbody"` (or similar) and set HTMX target to that so only rows refresh.  
   - Add sort (query params + links or HTMX).  
   - Add filter dropdowns and pagination (skip/limit in API already).

4. **Dashboard**  
   Pass breakdown counts (members by status, sets by status) from route; add quick-add links/buttons to create pages.

5. **Flash messages**  
   Use session or query params for “Created”, “Updated”, “Deleted”, “Error”; display in base template.

6. **Delete confirm**  
   Add `hx-confirm="Delete this X?"` (or a small modal) for delete buttons.

7. **Error pages**  
   Register FastAPI exception handlers for 404/500 and render Jinja2 templates matching the dark theme.

8. **Auth**  
   In login route: hash `ADMIN_PASSWORD` at startup (or use env with pre-hashed value), then call `verify_password(password, hashed)`.

9. **README**  
   Add/update: install, `.env`, migrate, run, seed; short data model description; placeholder for screenshots.

10. **Graph**  
    - Fix node click if IDs contain hyphens (e.g. UUIDs): parse by first `-` for type, rest as id, or use a different separator in API.  
    - Optional: filter by status (e.g. only active sets) via query param or UI.

---

## Ideas (future / optional)

- **Multi-user or roles** — Move from single admin password to user accounts and permissions (e.g. viewer vs editor).
- **Audit log** — Log who changed what and when (requires user or session id).
- **Export** — CSV/JSON export for members, incidents, or full graph.
- **Import** — Bulk import from CSV or JSON.
- **Timeline view** — Incidents (and optionally births/deaths) on a timeline.
- **Map view** — Territories or incident locations on a map (e.g. Leaflet/Mapbox).
- **Full-text search** — SQLite FTS or external search over names, descriptions, sources.
- **Source verification** — Flag or tier for source reliability; show on entity pages.
- **Images** — Upload/store photos (members, sets) instead of URL-only.
- **API versioning** — e.g. `/api/v1/` for future compatibility.
- **Public read-only mode** — Optional unauthenticated read access with auth only for write.
- **RSS/activity feed** — Recent changes as RSS for power users.
- **Graph improvements** — Layout presets, zoom to selection, edge labels, filter by date range.

---

*Last updated from the Full Build Plan and codebase audit. Edit this file as you complete items or add new ideas.*
