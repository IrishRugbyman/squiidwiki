# SquiidWiki - Changelog

What was built, what was tried, and what it was for. One dated entry per session
or shipped change. Forward-looking work lives in `ROADMAP.md`; when something
here ships, its line comes out of that file.

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
