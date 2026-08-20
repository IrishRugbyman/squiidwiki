# Corsica seed scope, phase 1

What to create in the Corsica universe (`6f9b8d0a-0d3a-4086-bfc1-2a4e9025c1ae`) as the
first real entries. Scope is **exactly what `people.md` sources**: the Ziglioli case, the
war that produced it, and the deaths of the four men involved. Nothing speculative.

Everything below is checked against the live models, not against `CLAUDE.md`.

**Total: ~40 primary records** plus join rows. Small enough to review by hand, big enough
that the universe stops being empty and the set/member/incident/business pages all have
something real to render.

## Already present, do not recreate

| entity | rows |
|---|---|
| `sets` | `Police`, `Civilian` (reserved) |
| `municipality` | Ajaccio, Bastia, Corte (all with geometry) |
| `gang` | none (the five Chicago nations were cleared 2026-08-20) |

---

## 1. Gangs (2)

| name | slug | notes |
|---|---|---|
| Brise de Mer | `brise-de-mer` | The nation. Clan sets (Mariani, Guazzelli, Santucci) get added in phase 3, not now: in 1981-85 the Brise was still one crew and inventing clan sets for this period would be unsourced. |
| Clan Memmi | `clan-memmi` | The older Haute-Corse power it destroyed. |

**Petit Bar (Ajaccio) is deferred.** It is a genuine peer nation but `people.md` carries no
sourced detail on it, so it would be a name with nothing under it.

## 2. Sets (2)

| name | gang | status | municipality |
|---|---|---|---|
| Brise de Mer | Brise de Mer | `ACTIVE` | Bastia |
| Clan Memmi | Clan Memmi | `EXTINCT` | Corte |

A `Gang` and a `Set` sharing a name is correct here, not redundant: the nation had exactly
one crew at this point, and the clan sets that later split off will hang off the same Gang.

`EXTINCT` on Clan Memmi is a real use of the enum: the clan was destroyed by 1983.

**One `SetRelationship`**: Brise de Mer ↔ Clan Memmi, `ENEMY`, `from_date` 1981 (`Y`),
`until_date` 1983 (`Y`). CRUD normalises `set_a_id < set_b_id`. Closing it in 1983 records
that the war ended because one side ceased to exist.

## 3. Municipalities (9 new)

`parent_id` used for the two hamlets. All Haute-Corse.

| name | parent | why it is needed |
|---|---|---|
| Taglio-Isolaccio | - | Le Castel, Ziglioli's disco |
| Cervione | - | Ziglioli's warehouse, the murder scene |
| Vescovato | - | Santucci's killing |
| Arena | Vescovato | the hamlet with Chez Fanfan |
| Sorbo-Ocagnano | - | where Seatelli and Santucci were caught, 2 Dec 1982 |
| Biguglia | - | Seatelli's killing, 1998 |
| Borgo | - | the prison of the fax escape; the Casone stadium alibi |
| Cardo | Bastia | Seatelli's family house, bombed 28 Dec 1982 |
| La Porta | - | Moracchini's birthplace |

Geometry can be backfilled later; `geometry` is nullable. Municipalities are **prod-only**
shared geo data, so create them through the municipality router (which routes to
`prod_session` via `resolve_prod_universe`), not against the active DB.

## 4. Members (9)

Nickname-first: only Seatelli has one, so the other eight get `nickname_unknown=True` and
display by `legal_name`.

| legal_name | nickname | status | dob | date_of_death | gang | set |
|---|---|---|---|---|---|---|
| Daniel Ziglioli | - | `DEAD` | 1949/1950 (`Y`, approx) | 1982-09-14 (`YMD`) | none | none |
| Gérard Ziglioli | - | `DEAD` | - | 1983-04-14 (`YMD`) | none | none |
| Robert Moracchini | - | `DEAD` | 1959-06-06 (`YMD`) | 2025-03-29 (`YMD`) | Brise | Brise |
| Pierre-Marie Santucci | - | `DEAD` | 1956/1957 (`Y`, approx) | 2009-02-10 (`YMD`) | Brise | Brise |
| Georges Seatelli | **le Gris** | `DEAD` | - | 1998-08-21 (`YMD`) | Brise | Brise |
| François-Marie Santucci | Francis | `DEAD` | - | 1992-07 (`YM`) | Brise | Brise |
| Louis Memmi | - | `DEAD` | ~1931 (`Y`, approx) | 1981-09-10 (`YMD`) | Memmi | Clan Memmi |
| Pierre-Jean Memmi | - | `DEAD` | - | 1982 (`Y`, approx) | Memmi | Clan Memmi |
| Christian Leoni | - | `UNKNOWN` | - | - | Brise | Brise |

Notes:
- **The two Ziglioli brothers get no `gang_id` and no set.** Daniel was a club owner
  aligned with the Memmi side, not a member of the clan. Recording him under Clan Memmi
  would be a claim no source supports.
- **Francis Santucci died of cancer**, so he gets `date_of_death` but **no** incident and
  no `death_incident_id`. Good check that the death-sync path is not the only way a member
  can be dead.
- `family` JSONB carries the sibling links: Daniel↔Gérard Ziglioli, Pierre-Marie↔François-
  Marie Santucci, Louis↔Pierre-Jean Memmi, and Georges Seatelli → brother Me Jean-Louis
  Seatelli (a lawyer, not a member, so he stays a `family` entry and not a `Member` row).
- `MemberSet` spells: everyone above gets `is_primary=True` and a `from_date`. Seatelli's
  starts 1982 (`Y`, approx) since he only left law school for the clan that December.
  Leoni's starts 1985, after the trial. Memmi spells close with `until_date` at death.
- Dob for Santucci and Louis Memmi are **derived from reported ages**, hence `Y` + approx.
  Santucci's is unreliable anyway, see the open question in `people.md`.

## 5. Incidents (9)

| # | date | type | municipality | who |
|---|---|---|---|---|
| 1 | 1981-09-10 (`YMD`) | `MURDER` | Corte | Louis Memmi `VICTIM`/`KILLED` |
| 2 | 1982-09-14 (`YMD`) | `MURDER` | Cervione | Daniel Ziglioli `VICTIM`/`KILLED`, + the three accused (see below) |
| 3 | 1982 autumn (`Y`, approx) | `MURDER` | Corte | Pierre-Jean Memmi `VICTIM`/`KILLED` |
| 4 | 1982-11-28 (`YMD`) | `BOMBING` | Bastia | none (the Brise bar, material damage only) |
| 5 | 1982-12-28 (`YMD`) | `BOMBING` | Cardo | Georges Seatelli `VICTIM`/`UNHARMED` (house destroyed, he was not in it) |
| 6 | 1983-04-14 (`YMD`) | `MURDER` | - | Gérard Ziglioli `VICTIM`/`KILLED` |
| 7 | 1998-08-21 (`YMD`) | `MURDER` | Biguglia | Georges Seatelli `VICTIM`/`KILLED` |
| 8 | 2009-02-10 (`YMD`) | `MURDER` | Vescovato | Pierre-Marie Santucci `VICTIM`/`KILLED` |
| 9 | 2025-03-29 (`YMD`) | `MURDER` | Bastia | Robert Moracchini `VICTIM`/`KILLED` |

- Incidents 4 and 5 are the first real use of `BOMBING`, added in `f3fc9a8`.
- Incident 6 has no municipality: the source gives the date but not the place.
- All nine get `verified=False` until someone checks them against the cited press.
- The death-sync path will set `status=DEAD`, `date_of_death` and `death_incident_id` on
  each `KILLED` participant automatically, so those member fields can be left to it rather
  than written twice. Seven of the nine members die this way.

### Resolved: how the three acquitted men are recorded on incident 2

**They go in as real participants, flagged `acquitted=True`.** Settled 2026-08-20 and
implemented in migration `56eddc26ba9b`.

`incident_participant` now carries an `acquitted` boolean, and `member_stats` excludes
flagged rows from `shootings`, `assists` and `kills`. So the role stays on record and the
red "Kills" tile stays at zero.

The flag is a boolean rather than a disposition enum on purpose. `False` means **attributed
by research**, not **convicted**: essentially every participant row in this database comes
from press or street sourcing and was never tested in court, so "alleged" is already the
baseline meaning of the role. A court affirmatively clearing someone is the narrow
exception, and that is all the column records. Finer shades (suspected, charged but never
tried) go in the participant `notes`, which the incident page now renders.

So incident 2 gets:

| member | role | outcome | acquitted |
|---|---|---|---|
| Daniel Ziglioli | `VICTIM` | `KILLED` | false |
| Robert Moracchini | `SHOOTER` | `UNHARMED` | **true** |
| Pierre-Marie Santucci | `SHOOTER` | `UNHARMED` | **true** |
| Georges Seatelli | `ASSISTED` | `UNHARMED` | **true** |

Each of the three carries a `notes` line along the lines of *"Acquitted, Dijon, 1 June 1985,
after the principal witness retracted. No investigation into possible juror corruption was
ever opened."* The trial itself goes in `Incident.narrative`.

This is the honest recording. The earlier plan to omit the participant rows would have
treated the acquittal as truth, which in this milieu it plainly is not: not one of the
killings of the Brise barons ever produced a charge. But nor does the wiki assert guilt a
court rejected. Both facts are on the page, neither is a statistic.

## 6. Businesses (8)

First real use of the `Business` entity from `aa14ae6`. This is the part that makes Corsica
different from Detroit: the war was fought over venues, not blocks.

| name | type | municipality | status | linked member |
|---|---|---|---|---|
| Le Castel | `NIGHTLIFE` | Taglio-Isolaccio | `CLOSED` | Daniel Ziglioli `OWNER` |
| Ziglioli (wholesale drinks) | `RETAIL` | Cervione | `CLOSED` | Daniel Ziglioli `OWNER` |
| La Brise de Mer (bar) | `HOSPITALITY` | Bastia | `ACTIVE` | - (Antoine Castelli ran it; not a member row) |
| Le Continental | `NIGHTLIFE` | Bastia | `ACTIVE` | Robert Moracchini `OWNER` |
| Palais des Glaces | `NIGHTLIFE` | Bastia | `ACTIVE` | Robert Moracchini `BENEFICIARY` |
| Le Saint-Nicolas | `NIGHTLIFE` | Bastia | `ACTIVE` | Robert Moracchini `BENEFICIARY` |
| L'Apocalypse | `NIGHTLIFE` | - | `ACTIVE` | - (manager Gilbert Voillemier) |
| Chez Fanfan | `HOSPITALITY` | Arena (Vescovato) | `ACTIVE` | - |

- `BusinessRole.FRONT` fits Moracchini's mother, the official manager of Le Continental
  while he drove a Porsche bought in the bar's name. She is not a `Member`, so either she
  gets a minimal member row or the fact stays in the business `description`. **Recommend
  the description**: she is not a participant in anything.
- `status` here means the venue, not the era. Le Castel is `CLOSED`; the others are marked
  `ACTIVE` only where they are believed to still trade, which needs checking. Flagged.

## 7. Sources (10)

From the `people.md` source list, with reliability as rated there.

**Blocker: `Source.url` is `NOT NULL`** (`app/models/source.py`), and the primary source is
a printed book with no URL. Options: use the ISBN as a resolvable URL
(`https://isbnsearch.org/isbn/9782259277525`), or make `url` nullable. The book is the
single most important source in this universe, so **making `url` nullable is the right
fix**, and it is a one-column migration. Until then the ISBN URL is a workable stopgap.

Sources to create: the *Vendetta* book (`HIGH`), the four press citations from its
footnotes (Corse-Matin ×3, Le Provençal-Corse, Le Canard enchaîné), and the five online
items already listed in `people.md`. Attach via `MemberSource` and `IncidentSource`.

---

## Deferred to later phases

- **Phase 2, the internal war (2000s)**: Richard Casanova, Francis Mariani, Francis
  Guazzelli, Maurice Costa, Jacques Mariani, and the clan sets splitting off the Brise with
  `SetRelationship` rows carrying the time dimension from `2a0c6df`.
- **Phase 3, Corse-du-Sud**: Petit Bar, Ajaccio, Michelosi, Codaccioni, Germani.
- **The nationalist overlay**: FLNC, Armata Corsa, Santoni. Real and entangled, but a
  different kind of entity that the schema has no room for yet.
- **Politics**: Mimi Viola and the Giacobbi connection. Needs a relationship type the
  schema does not have.

## Execution notes

- Seed through the API, not raw SQL: the audit log, slug generation, the bilateral
  normalisation trigger and the death-sync path all live in CRUD.
- Order: municipalities → gangs → sets → set relationship → members → member sets →
  businesses → sources → incidents last (so death-sync has members to update).
- `incident_participant` is the table name, singular. `CLAUDE.md` says
  `incident_participants`; it is wrong.
- Refresh `member_stats` / `set_stats` after seeding, or wait 5 min for APScheduler.
