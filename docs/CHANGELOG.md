# SquiidWiki - Changelog

What was built, what was tried, and what it was for. One dated entry per session
or shipped change. Forward-looking work lives in `ROADMAP.md`; when something
here ships, its line comes out of that file.

---

## 2026-09-29 - Sets cite their sources; alliances delete cleanly

`set_source` existed since `3aed746` with no write path: no schema field, no CRUD,
nothing on the page, so every citation a set was given lived only in the research
case files. `SetCreate` and `SetUpdate` now take `source_ids` (the complete list; `[]`
clears, omitted keeps), checked to belong to the set's universe (422 otherwise), and
the set reads return `source_ids`, the detail read `sources` too. The set page shows a
Sources panel with a Cite button, the same dialog the municipality page uses. The
research CLI's `set new` / `set edit` now attach what they cite, and a one-off
backfill attached 40 citations across 35 sets from the case files.

`delete_alliance` returned a 500 for any alliance with a city on file:
`alliance_municipality` and `alliance_set` reference it with no ON DELETE and the
delete did not clear them. It now clears both, and removes the alliance's photos
through the media CRUD so their R2 objects go too (the FK cascade only dropped the
rows). Regression tests for both.

---

## 2026-09-30 - A set can be in more than one alliance

`sets.alliance_id` held one alliance, so a set in two blocs lost one: 264 sat in 4Gang
until it was moved to TankMafia, though the map puts AOG and PJC among the 4s, and TMC
is in TMCNE and was one of the five sets that formed RHN.

Migration `81e18d3c4faa` revives `alliance_set`, a join table present since the first
schema that nothing ever wrote (0 rows): `position` added (0 = primary), both foreign
keys now cascade, an index on `set_id`, and every set's current alliance copied in as
its primary (78 rows). `sets.alliance_id` stays as the mirror of position 0, exactly as
`set_gang` did for gangs on 2026-09-28.

- Sets API: `alliance_ids` on create and update (the ordered list; a legacy
  `alliance_id` promotes that one and keeps the rest), `alliance_ids` on reads,
  `alliances` summaries on list rows, detail and territory polygons. The `alliance_id`
  filter matches any membership. Joining an alliance befriends its sets, for each
  newly joined alliance.
- Alliance side: `set_ids` adds or removes only that alliance's rows and re-mirrors the
  set's primary; delete promotes each set's next alliance. Set counts, member counts,
  the alliance's members and incidents, and the "a set in this alliance cannot be its
  enemy" check all read `alliance_set`. The "Through alliances" panel on a set page
  inherits links from every alliance, naming which one; a link between two of the set's
  own alliances is left out.
- UI: the gang chips became a shared `RankedPicker`, used for alliances too; set pages,
  cards and the list show every alliance and filter on any; the map's alliance view and
  sidebar place a set under each of its alliances; the alliance page's Add dialog offers
  any set not already in it, and Remove drops only that alliance.
- CLI: `wiki set edit --alliance` is repeatable and replaces the list.

---

## 2026-09-29 - Neighborhoods know their ZIPs

Neighborhoods sit under their city beside its ZIP districts, not under a ZIP:
Brightmoor is 99.8% inside 48223 but Dexter-Linwood is 70% in 48206 and 29% in 48238,
so no single ZIP can be the parent, and a third level would break the one-level maps,
rollups and breadcrumbs. What was missing was the link between the two layers.

`municipality_overlap` (migration `2d5a7ab2c470`): one row per neighborhood and
district that share ground, with the share of each. `sync_overlaps` computes it from
the two outlines with shapely (new dependency, 2.1.2) for the whole city on every
create or update of a sub-area that changes its parent, kind or outline, so moving a
district also refreshes neighborhoods nobody touched. Overlaps under 2% of the
neighborhood are dropped: they are where the city's neighborhood map and the ZIP map
disagree at an edge. `app/scripts/recompute_overlaps.py` backfilled the four current
links. The neighborhood page reads "in 48206 (70%) and 48238 (29%)"; a district page
has a Neighborhoods panel with how much of the ZIP each covers.

---

## 2026-09-29 - Municipality populations

`population`, `population_year` and `population_source` on `municipality`
(migration `18ab21ff07f0`), filled for 101 rows by the new
`app/scripts/import_populations.py`: every top-level place in the six universes and
Detroit's ZIP districts. Three columns because the figures come from three bodies on
three cycles, and a bare number reads as current forever:

- US cities and townships: Census Population Estimates, Vintage 2025 (July 1, 2025).
  Name overrides for a charter township (a county subdivision, not a place) and
  Augusta's consolidated government (the city "balance").
- ZIP districts and CDPs: ACS 5-year 2020-2024, read from the table-based summary
  file because the Census API now answers keyless requests with "Missing Key".
- Corsican communes: INSEE populations légales 2023 through geo.api.gouv.fr,
  checked against INSEE's PopRef 2023 PDF. Hamlets have no official count.

Dry run by default, idempotent, written through the ORM so the audit log records it.
The municipality page shows a Population tile with the year and the source; the list
shows the figure and sorts by it, places with no figure last.

---

## 2026-09-29 - Municipalities hold what the maps say about a place

A municipality held a name, a parent and a boundary. The community maps say far
more about a place than that: the name it goes by on the street, the region it is
spoken of as part of, its history, its pictures. None of it had anywhere to go.

Migration `01b045fa156b`:

- `kind`: CITY at the top level, and under a city either DISTRICT, a sub-division
  that partitions it (the ZIP codes), or NEIGHBORHOOD, a named area whose outline
  may overlap districts. CHECK: CITY exactly when `parent_id` is null. Existing
  rows backfilled to CITY or DISTRICT by their parent.
- `aliases` (JSONB list), `region`, `description`.
- `municipality_source`, both ends `ON DELETE CASCADE`, written as a complete
  `source_ids` list on POST/PATCH and returned as `sources` on the detail read.
- `media.municipality_id`, with the exactly-one-entity CHECK widened to it.

Rules the CRUD enforces with a 422 rather than an IntegrityError: a kind that
does not fit its parent, a parent that is itself a sub-area (one level only), and
moving a city that holds sub-areas under another city. Changing the parent
without a kind keeps the kind when it still fits and otherwise re-derives it.

Municipalities live in prod whatever the DB mode, so their photos have to as well:
the media router sends `municipality_id` to the prod session, and a by-id
get/patch/delete that misses in the active DB looks for a municipality photo in
prod. Deleting a municipality deletes its photos through the media CRUD, so the
R2 objects go too. Search matches aliases. `GET /geojson` takes `kind`, so a
city's map draws districts or neighborhoods, never both stacked.

UI: the municipality page shows the aliases, a region chip (linking to every place
in the region), an About panel, a photo gallery, the sets anchored to or claiming
the place, and cited sources with an Attach dialog. Sub-areas split into District
and Neighborhood panels, with a layer toggle on the map. The form edits kind,
aliases, region and description, and offers only cities as parents. The incident
page's source dialog became the shared `AttachSourcesDialog`.

Fixed on the way: editing a municipality from the list page seeded the form from
the list row, which carries no boundary, so saving wiped its geometry. The sheet
now loads the full record first. And the detail read never returned
`has_geometry`, so "View on map" never showed.

---

## 2026-09-26 - Alliances get allies and enemies of their own

`set_relationships` has a set at both ends, so a war between two blocs could only
be written from some stand-in set. That is why one alliance, alone among them,
carried a core set named after itself: it was the only place the bloc's enemies
could hang, and its war with a rival bloc had to be split into edges from that set
to the rival's individual sets.

`alliance_relationship` (migration `eccb7ce3c92a`): a FRIEND/ENEMY spell held by an
alliance, whose far side is another alliance or one set, never both (CHECK on
`num_nonnulls`). Alliance pairs are stored once in UUID order, by CHECK rather than
the trigger `set_relationships` uses. One open row per pair by two partial unique
indexes, `until_date` to end a spell as with sets, and `ON DELETE CASCADE` at both
ends. `setrelationshiptype` is reused.

- API: `GET/POST /alliances/{id}/relationships`, `POST .../{rid}/end`,
  `DELETE .../{rid}`, and `GET /sets/{id}/alliance-relationships`, which returns the
  links naming the set plus the ones its alliance holds, marked `via_alliance_*`.
  Refused: the alliance itself, a set inside it, a reserved set, another universe,
  and an open link of the other type (409).
- UI: an "Allies and enemies" panel on the alliance page with an add dialog that
  picks from alliances and sets together, and a read-only "Through alliances" panel
  on the set page. The alliance graph still draws set-to-set edges only.
- Fix: deleting a set with any `set_relationships`, `set_lineage`, `set_source`,
  `set_municipality` or `alliance_set` row failed on a foreign key, because none of
  those cascade. `delete_gang_set` now clears them first.
- Research CLI: `wiki alliance relate`, with `check` support.

That alliance was then remodelled like every other: the core set deleted, its
members left on the alliance directly, its outside edges moved up to the alliance
(two of them merging into one alliance-to-alliance link), its bio, name variants and
municipality folded into the alliance. Its territory polygon had nowhere to go,
since an alliance has none, and survives only in the DELETE row of `audit_log`.

---

## 2026-09-23 - Custody numbers get their own table

A Georgia universe brought numbers the schema had nowhere to put: a GDC ID
(Georgia's MDOC), and the Offender Tracking Number printed on every Georgia
indictment. Adding a column per system had already happened twice (`mdoc_number`,
`bop_register_number`) and would have kept happening for Tennessee, Illinois and
every county jail, each with its own migration and form field, and each holding one
number when jail bookings and OTNs are issued per arrest.

`member_custody_id` (migration `dca974125ded`): one row per number, `system` as
VARCHAR validated by the `CustodySystem` enum so a new system is a code change,
with `source_id`, `photo_media_id` (the mugshot that system served, SET NULL on
delete), `retrieved_at` and `notes`. Unique on `(universe_id, system, number)` for
every system but MDOC, whose column was always deliberately non-unique, and on
`(member_id, system, number)` always. A universe stays its own namespace, as BOP
already was.

**MDOC and BOP are mirrored, not moved.** Their columns stay the write path, since
the OTIS importer, the BOP flow and the research CLI all write there; every member
create or PATCH that touches them syncs the table, and the API refuses a direct
MDOC/BOP write or delete on the table so the two cannot disagree. Backfilled 54
MDOC and 56 BOP rows, exactly the non-null columns. Retiring the columns is the
second step: switch those three writers to the table, then drop them.

`GET/POST/PATCH/DELETE /members/{id}/custody-ids`, `custody_ids` on member detail,
badges on the member page for systems other than MDOC/BOP (which keep their own
badges and lookup links). Research side: `wiki member custody-id` (with `--photo`
to upload a mugshot and link it), a `custody_id` assertion type keyed
`<member> <SYSTEM>:<number>`, and `wiki check` verifying it.

Autogenerate proposed dropping every trigram index, the partial unique indexes on
`member_set` and `set_relationships`, two unique constraints on `gang` and the
CASCADE/SET NULL behaviour of a dozen foreign keys. The migration was written by
hand with none of that. Tested: 8 new backend tests (the mirror tests fail with the
mirror disabled), 222/222 backend, 363/363 research.

First rows: a member's GDC ID with his GDC photo linked, and the OTNs of
four defendants in the Augusta MacArthur Park Apartments indictment.

---

## 2026-08-29 - Set lineage, and emojis a set is known by

Two additions to sets. One was on the roadmap and needed a different shape than
the roadmap proposed; the other is new.

### Set lineage: which set came out of which

`ROADMAP.md` proposed adding directional values (`PARENT_OF`, `CHILD_OF`,
`SPLINTERED_FROM`, ...) to `setrelationshiptype`. That could not work, for two
reasons that only show up in the live schema:

- `set_relationships` carries a `set_a_id < set_b_id` CHECK plus the
  `enforce_set_relationship_ordering` trigger, and `_pair()` in the CRUD sorts
  every pair before insert. Endpoints are therefore stored in UUID order, so
  which set is the parent would have been decided by UUID sort order rather than
  by meaning.
- `uq_set_relationship_current` allows exactly one open row per pair. A splinter
  set now at war with the set it left could record the descent or the beef, never
  both, and that pair is the common case rather than an edge case.

So descent went into its own table, `set_lineage` (`parent_id`, `child_id`,
`kind`, `from_date`, `until_date`), with no ordering constraint. Nothing about
`set_relationships` changed, and a pair can now hold a lineage row and an ENEMY
row at the same time.

`SetLineageKind` is `SPLINTERED_FROM`, `RENAMED_FROM`, `MERGED_FROM` and
`YOUNGER_GENERATION_OF`. Every one reads in a single direction, **child KIND
parent**, so a row is unambiguous whichever column it is read from. `MERGED_FROM`
is the one that reads the other way in ordinary speech ("the old set merged into
the new one") and is named for the child anyway, deliberately: one reading rule
is what stops directional edges being stored backwards. The add dialog shows the
sentence the row will read as before saving, for the same reason.

Adding an edge that would make a set its own ancestor is refused with a 409. The
check is a recursive CTE walking the current lineage upward from the proposed
parent; `UNION` rather than `UNION ALL` means it terminates even on a cycle that
somehow already exists. Self-parenting is caught by `ck_set_lineage_no_self` too,
but is tested in the CRUD first so the caller gets a sentence instead of a 500.

Like a relationship, a descent is a spell: `/end` closes it and keeps it as
history, `DELETE` is for rows entered in error.

### Emojis per set

`sets.emojis`, a JSONB list. The first entry is the badge shown wherever the set
is listed; the rest are the other glyphs the set is known by. The list rather
than a single column is what makes the research direction work: members signal
affiliation with these in bios and display names, so an emoji seen in a handle
needs to resolve back to a set, and a set uses more than one. A GIN index backs
`sets.emojis @> '["<glyph>"]'`.

Validation rejects anything that is *entirely* ASCII. No emoji is, not even the
keycaps (`1<VS16><keycap>` is an ASCII digit plus two non-ASCII code points),
while `BO` and `752` are, and those belong in `name_variants` where they are
searchable as names. Without that rule the column quietly becomes a second alias
field. The frontend applies the same rule next to the input so the error lands on
the field, and splits pasted input by grapheme so a ZWJ sequence survives as one
entry instead of shattering into surrogate halves.

The column uses `JSONB(none_as_null=True)`. Without it, clearing the field stores
the JSON scalar `null` rather than SQL NULL, and `emojis IS NULL` then misses
every set that was ever cleared. This was found by clearing a set during testing
and finding the row still matched `emojis IS NOT NULL`; the test database had 355
such rows and both databases were normalised.

Migration `09fbe10e849f`, applied to prod and test. `squiidwiki_dev` is at
`4ed6ee82caee`, well behind, and is referenced by nothing in `.env`; it was left
alone.

---

## 2026-08-27 - Several accounts per platform, and the OTIS status that never applied

Two bugs found by using the app on real records, both fixed with tests.

### `social_media` could only ever hold one account per platform

`social_media` was typed `Record<string, string>`: one handle for Instagram, one
for Facebook, one for Twitter. A member with four Instagram accounts across the
years could keep exactly one of them, and the form made this worse than it looked.
The submit path rebuilt the whole object from three inputs, so opening the sheet
and saving would silently drop any extra key that had been written by hand.

A platform key now holds either a string or a list, and everything flattens to one
chip per account.

- New `frontend/src/lib/social.ts`: `socialEntries` (flatten), `socialHandle`
  (label), `splitSocial`, and the `SocialMap` type. It sits in `lib/` rather than
  beside the member detail route because `MemberFormSheet` needs the type, and
  that route already imports the sheet, so importing back would be circular.
- **Chips are labelled by handle, not by platform.** Four chips reading
  "Instagram" tell the reader nothing; `@handle` does. Platform moved to the
  tooltip, icon kept. URLs are reduced to their last path segment, with a
  fallback to the host when that segment is a file (`profile.php`).
- The edit form takes comma-separated handles (handles cannot contain a comma),
  normalises each on blur, and previews one link per account.
- **One account stays a bare string.** Only a genuine list becomes an array, so
  existing rows keep their shape and nothing needs migrating.
- The markdown export lists every account.
- No backend change: `social_media` is `dict[str, Any]`, so a list round-trips
  through Pydantic as-is.

### MDOC import left the status UNKNOWN on prisoners

Importing an offender from OTIS filled the legal name, DOB, MDOC number and every
incarceration spell, then left the member's status at UNKNOWN. The import did have
a rule for it, `profile.status === 'Prisoner'`, but OTIS does not return a bare
custody state. It qualifies it in prose after a dash:

```
Prisoner - Released to court on writ (08/13/2026)
```

That man is a prisoner, temporarily at a courthouse. The exact-equality comparison
matched nothing, so the check failed on precisely the records OTIS describes in the
most detail, while a plain `Prisoner` would have worked.

- New `frontend/src/lib/mdoc.ts`: `memberStatusFromMdoc` cuts the qualifier at the
  first dash or bracket and matches case-insensitively.
- **Only a live prisoner maps to LOCKED.** Parole, probation and discharge all mean
  some degree of *out* and each means something different here, so they return null
  and leave the curator's status alone rather than guessing. Nothing is mapped that
  has not actually been seen coming out of OTIS.
- The existing guard is kept: the import only writes a status when the member is
  still UNKNOWN, so it never clobbers a curated one.
- Swept the database for other members hit by this. One candidate, and it was not a
  false negative: OTIS reports that offender as `Discharged`, where declining to
  set a status is the correct behaviour. Every other member carrying an MDOC number
  was already LOCKED, DEAD or FREE.

### Tests

`social.test.ts` (13) and `mdoc.test.ts` (6). Both were checked against the bug
they describe: reintroducing the last-one-wins flatten fails 3 of the social tests,
and restoring the exact-match on `'Prisoner'` fails 2 of the MDOC tests. Expected
values are written from the data and the intended display, never from running the
function under test. The OTIS strings in `mdoc.test.ts` are real responses.

### Also

- `ideas.md` became `docs/ROADMAP.md`, retitled and restated as forward-looking
  only, and `docs/CHANGELOG.md` started. A stray unformatted note in the backlog
  (test Alembic migrations against a throwaway DB before prod) became a real entry.
- Two new roadmap entries fell out of the above: video links as first-class media,
  and showing a member's sources on their page. The second is why bare URLs are
  still sitting in biographies, since moving one into a source row today would make
  it invisible on the page.
- The existing set-lineage entry was rewritten around `PARENT_OF` / `CHILD_OF`.
  `set_relationships` has only `FRIEND` and `ENEMY`, both symmetric, so a set
  descended from another set has nowhere to record it and it ends up in a bio line.

---

## 2026-10-02 - A set's name is derived; the universe is in the URL

**Set names.** `sets.name` and the primary entry of `name_variants` were two
independent columns, and the set form's Save rewrote the name from the variant:
35 sets displayed one thing and would have become another on their next edit (the
four Cash Flow Posse sets all to "CFP", TNO to "Trust No One", No Limit 083 and 087
both to "No Limit"). The name is now computed from the primary variant by
`app/core/set_names.py` on every create and update, mirrored in
`frontend/src/lib/setDisplay.ts` and in the research CLI; a POST or PATCH whose name
disagrees is a 422, a PATCH of `name` alone is refused, and only a real rename
re-slugs. `lead` became one slot or an ordered list (`["initials", "number"]` shows
"CFP 2400"), the form's "Show as" picks slots in order with a live preview, and the
CLI takes `lead=initials+number`. `app.scripts.derive_set_names` aligned 64 prod sets
(and the test DB) with the name each already showed, renaming nothing; names and
slugs were checksummed before and after. A follow-up moved 31 misfiled parts into
their slots (numbers out of `name`, initials out of `name`, expansions merged with
their initials), removed the moderation spelling from HNIC and folded an Illinois
duplicate created by a French import. A combined lead is used only when the
combination is the name a crew goes by, never initials plus their expansion or
their keypad number.

**Universe in the URL.** Slugs are unique within a universe only (301 member slugs
recur across universes), yet `/members/<slug>` resolved against whichever universe
the viewer had selected, so a shared link could open someone else. Every
universe-scoped page moved under `/$universe/` (route files `_app.$universe.*`);
`_app.$universe.tsx` resolves the slug in `beforeLoad` and syncs the store,
`_app.tsx` reconciles the persisted universe with the server on every load (a
renamed universe had kept its old slug, which broke links until this), `/` goes to
the last universe used, and an old `/members/x` link is redirected into the active
universe. Universe slugs that name a page are refused (`RESERVED_UNIVERSE_SLUGS`).
Switching universe keeps the section; recents record their universe and are listed
per universe. Links inside a universe page use `from="/$universe"`; the sidebar,
shortcuts and palette name the universe explicitly.

A half-migrated frontend was briefly live mid-change: `vite build` writes the
`dist/` nginx serves. Use `npm run build` only to ship.
