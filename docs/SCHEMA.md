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
