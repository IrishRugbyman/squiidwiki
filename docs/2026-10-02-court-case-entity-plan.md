# Court case entity: plan

Status: phases 1 (schema and API) and 2 (pages) shipped 2026-10-02/03; phases 3 to 5 open. Replaces the one-line "Court case entity" item in
`ROADMAP.md` once started.

## Why

Most of the research behind this wiki comes out of courtrooms: federal
racketeering indictments, state sentences read off OTIS, BOP register numbers,
French assize trials. The wiki has no place for a case, so every one of them is
smeared across columns that were built for something else:

| Where case data lives today | Count (prod, 2026-10-02) |
|---|---|
| `member_incarceration.case_id`, free text | 443 of 558 spells, 175 distinct values: 141 Michigan court files, 14 federal dockets, 20 malformed (a court alone, a docket with an MDOC number in it) |
| OTIS spell `notes`: offense, MCL, county, plea or jury, sentence | one block per count |
| Member biographies with conviction or sentencing prose | 108 (Michigan 67, Corsica 31, Illinois 10) |
| Incident narratives with the same | 69 |
| Participant notes with the same | 27 |
| `incident_participant.acquitted` | 18 rows, a boolean standing in for a verdict |
| Set bios naming an indictment or racketeering case | 12 |
| Sources pointing at courts, DOJ, BOP, govinfo | 213 |

And on the research side: about 20 court-case document folders with defendant
tables (counts, outcome, sentence, register number), 11 staged federal cases in
`detroit/extraction/federal-cases.md`, 41 distinct federal docket strings and
about 27 state court-file numbers across the case files, 89 `incarceration:`
assertions whose sentence detail sits in `notes`, and `tools/pacer.py` able to
resolve a docket to its CourtListener records.

The cost is concrete. A biography restates a conviction that has no column
(the biography rule bans the reverse, but here there is nothing to point at).
A co-defendant list exists only by grepping `case_id`. An acquittal is one bit
on one participant row, with the charge, court and date in a note. A set's page
cannot say "the target of two racketeering cases". The same docket is written
three ways, so nothing joins on it.

## Model

Five tables, one column. Names avoid `case`, which is an SQL keyword and also
the research case-file key.

### `court_case`

| column | notes |
|---|---|
| `id`, `universe_id` | universe = where the court sits when a universe exists for it, else the universe of most defendants (a D.N.D. case against Michigan men sits in Michigan) |
| `name` | as captioned: "United States v. Surname et al.", "People v. Surname", "Affaire Surname" |
| `slug` | unique per universe, like members |
| `jurisdiction` | enum `US_FEDERAL`, `US_STATE`, `FR`, `OTHER`: drives docket normalisation and which fields the form shows, nothing else |
| `court` | normalised short form: "E.D. Mich.", "Wayne County Circuit Court", "Cour d'assises de Haute-Corse" |
| `docket` | normalised (see Backfill); unique together with `court` |
| `docket_aliases` | text[]: every other spelling seen, so OTIS and case files resolve to the row |
| `kind` | enum `CRIMINAL`, `CIVIL` (habeas, 1983), `MAGISTRATE` (complaint, warrant), `APPEAL` |
| `parent_case_id` | self FK: the appeal of a trial, the indictment a complaint became, the Rule 5 copy in another district |
| `filed_at`, `closed_at` | FuzzyDate |
| `judge` | text |
| `summary` | prose under the biography rule: what no column holds (the theory of the enterprise, a cooperator's role) |
| `courtlistener_ids` | int[]: one case spans several CourtListener dockets |

### `court_case_defendant`

One row per person charged. `member_id` is nullable with a `label`, because
indictments name people the wiki has no row for yet ("D-7").

| column | notes |
|---|---|
| `court_case_id`, `member_id` (nullable), `label`, `defendant_number` | |
| `disposition` | enum `PENDING`, `PLEADED`, `CONVICTED`, `ACQUITTED`, `DISMISSED`, `DIED`: the status words `federal-cases.md` already uses |
| `charges` | JSONB list `{count, statute, offense, disposition}`: MCL or USC citation, as OTIS and the indictments give them |
| `sentence_months`, `life_sentence`, `supervised_release_months`, `sentenced_at` | the term, which `member_incarceration` has no column for (privedatabase writes `sentence_years` into notes today) |
| `cooperated` | boolean: repentis, 5K1 cooperators. Corsica's one-in-three bio hits are largely this |
| `notes` | |

### Links

- `court_case_incident` (case, incident): the acts a case covers. Many to many: one
  racketeering case covers a dozen incidents, and one killing produces a state
  and a federal case.
- `court_case_set` (case, set): the enterprise or the sets named in the
  indictment. This is what lets a set page list its prosecutions.
- `court_case_source` (case, source): citations, copying `_sync_set_sources`
  (checks the universe, 422 otherwise), not `_sync_incident_sources`, which
  checks nothing.
- `member_incarceration.court_case_id`: nullable FK beside the raw `case_id`
  text, which stays as OTIS reports it.

### Cross-universe

Same rule incidents got this morning: a case belongs to one universe, while its
defendants and incidents can come from any (a Michigan member in an Ohio or a
North Dakota case). Its sets and sources are checked against its universe.
Links use `paramsIn` and carry `universe_slug`.

### Verdicts and `acquitted`

`incident_participant.acquitted` becomes a mirror, kept by one sync function
like `sets.gang_id` and `sets.alliance_id`: true when a case covering that
incident has the participant as a defendant with disposition `ACQUITTED`.
`member_stats` reads the column it reads today, so the views are not touched.
The 18 existing flags stay until each one has a case behind it. Until then a
flag with no case is legal, and the sync never clears it.

## Where else it applies

**Inside the wiki**

1. **Incarceration spells.** Each spell links to its case. The member page groups
   spells under the case that produced them instead of listing counts one by one.
2. **The OTIS importer** (`app/services/mdoc.py`). It already parses court file
   number, county, offense, MCL and plea or jury per count. It resolves or
   creates the state case and writes a defendant row with charges, so every
   future import feeds the entity without anyone typing.
3. **Member page:** a Cases panel (role, disposition, sentence), and the stat
   strip gains "convictions".
4. **Set page:** a Prosecutions tab from `court_case_set`, plus the count in
   `StatStrip`.
5. **Incident page:** a Cases section under Participants. The "was convicted of"
   sentence leaves the narrative.
6. **Alliance page:** cases against its sets, the way it already aggregates their
   incidents.
7. **Calendar and timeline:** sentencing days and verdicts as events. The timeline
   already has a RELEASE type, so a SENTENCED one is the same shape.
8. **Command palette:** search by docket number in any spelling, through
   `docket_aliases`.
9. **Sources:** a source page shows which case it documents, and the source list
   can group court documents by case.
10. **Data checks:** a defendant convicted of a killing who is not a participant in
    it, or a spell whose case has no defendant row for its member.
11. **Later entities.** The conflict (beef) entity on the roadmap reads its
    retaliation chains off cases, and per-fact citations can point a sentence at a
    case document.

**In research (private repo)**

12. **The `wiki` CLI:** `case new`, `case edit`, `case defendant`, `case link`
    (incidents, sets), and an assertion key `court_case` in the case files, wired
    through `assertions`, `identity` (resolve by court + docket or any alias),
    `entities` and `check`. `member spell --case` resolves to the case.
13. **The participant shorthand** in case files (`slug:ROLE:OUTCOME`) cannot say
    acquitted today; the defendant row says it instead.
14. **`tools/pacer.py`:** `pacer find` fills court, docket, filing date and
    CourtListener ids for `case new`. The PACER waiting list becomes the cases
    whose documents are unbought.
15. **Imports:** about 20 court `INDEX.md` defendant tables and the 11 staged
    sections of `federal-cases.md` become rows. A parser does the regular tables;
    the irregular ones go through the CLI by hand.
16. **`privedatabase/tools/apply_spells.py`** stops putting `sentence_years` in
    notes.

**Not applicable**

- **ig.** It posts memorials only and never about the living. A clause like "the
  man who killed him got life" would name a living person, which its rules
  forbid.
- **The map.** A case has no location of its own; its incidents already do.

## Backfill

1. **Normaliser** (`app/core/dockets.py`, mirrored in `wikilib`):
   - Federal `N:YY-cr-NNNNN` with or without the court; the court is inferred
     from a parenthetical, the case file's sources, or the spell's facility state.
   - Michigan `YYNNNNNN-XX[-suffix]`: the county comes from the OTIS notes.
   - Corsica free-form.
   - Unparseable values are reported, never guessed. The 20 malformed ones are
     fixed by hand.
2. **Federal cases first.** 14 dockets, 62 spells, and all 8 shared case ids. Create
   the case, link the spells, add defendant rows for every member holding a
   spell, enrich from the matching `INDEX.md`.
3. **State cases from OTIS:** of the 141 court files, only those meeting
   decision 1 below.
4. **Prose.** Move conviction and sentencing facts out of the 108 bios, 69
   narratives and 27 participant notes into rows, case by case, keeping what no
   column holds (the cooperation, the theory).
   `research/privedatabase/tools/verify_bios.py` checks the result.

## Phases

| | Scope | Done when |
|---|---|---|
| 1 | Migration (5 tables, the spell FK, audit registration), models, CRUD with `_check_universe`, routers, the acquitted mirror sync, API tests | the backend suite passes, and a case covering an incident flips `acquitted` both ways |
| 2 | Cases section (list, detail), panels on member, set, incident and alliance pages, palette, recents, nav, `SCOPED_SECTIONS` / `RESERVED_UNIVERSE_SLUGS` | a case page renders with a cross-universe defendant |
| 3 | Normaliser, federal backfill, the OTIS importer writing cases | 14 federal cases with linked spells; a fresh OTIS import creates its state case |
| 4 | `wiki case` verbs, the `court_case` assertion key, `check`, `pacer find` hookup, the INDEX.md importer | `wiki check` reports no drift on the imported cases |
| 5 | Prose migration, data checks, timeline and calendar events, Prosecutions stats | the bio verifier passes with conviction prose moved to rows |

Phase 1 copies the `alliance_relationship` vertical (model, migration, CRUD,
router, tests, panel). Custody numbers are a poorer template: they have no
frontend write path.

Things that will bite:
- `member_stats` and `set_stats` are untouched by design. If a later phase wants
  a "convictions" figure in them, both views are dropped and recreated together,
  since `set_stats` depends on `member_stats`; their current SQL is in
  `56eddc26ba9b`.
- Join-table writes through `__table__.delete()` skip the audit listeners.
- `attach_citation_counts` and `delete_source` in `crud/source.py` need the new
  join table.
- The test DB's views are never refreshed: the scheduler refreshes prod only.

## Decisions

1. **State cases from OTIS: only the notable ones.** A Michigan court file becomes
   a case when it has a second defendant, a linked incident, or a homicide or
   assault charge. The rest stay as spells carrying their raw court file number,
   and the OTIS importer creates a case only when one of those conditions holds.
2. **Unnamed defendants: labelled rows.** A defendant row may carry a `label` and
   no member, with its disposition and sentence, and is attached to a member when
   one is created. A CHECK requires one of `member_id` and `label`.
