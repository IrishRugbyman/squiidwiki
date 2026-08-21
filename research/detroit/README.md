# Detroit research

Raw material for the Detroit universe in SquiidWiki. Nothing here is wiki data itself -
it's source material to extract from, structured by how ready it is to use.

```
sources/       Bookmark exports - citations to feed the Source entity
raw/           Unprocessed copy-paste dumps - need triage before they're usable
raw/fetched/   Full text retrieved from the sources/ URLs on 2026-08-21 (see below)
extraction/    Curated notes, ready (or close to ready) to seed Set/Alliance/Member records
```

## sources/

All four extracted from a Chrome bookmarks export (`favoris_02_08_2026.html`) on 2026-08-02.
Tab-separated, one row per bookmark. Maps onto the wiki's `Source` entity (citation +
reliability rating) except `mdoc-records.txt`, which is offender lookups rather than
citations.

- `legal-sources.txt` - 56 court opinions, federal indictments, DOJ releases, PDFs
- `press-sources.txt` - 91 news articles across 41 outlets
- `social-links.txt` - 105 Facebook/Instagram/Twitter profile and search links (open
  logged-in in a browser - all three platforms 403 non-browser clients)
- `mdoc-records.txt` - 405 Michigan DOC (OTIS) offender records by MDOC number; lookup
  URL pattern is in the file header. OTIS also 403s non-browser clients.

## raw/

Copy-pasted straight from wherever they were found, with no processing since. Origin and
capture date weren't recorded - each file's header says what's known and what to verify.

- `sets.txt` - 412-entry numbered master list: active sets, a defunct-sets section, and
  non-gang entries (housing projects, cemeteries, funeral homes, closed schools) the
  source apparently groups in with sets for territorial context.
- `murders.txt` - 215-entry memorial list of deceased individuals with affiliation tags
  where known.

Both need to be split up and cross-referenced against existing wiki entities before
anything in them turns into a Set, Member, or Incident record.

## raw/fetched/

Full text of every reachable URL in `sources/`, retrieved 2026-08-21 with a headless browser.
**97 of 147 documents** yielded usable text (1.4 MB). Filenames are the source IDs used
throughout `extraction/`.

The 50 that failed are not dead links, they are refusals: `documentcloud.org`,
`law.justia.com`, `casetext.com`, `casemine.com`, `leagle.com`, `mlive.com` and
`cases.justia.com` sit behind Cloudflare and return 403 to this server's datacenter IP. A
browser on a residential connection reaches them normally, so **these are worth opening by
hand** - the DocumentCloud set in particular holds the Seven Mile Bloods indictment and
chronology and two plea deals. Two federal PDFs downloaded but are scanned images needing OCR.

`raw/fetched/chamspage/` holds eleven years of Detroit homicide victim lists (2003-2013)
plus the blog's statistics pages.

## extraction/

- `bloods-sets-extraction.md` - curated extraction from DetroitStreetGangs.com's Detroit
  Bloods overview page: 9 main sets, 3 alliances, ~40+ sub-cliques, with territory and
  status notes, ready to drive Set/Alliance creation. Covers Bloods only - Crips, GDs,
  Vice Lords etc. seen in `raw/sets.txt` aren't extracted yet.
- `source-index.md` - all 147 citations with fetch result and a proposed `SourceReliability`
  rating (HIGH for court records and federal releases, down to UNVERIFIED for forums).
- `federal-cases.md` - twelve gang prosecutions, case by case, with every named defendant,
  alias, sentence, and an explicit **charged / pleaded / convicted / acquitted** column.
- `people.md` - consolidated roster of every named individual, grouped by set, with a
  `MemberStatus` enum mapping. Separates gang members from victims and from officials.
- `sets.md` - sets and gangs with territory, aliases, rivals and internal rank vocabulary.
  **Read its "Naming caution" section before seeding anything** - four distinct traps there
  will corrupt the Set table (gangs rename themselves; "Band" is three different gangs).
- `incidents.md` - dated incident timeline with FuzzyDate precision marked per row.
- `homicides/` - 4,019 Detroit homicide victims, 2003-2013, one markdown file per year.

Nothing in `extraction/` has been written to the database.

## Workflow

1. Pull structured facts out of `raw/` and `sources/` into a curated doc under
   `extraction/`, following the shape of `bloods-sets-extraction.md`.
2. Use the extraction doc to drive `POST`s (or a seed script) against the backend -
   Sets and Alliances first, then Members, then Incidents linking them.
3. Attach the matching rows from `sources/` to each entity as citations.
