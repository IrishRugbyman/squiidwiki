# Handoff: History tab and data-anomaly report

Branch `claude/history-tab-anomalies`, built 2026-11-03 in a cloud session against a
throwaway Postgres 16 in the container (no prod data, no R2). No PR opened.

## What was built

### 1. History tab (ROADMAP: "Version history / diff view on biographies")

**Endpoint:** `GET /api/v1/history/{entity_type}/{entity_id}?universe_id=...&offset=0&limit=50`

- `entity_type` is `member`, `set`, `alliance`, `incident` or `source`; `entity_id`
  is the UUID (not the slug). 404 if the entity is not in that universe, 422 for an
  unknown type.
- **Who can see it: admins only**, the same gate as `GET /audit/`. It is the same
  data (who changed what, by account email) seen through a narrower window, so it
  would be odd for a USER to see per-entity what they cannot see globally. The tab
  is not rendered for non-admins.
- Response: `{items, total, labels}`. Each item has `created_at`, `action`,
  `actor {id, email}`, `entity_type/entity_id` (the row's owner), `is_self`, and
  either `changes` (column old -> new, `kind` = `scalar` / `text` / `opaque`) or a
  link delta (`link`, `link_key`, `added`, `removed`, `changed`). `labels` maps
  every UUID on the page to `{type, label, slug}` so the UI can link it.

**How the diffs are made.** The audit listeners store a whole-row snapshot per
write, not a diff, so `app/crud/history.py` compares each snapshot with the
previous one for the same entity. Saves that changed nothing visible (only
`updated_at`) are dropped. An entity whose first audit row is an UPDATE (seeded or
written in SQL) shows one "first recorded state" marker instead of a fake diff.

**Join rows ("who put this member in this set").** These were never audited: the
sync functions replace every row with a Core DELETE and re-insert on each save,
which ORM listeners cannot follow. Each sync function now reads its rows first and
calls `record_link_change` (`app/core/audit.py`), writing one audit row on the
owner only when the list really changed. Its `_related` list names every far side
and is GIN-indexed, so the far side's history picks it up too: a set's History
shows "on member Member A: + Sets: this set". Covered:

| Owner | Link lists |
|---|---|
| member | `sets` (incl. ending a spell via `/affiliations/{id}/end`), `sources` |
| incident | `participants`, `set_participants`, `sources` |
| set | `gangs`, `alliances`, `sources` |
| alliance | `sets` (the alliance-side `set_ids` edit) |

**Frontend.** A History tab on the member, set, alliance, incident and source
pages (admins only). The set and source pages already had tabs, so History is
one more tab there (`?tab=history` on sets). Member, alliance and incident pages
get an Overview / History switch under the header; the overview stays mounted
while History is open, so a half-written bio edit survives. Long text renders as
a red/green word diff (`lib/wordDiff.ts`), scalars as old -> new, ids as links.
`EntityHistory` is a lazy chunk (3.3 kB gzipped).

### 2. Data anomaly report (ROADMAP: "Data anomaly dashboard")

**Endpoint:** `GET /api/v1/admin/anomalies?universe_id=...[&kind=...&kind=...]`, admin
only. It returns `{universe_id, checks: [{kind, title, count}], items: [{kind,
entity_type, entity_id, slug, display_name, message, related_type, related_id,
related_label}]}`. An unknown `kind` is a 422, so a CLI typo is not read as "no
findings". The checks are plain functions in `app/crud/anomalies.py`:

```python
data = await load_universe_data(session, universe_id)
findings = run_checks(data)                      # or run_checks(data, {"killed_twice"})
```

| kind | What it flags |
|---|---|
| `set_member_unsourced` | Member with an open spell in a non-reserved set, and no source anywhere behind them: no `member_source` row and no source on any incident they are in. **My reading:** `member_set` has no source column, so "the set link was added without a source" cannot be asked of the link itself; "nothing cites this person at all" is the nearest question the schema can answer. Unknown/Police/Civilian are skipped, since parking someone in Unknown is not a claim. |
| `dead_without_death_record` | `status=DEAD`, no usable `date_of_death`, no `death_incident_id` |
| `incident_after_death` | Participant in an incident unambiguously later than **every** death record they have (a KILLED outcome elsewhere, or `date_of_death`) |
| `incident_before_birth` | Participant in an incident unambiguously before their `dob` |
| `extinct_set_recent_incident` | EXTINCT set involved in an incident whose earliest possible date is within the last 730 days: as a set participant, or through a shooter/assist whose current primary set it is. Sets have **no extinction date**, so "after it went extinct" cannot be asked; "recently" is used instead. |
| `death_incident_but_not_dead` | `death_incident_id` set but status is not DEAD |
| `killed_but_not_dead` | Outcome KILLED in an incident but status is not DEAD (half an un-kill) |
| `killed_twice` | Outcome KILLED in two or more incidents |
| `death_before_birth` | `date_of_death` unambiguously before `dob` |
| `spell_ends_before_start` | A set spell whose `until_date` is unambiguously before its `from_date` |

**FuzzyDate rule.** Every comparison maps a date to the span of days it could mean
(Y = the whole year, YM = the month, approximate or circa widens it by a year on each
side, UNKNOWN = no span) and reports only when the spans do not overlap. "Mar 2021"
against "2021" is never a finding; "2021" against "2023" is.

**Frontend.** `/$universe/anomalies`, linked as "Anomalies" in the admin section of
the sidebar. Findings are grouped by check (collapsible), each linking to the entity
and to the record it contradicts; checks that came back clean are listed at the foot.
`anomalies` was added to `SCOPED_SECTIONS` and `RESERVED_UNIVERSE_SLUGS`.

## Migrations

- `8ee2386f30c6` (revises `3c7f32fad6eb`, the search migration; it revised `81e18d3c4faa` until the two branches were stacked): GIN index
  `ix_audit_log_diff_json_related` on `(diff_json -> '_related') jsonb_path_ops`.
  Index only, no data change. Tested up, down and up again.

## Test results

- Backend: **321 passed** (baseline on master was 300; +8 in `tests/test_history.py`,
  +13 in `tests/test_anomalies.py`, each anomaly check with a positive and a
  negative case, plus FuzzyDate-span unit tests).
- Frontend: `npm run build` passes; vitest **176 passed** (incl. new
  `lib/wordDiff.test.ts`). Main chunk 56.97 -> 57.36 kB gzipped.
- `npm run lint` **already fails on master** (137 errors, nearly all
  `react-refresh/only-export-components` on route files, which is how every route
  file here is written). This branch adds exactly one more of that rule (the
  anomalies page component); nothing else.
- Checked in a real browser (Playwright against uvicorn + Vite): member History
  showing field diffs, the bio word diff, set link changes and an incident
  participation; set History showing the member being added; the anomalies page
  with three kinds of finding. No console errors.

## Left out, and why

- **Other join tables** are not link-audited yet: set relationships (allies and
  enemies), lineage, alliance relationships, territory/municipality links, aliases,
  family, incarcerations, custody ids, businesses. Same pattern applies
  (`record_link_change` in the sync function); I kept to the lists that answer the
  "who put X in Y" question to keep the diff reviewable.
- **No backfill.** Link changes before this branch were never written anywhere, so
  "who added this member to this set" is answerable only for edits made after deploy.
- **Municipality history** is not exposed: municipalities live in the prod DB
  whatever the DB mode, and the endpoint reads the active DB.
- **Deleting a member** removes their join rows with Core deletes, so a set's
  History does not show "member removed (deleted)". The member's own history is
  moot once the page is gone.
- **Pre-existing warning:** the audit listeners call `session.add()` during flush,
  which SQLAlchemy warns about (`SAWarning: Usage of the 'Session.add()' operation
  is not currently supported within the execution stage of the flush`). The rows
  do persist. The warning shows more often in tests now because the history tests
  attach the listeners, as the app does on startup. A rewrite to
  connection-level inserts is a separate change.

## To try it locally

```bash
cd ~/squiidape/squiidwiki
git fetch origin && git checkout claude/history-tab-anomalies

# 1. Migrate (prod, then test if it exists)
cd backend
.venv/bin/python -m alembic upgrade head
DATABASE_URL_PROD='<DATABASE_URL_TEST from .env>' .venv/bin/python -m alembic upgrade head

# 2. Restart uvicorn on :8001
pgrep -af "uvicorn app.main"   # kill <pid>
.venv/bin/python -m uvicorn app.main:app --port 8001 &

# 3. Tests (optional)
.venv/bin/python -m pytest -q

# 4. Frontend
cd ../frontend && npm run build
```

Then, logged in as an admin:

1. Open any member page (`/<universe>/members/<slug>`), click **Edit**, add them to a
   set and change a sentence of the biography, save.
2. Click **History** under the header. Expect an UPDATE entry with the biography as a
   red/green word diff and a LINKS entry `+ Sets: <set>` with your email and the time.
3. Open that set and click its **History** tab. Expect `on member <name>: + Sets: this set`.
4. In the sidebar's admin section click **Anomalies** (`/<universe>/anomalies`). Expect
   the findings grouped by check, each name linking to its page.
