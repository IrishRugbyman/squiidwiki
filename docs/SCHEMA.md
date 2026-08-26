# SquiidWiki — Schema Reference

See also `README.md` for the canonical field-level schema. This document focuses on relationships, design decisions, and the FuzzyDate spec.

---

## Entity Relationship Overview

```
Universe
  ├── Municipality (parent_id nullable → sub-districts)
  ├── Alliance
  │     └── Set (many-to-many via alliance_id FK)
  ├── Set
  │     ├── SetRelationship (bilateral friend/enemy, normalized min/max)
  │     ├── SetTerritory (set_id → municipality_id)
  │     └── Member (set_id FK)
  ├── Member
  │     ├── MemberSource (member_id ↔ source_id)
  │     └── IncidentParticipant (member_id ↔ incident_id + role + outcome)
  ├── Incident
  │     ├── IncidentParticipant
  │     └── IncidentSource (incident_id ↔ source_id)
  └── Source
```

---

## FuzzyDate

All event/biography dates use `FuzzyDate`, a JSONB structure:

```json
{
  "year":       1998,
  "month":      null,
  "day":        null,
  "precision":  "Y",
  "approx":     true,
  "circa_text": null
}
```

| Field | Type | Values |
|---|---|---|
| `year` | int \| null | 4-digit year |
| `month` | int \| null | 1–12 |
| `day` | int \| null | 1–31 |
| `precision` | enum | `Y` \| `YM` \| `YMD` \| `UNKNOWN` |
| `approx` | bool | true → "circa" prefix in display |
| `circa_text` | str \| null | Free-text override ("mid-1990s") |

**Display rules:**
- `UNKNOWN` → "unknown"
- `Y` + approx → "circa 1998"
- `YM` → "Mar 1998"
- `YMD` → "Mar 15, 1998"
- `circa_text` set → use it verbatim (overrides all)

**Validation:** precision `Y` requires `year`; `YM` requires `year` + `month`; `YMD` requires all three.

**Sorting:** a generated `sortable_date` column stores the earliest possible `DATE` for ordering (year-01-01 for Y precision, year-month-01 for YM, exact date for YMD). `UNKNOWN` sorts as NULL.

---

## Bilateral Set Relationships

Set friend/enemy relationships are stored as a single row per pair, normalized so `set_a_id < set_b_id` (lexicographic UUID comparison). A Postgres trigger rejects inserts that violate this ordering; the application layer also normalizes before insert.

The `type` column is `FRIEND` or `ENEMY`. An additional constraint prevents the same pair from appearing in both types simultaneously (enforced at the CRUD layer with a 409 conflict check).

To query all relationships for set X (regardless of which column it appears in):
```sql
SELECT * FROM set_relationships
WHERE set_a_id = :x OR set_b_id = :x
  AND universe_id = :universe_id;
```

---

## Incident Participants

The `incident_participants` join table replaces the old dict-of-lists approach:

| Column | Type | Notes |
|---|---|---|
| `incident_id` | UUID FK | |
| `member_id` | UUID FK | |
| `role` | enum | `SHOOTER` \| `ASSISTED` \| `BYSTANDER` \| `VICTIM` |
| `outcome` | enum | `KILLED` \| `INJURED` \| `UNHARMED` \| `UNKNOWN` |
| `notes` | text \| null | Free-text role notes |

A member can appear only once per incident (unique constraint on `incident_id, member_id`). Role and outcome are independent — a SHOOTER can have outcome KILLED (e.g., shot back).

---

## Incarceration Spells

`member_incarceration` carries four dates, and three of them are easy to
conflate. The distinction that matters is **fact versus forecast**:

| Column | Type | Notes |
|---|---|---|
| `from_date` | FuzzyDate \| null | Date of sentence |
| `to_date` | FuzzyDate \| null | When the spell **actually** ended. A fact |
| `earliest_release_date` | FuzzyDate \| null | Soonest release the sentence allows. A forecast. Blank for federal terms, which have no parole |
| `max_discharge_date` | FuzzyDate \| null | Latest release the sentence allows. A forecast |
| `life_sentence` | bool | Nulls both forecasts at the CRUD layer |

`to_date` is what makes a spell historical. Once it is set, the two forecasts are
projections that were overtaken by events: they stay on the row as the record of
what was expected, but `list_universe_release_events` excludes the spell, so
nothing announces a 2046 max discharge for someone released in 2015. Setting
`life_sentence` does **not** suppress `to_date` - commutation and death both end
a life term, and both are worth recording.

All four use `JSONB(none_as_null=True)`. Without it an absent date is stored as
the JSON scalar `null`, which `IS NULL` cannot see, and the release-events filter
silently matches nothing.

**MDOC imports.** OTIS splits these facts across two places, and the split is the
reason a discharged offender used to import as an empty page. Each sentence row
carries its own `from_date` and, once served, its own `to_date`. The forecasts
and the facility live in the profile's Status block instead, belong to the
offender rather than to any one sentence, and are blank once he is out.
`derive_spells` in `app/services/mdoc.py` reconciles the two: one spell per
prison sentence, with the Status block attached to the single most recent spell
still running, so concurrent sentences yield one projected release rather than
three.

**Probation is not imported, and this table holds no supervision.** OTIS covers
probationers as well as prisoners, and a profile can carry probation sentences
and no prison time at all - in which case the correct import result is zero
spells and a member page reading "No incarceration records". A probation term
rendered in this table would read on the page as time served, which is a false
claim about a named living person; keeping the offense detail is not worth that.
The import UI says how many probation sentences it saw, so an empty result is
not mistaken for a failed import. This is a decided product rule, not a gap.
Revisiting it means adding a `kind` column here (or a sibling table), not
loosening the filter in `derive_spells`.

---

## Materialized Views

### `member_stats`

| Column | Description |
|---|---|
| `member_id` | UUID |
| `shootings` | Incidents where role = SHOOTER |
| `assists` | Incidents where role = ASSISTED |
| `kills` | Incidents where role = SHOOTER and outcome of any VICTIM = KILLED |
| `times_shot_survived` | Incidents where role = VICTIM and outcome = INJURED or UNHARMED |

### `set_stats`

| Column | Description |
|---|---|
| `set_id` | UUID |
| `member_count` | Active members (status != DEAD) |
| `dead_members` | Members with status = DEAD |
| `total_shootings` | Sum of member shootings |
| `total_assists` | Sum of member assists |
| `total_kills` | Sum of member kills |

Both views are refreshed every 5 minutes and fall back to zeros when not yet populated.

---

## Audit Log

All writes to tracked entities are recorded in `audit_log`:

| Column | Type |
|---|---|
| `id` | UUID |
| `user_id` | UUID FK → users |
| `entity_type` | varchar (e.g., "Member", "Incident") |
| `entity_id` | UUID |
| `action` | enum: `CREATE` \| `UPDATE` \| `DELETE` |
| `diff_json` | JSONB — before/after values for UPDATE; full record for CREATE/DELETE |
| `created_at` | timestamptz |

The audit listener uses SQLAlchemy event hooks and reads the acting user from request context set by the auth middleware.
