# privedatabase.wordpress.com

Full harvest of the WordPress site, 2026-08-21. **1,105 pages**, retrieved through the
WordPress.com public REST API in 12 calls. The site is public (`is_private: false`), site ID
`184758954`.

Kept as a sibling of `../detroit/` rather than inside it, because **the site is not only
Detroit**. Roughly 40% of it is Chicago.

**Nothing here has been written to the database.**

## Files

| File | Contents |
|---|---|
| `page-index.md` | **All 1,105 pages** - ID, title, city, kind, **author**, created, modified, size, image count, deceased/incarcerated flags, URL |
| `detroit.md` | 232 Detroit pages: sets with their allies/enemies/members, then people |
| `chicago.md` | 448 Chicago pages - **221 sets** with allies, enemies and member rosters. Kept separate so they cannot leak into Detroit seeding |
| `other-cities.md` | 261 pages: London, Atlanta, New York, Tottenham, Toledo, Louisiana |
| `unclassified.md` | 155 pages the classifier could not place, listed in full rather than guessed |
| `db-sync.md` | **Generated.** What has actually reached the database, and what has not |
| `tools/db_sync.py` | Regenerates `db-sync.md`. Read-only against the DB |
| `tools/extract-chicago.json` | The 156 parsed Chicago set records the sync reconciles against |

232 + 448 + 261 + 155 = 1,096, plus the 9 remaining city-index stubs (Birmingham, Columbus,
Floride, Los Angeles, Montreal, Paris, Quebec, Saint-Louis and one titled `18`), all empty.
`page-index.md` is the authoritative list and reconciles to exactly 1,105.

## Authorship

| Author | Login | Pages |
|---|---|---|
| FCK HEAD$HOT | `frenchsquiidape` | 1,025 |
| irishrugbyman | `irishrugbyman` | 80 |

Both authors are recorded per page in `page-index.md`. Nearly everything dates from 2020
(1,048 pages), with 43 from 2019, 13 from 2021 and 1 from 2018.

## How the city classification works

The site does **not** store a city on each page. It has to be derived, and how confidently
varies. Four passes, strongest first:

**1. Link reachability (highest confidence).** There are 16 city index pages at
`/{{city}}/liste-des-sets/`. Only the Detroit one uses hyperlinks - it links to 40 set pages -
so a breadth-first walk from it produced 156 certain Detroit pages.

**2. Title against city vocabulary.** Every other city index lists its sets as **plain text**,
not links. Matching page titles against those word lists placed a further 459 pages, including
the bulk of Chicago.

**3. Link propagation.** Pages inherit the city of pages they link to, iterated to fixpoint.

**4. Court-roster match (Detroit only).** Any remaining page whose text contains a name from
the court-sourced roster in `../detroit/extraction/` was marked Detroit. This added 27 pages
and is the most trustworthy signal of the four, because the roster comes from federal
indictments rather than from the site itself.

**155 pages resisted all four.** They are listed in full in `unclassified.md` rather than
guessed at. Most are short person pages naming no set and no other person, so there is no edge
to propagate along; 31 are entirely empty. The sample leans Detroit, but leaning is not
knowing.

**A trap worth recording:** page slugs are **not unique on this site**. Sixteen pages share the
slug `liste-des-sets`, one per city, distinguished only by URL path. Two further pages both
occupy `/mob/` (IDs 246 and 7483, both Chicago, one empty). Any tooling that keys on slug will
silently collapse these. **Key on page ID or full URL.** This cost me a broken link graph on
the first pass - the walk from the Detroit index returned exactly one page, because all
sixteen city indexes had collapsed into a single dictionary entry.

## Page structure

**Set pages** use a fixed template that maps directly onto the wiki schema:

```
ALLIÉS: BCG BCB
ENNEMIS: TMCNE Number Streetz
LISTE DES MEMBRES: Duke (décédé), BJ, Hova, Bean, Ed (décédé)...
LISTE DES CORPS DU SET: Duke (CashCrew)
```

`ALLIÉS`/`ENNEMIS` are the bilateral set relationships. `LISTE DES MEMBRES` is set membership.
`(décédé)` is `status = DEAD`. `LISTE DES CORPS DU SET` appears to record kills attributed to
the set, with the victim's own set in parentheses.

**Person pages** are one or two French sentences of fact:

> `Neff` - "Djuan Page a été tué le 24 Juillet 2014."
> `Los` - "Carlos Ross a balancé Ju (TNO), Rez (TNO/YBF) et Lil B (TMC NE) après le meurtre
> de Lil Jay (TMCNE)."

Note the second one: that is a **cooperation/informant relationship**, which the wiki schema
has no field for today. It would currently have to live in member notes.

Across the whole site, **279 pages assert the subject is deceased** and **220 that they are
incarcerated**; 104 carry a parseable date. Those flags are in `page-index.md`.

## Why this source is worth more than its reliability rating suggests

It is self-published research with no citations, so it rates `UNVERIFIED` next to a federal
indictment. But it was checked against the court corpus rather than taken on trust, and it
holds up on the hardest possible test - **it independently reproduces a federal indictment's
alias mapping, and then adds to it.**

Six of the fourteen Playboy Gangster Crips defendants named in the October 2017 indictment
[press-084] have pages here, each giving the same nickname/legal-name pair the indictment
gives, plus a release date the indictment never stated:

| Indictment | Page | Adds |
|---|---|---|
| Jvon Clements, "Toon" | `Toon` (4438) | Earliest release 2033-08-24 |
| Andre Tinsley, "Danger" | `Danger` (4459) | Release 2025-11-24 |
| Deshaun Tisdale, "Havoc" | `Havoc` (4464) | Release 2035-09-04 |
| Recharl Boynton, "Bear" | `Bear` (4500) | Release 2024-04-14, **plus a second alias, "Cee"** |
| Anthony Marshall, "Hitman" | `Hitman` (4505) | **Earliest 2025-05-09, latest 2037-05-09** |
| Darryl Grizzard, "Deezy" | `Deezy` (4512) | Release 2022-06-02 |

Reproducing six alias pairs from a document it never cites is not something a fabricated
source does.

The `Hitman` entry is the informative one: *"sortira le 9 Mai 2025, au plus tôt, ou le 9 Mai
2037, au plus tard"* - an earliest **and** a maximum date, which is the Michigan state
sentencing shape rather than the federal one. That distinction already matters elsewhere in
this project, and it means these dates should populate the earliest/maximum release fields
separately, not a single date.

It does **not** sharpen the court record, and the one place it looked like it did is a
warning. `Neff` dates Djuan Page's killing to **24 July 2014**. The federal orders of 9 May
2018 in *US v. Arnold* (2:15-cr-20652) date the shooting to **14 July 2014** and say Page
"eventually died in August 2014" after weeks in a coma. So the site's single date is neither
the shooting nor the death, and 24 reads like a transposition of 14. Where a date here has no
court counterpart, treat it as a lead, not as a correction.

And it revives dead Facebook links. `social-links.txt` has `kavaughn.clark` tagged "Othaside
aughn"; the `9000` set page lists a member **"Othaside Vaughn."** Same for `atb.mal` → `ATB`,
`bcb.nutty` → `Nutty`, `9000 Richy` → `Richy`. Profiles that are now unreachable become
identifiable people again without touching Facebook.

## Chicago extraction: two tracks, and why

The Chicago set pages carry more structure than Detroit's, and the two halves of a page needed
completely different handling.

**Member blocks were parsed by machine.** `FUSILLADES IMPORTANTES:` / `CORPS:` /
`ASSISTANCE(S):` are newline-separated lists of `Name (Set)` entries, regular enough for a
parser. Yield: **726 members, 3,469 shootings, 586 member-level bodies, 515 assists**, plus
**1,772 set-level bodies** and 618 listed member names.

Each event entry names a target *and* the target's own set, so these are **directed edges
between sets**, not prose. That is the most directly seedable material on the whole site.

**Bios were read, not parsed.** The opening paragraph is irregular French and regex mangled
it, so each of the **156 set bios** was read and normalised by hand. Yield: **335 ally links,
497 enemy links, 24 former alliances.**

| French | Meaning | Mapped to |
|---|---|---|
| `fusionnés avec` | merged with | **allies** |
| `alliés avec`, `cools avec`, `en bonne entente avec` | allied / on good terms | **allies** |
| `ennemis avec`, `ennemis directs avec` | enemies | **enemies**, one list |
| `en guerre contre`, `en embrouille avec` | at war / recent beef | **enemies** |
| `étaient autrefois alliés`, `mais ne le sont plus` | formerly allied | **former_allies** |

Merges fold into allies because the wiki has one ally relationship, not a separate merge
concept. `former_allies` stays split, because collapsing it would assert alliances that
ended - 800 Young Money *was* merged with 051 Young Money and is not any more, with only the
Mickey Cobra OGs still linked across both. Nation names are expanded where the author elided:
"un set de Gangster et Black Disciples" means Gangster **Disciples** and Black Disciples.

### Judgement calls flagged during extraction

Recorded so they can be overridden rather than silently inherited:

- **DIPSET BLVD** (7999) - described as a faction of OTE that OTE later turned against.
  `former_allies` is inferred from "faction du set OTE", never stated outright. PBG is not
  listed as an enemy because the bio never says so directly.
- **GUTTAVILLE** (8002) - "proches de la THF 46" (close to) read as an alliance, though it is
  not one of the standard ally phrasings.
- **HARVEY WORLD** (7099) - "des clashs entre O'Block et le Harvey World" read as enmity;
  "clash" is not standard enemy phrasing here.
- **KILLAWARD 078** (7894) - RMG appears as both a plain enemy and as "RMG (YKN)" ally. Both
  kept, on the assumption the qualifier marks a distinct clique.
- **TAY CITY** (7901) - "devenus BDK" after Lil Jojo's death read as turning against the 600
  specifically, though the bio only states the general anti-Black-Disciples stance.
- **WIIIC CITY / O'BLOCK** (6273) - "Brick City" placed in `former_enemies`; unclear whether
  that should resolve to the present-day 600, which used to carry that name.
- **051 YOUNG MONEY** (286) - the MetBoyz alliance is past tense on this page but current on
  the companion page 7494. Left out of both lists on 286, kept in prose.
- **BLACKMOBB** (283, 7492) - required resolving an ambiguous French pronoun to decide whether
  the NLMB alliance belongs to BlackMobb or to ABK. Settled as ABK, cross-checked against
  ABK's own page.
- **CCG** (8001) - "ennemis avec des sets TVLs" names no specific set; recorded as the generic
  "TVL sets" rather than inventing names.
- **LEXIQUE** (8007) - not a set at all, a glossary entry defining "BACKDOOR".
- **OAK BOYZ NATION / OBN** (7895) - source bio is truncated mid-sentence on the site itself,
  so only the nations could be recovered.

One parser bug worth knowing if you re-run it: `CORPS IMPORTANTS:` is a **set-level** list,
not the trailing member's kills. Treating it as a member section credited 23 bodies to whoever
happened to be listed last on the page.

## Keeping track of what reached the database

`db-sync.md` answers "which of this is actually seeded". It is **generated, never
hand-maintained** - a status table edited by hand drifts from the database within a week and
then quietly lies. Regenerate it after any seeding pass:

```bash
python3 research/privedatabase/tools/db_sync.py --db squiidwiki_prod
```

The script is read-only. It reports three things, and the third is the one that catches
mistakes:

1. **Extracted and seeded** - with the DB slug, and whether bio, gang, members and
   relationships are populated, so partial seeds are visible rather than looking done.
2. **Extracted, not yet seeded** - with nation and relationship counts, so the next batch can
   be picked by value.
3. **In the database with no matching extraction** - hand-entered sets, renamed sets, and
   duplicates. This is where errors surface.

Matching is on normalised names plus `name_variants`, and on the shapes site titles take that
DB names do not: `OAK BOYZ NATION (OBN)` is stored as `OBN`, and `DIPSET/FRONT$TREET` covers
two sets. Without that, the reconciliation reports false orphans in both directions - it
initially flagged OBN, SKD and Front$treet as unmatched when all three were seeded correctly.

Two genuine orphans as of the first run, both expected:

- **3000ST** - predates this work, entered by hand, carries 2 members.
- **Kimo Gang** - seeded deliberately with no bio. It is the one set referenced by 757 that has
  no page anywhere on the site, so there is nothing to extract for it.

## Family ties, and the quote-regex repair (2026-08-22)

The member seed never read kinship. The site states it in prose ("Il est le petit frère de
GBE Capo et l'oncle de T-Slick", "Darius Jones (frère d'Eastside Ivo)"), so Chicago sat at 0
family links on 4,577 members while Detroit and Corsica had theirs. `tools/extract_chicago_family.py`
walks the same pages and sentences as `extract_members_full.py`, pulls every
`<rel> de <name> [du même set | de la <set> | (<set>)]` clause, resolves subject and object to
DB rows (nickname, legal name or alias, narrowed by the set hint, then by the subject's own set,
then by exact-nickname over alias-only matches) and writes through the API, whose member update
mirrors the inverse link on the relative. Result: 267 links on 260 members, 534 directed edges,
every one with its inverse. The full list with its source sentence is committed as
`tools/chicago-family-links.json`; 64 clauses stayed unresolved (relatives who are not members,
"MOB Lil Mike" with no MOB Lil Mike row, two Marcos) and are listed by the dry run. Sister,
mother, daughter and in-law have no key in the wiki's family model and were counted, not written
(8 mentions). Twenty-odd cases were adjudicated by hand in the script's `OVERRIDES` tables with
the reasoning beside each.

Two bugs surfaced on the way:

- `chiparse.ALIAS` opened on `« " “` but only closed on `» " ”`. The site uses opening and
  closing marks interchangeably (`“Wop“, «Dooski»`), so Doowop's aliases came through as one
  string and a quote in later prose could swallow a paragraph (Jusblow). The class is now
  symmetric, aliases are only read from the naming clause before the first verb, and
  `Firstname “Nick” Lastname` yields nickname + legal name instead of a quoted alias.
  `tools/fix_chicago_aliases.py` re-derived the 11 damaged alias rows and 3 quoted nicknames
  from the source sentences. The committed `extract-chicago-people.json` predates this fix and
  was deliberately not regenerated: it is what the database was seeded from, and a regeneration
  also changes set-name casing and record counts for reasons unrelated to the regex.
- Roster parentheticals that held a relation instead of a set ("Big Swirl (frère de
  RondoNumba9 de la 600 ...)") had been seeded as sets. `tools/cleanup_chicago_junk_sets.py`
  deleted the 16 of them, re-attaching the member to the page's set only when the entry sat
  under a MEMBRES roster (under CORPS it is a victim of that set, whose own set is unknown).
  Three junk member rows it could not fix remain and are real victims without a name on the
  site: "Innocente" (x2), "Sa petite amie", "Frère de sa petite amie".

`tools/wikiapi.py` is the shared admin API client + psql helper these scripts use; the
page-to-city owner map and alliance-page list the extractor needs now live in `tools/`
(`wp-owner.json`, `chi-alliance-pages.json`) instead of a session scratchpad.

## Duplicate members, and what actually caused them (2026-08-22)

Two duplicates were merged by hand with `tools/merge_members.py`, which carries
the whole row rather than just the name:

- **KTS Von** absorbed **Von** (both KTS, both DEAD, both listing Dre and Vinnie
  as brothers). Page 7491 states it outright: KTS Von's own sentence says he is
  "le frere de Dre et Vinnie", and Dre's and Vinnie's sentences on the same page
  each say "le frere de ... Von du meme set". The NLMB page had also credited the
  same killing twice, to MaddMaxx (+ EBK Juvie assisting) under "KTS Von" and to
  Choppa under "Von", so the seed built two murders; they are now one murder with
  all three perpetrators. His alias "Big Kutthroat Da Smoker" was added: the old
  parser never reached it.
- **Lil Durk** (Lamron) absorbed **Lil Durk** (OTF). OTF is his own label, not a
  rival set; he now carries both affiliations, Lamron primary.

**Why they existed.** Three separate failures, none of them random:

1. `extract_members_full.py` keys people by `(name, set)`, and one person on two
   set pages is two records by construction. That is deliberate for genuinely
   ambiguous nicknames, and wrong for a man whose name is written with his set's
   tag on one page and without it on another.
2. The agent dedupe pass (`dedupe-verdicts.json`) groups candidates by
   *normalised nickname*, so "KTS Von" and "Von" were never in the same bucket
   and never compared. It did judge `lildurk`, and got it wrong, reading the
   empty OTF row's lack of events as evidence of a second person.
3. `apply_dedupe.py` merges names, aliases, sets and gang onto the keeper and
   then DELETEs the absorbed row - but `delete_member` drops that row's incident
   participations, and nothing repoints the family links other members hold to
   the absorbed id. That cost nothing on the original run, because the same
   commit re-seeded every incident afterwards; **re-running it today would
   silently destroy incident links and family links.** Use
   `tools/merge_members.py` instead: it folds incidents, rewrites every holder's
   family reference, and only then deletes.

**All 15 others of the same shape have now been merged** (2026-08-22), each read
back to the source and recorded in `PAIRS` with the line that settles it:

| kept | absorbed | what settles it |
|---|---|---|
| FBG Brick | Brick | p7484 member sentence, alias `#30`; bare row is event sightings all tagged `(STL/EBT)`, both DEAD |
| FBG Butta | Butta | p7484: "Butta, aussi connu sous le nom de «#26» et de «Tunechi»" - the set page's only Butta |
| FBG Cash | Cash | p7484 sentence; p4755 writes both "Cash (STL/EBT)" and "FBG Cash (STL/EBT)" |
| FBG Young | Young | p7484 sentence, aliases Mello / `#1` |
| FYB DJ | DJ **and 007** | p7486: "FYB DJ ou «007» ... grand frere de LC"; L.C carried both as separate brothers |
| FYB Duke | Duke | p243 Jaro City roster line; kill lists write him "FYB Duke (Jaro City)" |
| FYB J Mane | J Mane | p7486 sentence; the bare name appears only on the p243 roster |
| FYB Mattana | Mattana | same shape as J Mane |
| GBE Capo | Capo | p6278 sentence (alias Drama, deceased); p245/p7485 write "Capo (Front$treet)" |
| OTF Ikey | Ikey | both off the SAME alphabetical roster (p1151): "Ikey" in the I's, "OTF Ikey" in the O's |
| OTF Pat | Pat | the same shooting from both sides: p7487 "FBG Brick tire plus de 15 fois sur Pat" / p7484 "Pat (NLMB, il lui a tire dessus 15 fois mais Pat a survecu)" |
| OTF Tay | Tay | p6536's kill list holds both two lines apart; Lowelife's own body list (p7944) has exactly one Tay |
| PBG Spazz | Spazz | bare row is the p7488 PBG/TFG member sentence; only one Spazz in the source |
| TFG Bigz | Bigz | the two rows already carried the **same brother** - only happens when one man was split |
| ABM Tay | Tay | no Jaro City page names a bare Tay; that row's set is an artifact of "Tay (ABM)" on p7908 |

Not merged, deliberately: the Lowelife Ikey, the Killaward 078 Capo, CapFck12
(whose alias is "Capo"), 007 of THF 46, and the dead Pats on CCG, Smashville,
TaeTown and South End - all different men on different sets.

Result: 16 rows absorbed, 4,558 members, family edges down to 532 with **0
dangling ids, 0 missing inverses and 0 orphaned incidents**. Every absorbed
nickname survives as an alias, so a search for "Brick" or "007" still finds the
man. Re-running the query above now returns nothing.

### The block-leak bug: 171 incidents repaired (2026-08-22)

On a set page the extractor attributes each CORPS / ASSISTANCE / FUSILLADES block
to the member sentence above it. When `parse_member` could not produce a usable
name, `good_name` rejected it and `current` was never advanced - so the **previous**
member absorbed the next man's entire kill list.

The sentences that broke all share one shape: `<Name> aussi connu sous le nom de
«X» est un ...` with no comma before "aussi", sometimes with no "de" before the
quote, sometimes with a dangling "ou". Three `chiparse` fixes cover them (plus a
regression I introduced on 2026-08-21 by requiring that "de", which cost BiteDown
his block).

What it had done, on the two pages the user spotted:

- **Gullie Gibson** (p7488, PBG/TFG) - his fiche gives him exactly two bodies,
  Slutty and Pig. The database credited him with **61 shootings, 5 assists and 11
  kills**: 75 event lines belonging to **Lil $hawn** (41), **Lil Dutty** (13),
  **Kemo** (13) and **Mosey** (8), the four men whose sentences follow his.
- **Bad Luck** (p7954, LOC City) - absorbed 13 lines belonging to **DB**
  ("DB aussi connu sous le nom de «Derry»").
- **KTS Dre** (p7491) - absorbed KTS Von's six bodies and sixteen shootings, which
  is why KTS Von showed 0 kills.

`tools/fix_misattributed_incidents.py` re-derives the perpetrators for every
affected victim from the corrected extraction and PATCHes only the incidents whose
participant list actually changes. It never creates or deletes an incident, so the
hand-made T-Slick murder and all set-level claims survive untouched. **171
incidents repaired**; Gullie Gibson is back to 2 kills, KTS Von has his 6.

Four men had to be created first: the old parse never produced a row for them, so
the seed could not resolve their name and dropped every event naming them -
**Kemo** (PBG/TFG), **DB** (LOC City), **No Good Loso** (Out7aw City) and **The God
Father** (the No Luv City *alliance*, not a set). Two shared names with no set hint
are pinned by page in `PERP_OVERRIDES` (Zo of Landlord COV, Tyto of p1772).

**What this pass cannot reach.** It only moves attributions between rows that
already exist inside an incident that already exists. It cannot recover an event
whose victim has no member row (Lil Harvey), nor one seeded under the wrong type
(The God Father's kill of Anthony sits as a SHOOTING, the corrected extraction
calls it a body). Those need a re-seed of incidents, which would also destroy every
hand-made record, so it remains a deliberate decision rather than a cleanup.

### The two LOC City sets were labelled the wrong way round

The site carries two sets it explicitly says not to confuse: p7954 "LOC CITY"
(312 lines, "un set de Gangster et de Black Disciples a Rogers Park", also known
as 1212, MMG, Jeffery Boyz, Get Rich, Blake Block, Montana Gang, Keno World,
Munchie Gang, Lawless) and p450 / p7991 "LOC CITY (BotY)" in Back of the Yards,
"a ne pas confondre avec le LOC City dans le Nord de Chicago".

Both titles reduce to the same comparison key `loccity` - `candidates()` strips
the parenthetical - so every unqualified sighting went to whichever row
registered that key first. The result was inverted: the row **named** "LOC City
(Back of the Yards)" held the 105 members and 15 relationships that come off the
Rogers Park page, while "LOC City (Rogers Park)" held two Rogers Park men and the
Rogers Park name variants.

The bios, the name variants and the set relationships were all swapped with
the labels. `tools/fix_loc_city.py` relabels each row to match the content it
actually holds,
drops the parenthetical from both names (**LOC City**, 100 members; **LOC City
BotY**, 7) and moves the nine members that sat on the wrong one. Four names -
ChiefLocMoney, Heado, Mon and Rico - appear on *both* source lists and were left
on LOC City: splitting them needs evidence that they are two different men, and
the source does not give it. It also hands each row its own bio and the five
relationships the BotY page states (DamenVille and W.B 057 as allies, JackBoys,
LordsVille and MurdaField as direct enemies). PottBlock, SedVille, 5th Ward Life
and Jaro City are named by neither LOC City page and were left where they sat.

No set name in the universe carries a parenthetical any more. Any future set whose
title differs from another only by a parenthetical will collide the same way -
`candidates()` is the place to look.

## Biographies, and the rule that makes them worth having (2026-08-22)

The seed never wrote one: 4,563 of 4,565 members were blank while 454 had a full
sentence about themselves in the French source. Ten Haiku agents drafted one each
from `tools/bio-instructions.md`, under a single rule - **say only what no other
column holds** - and 266 were written.

That rule is the whole point. A biography that repeats the set, the nation, the
family and the status is noise: those are columns, they render on the page
already, and prose duplicating them rots the moment one is corrected. What earns
its place is what has nowhere else to live:

> **Booka** - One of the four founding members of the 600. Close to Lil Durk.
> **Stello** - An OG of Brick City and one of its last active members. His death
> was one of the reasons for the 600's decline.

The distinction to hold on to is **state versus circumstance**. "He is
incarcerated" is a column and is banned; "took the charges for his members" is a
fact no column holds. Same sentence, opposite verdicts.

182 drafts came back empty, and that is the correct answer rather than a failure:
strip the columns out of "X est un Black Disciple. Il est le frere de Y. Il est
actuellement incarcere." and nothing remains.

`verify_bios.py` checks prose the two ways prose can be checked - every
capitalised token must appear in the source sentence, so an invented associate or
song title fails before reaching the database, and no column may be restated. 433
of 454 passed untouched. The 21 flagged were read by hand and were almost all
false positives of the checks themselves: "Fridays" as a plural, "Millie's" as a
possessive, and a bio correctly stating that B.A. is jailed for a murder Mack
committed, which tripped the status test by naming another man's imprisonment.

A rerun of batch 8, launched while the first was still in flight, is worth
recording: it produced four more non-empty bios than the original, and all four
were **worse** - "Also known as PeeWee", "Also known as 007". An alias is a
column. The first agent had correctly returned empty. More output is not better
output, and the rule is what tells them apart.

## The seeds are destructive; the replacements are not (2026-08-22)

`reseed_chicago_members.py` deletes every member and rebuilds; `seed_chicago_incidents.py`
wipes every incident and rebuilds. That was correct on a virgin universe. It is
now the reason a parser fix looked like it could not be applied: re-running either
would throw away the merges, the family links, the hand-written biographies, the
T-Slick murder and every manual edit.

The answer is not "re-seed or live with it". It is to **reconcile instead of
wipe** - resolve what the extraction says against what the database holds, write
only the difference, never delete. Then a parser fix can be applied at any time.

- `tools/sync_chicago_members.py` is the idempotent replacement for the member
  reseed. It matches every extracted person against the DB **by nickname or
  alias**, narrowed by set, and POSTs only the genuinely absent. Matching on
  aliases is what stops it re-creating the duplicates merged by hand: "Brick"
  survives as an alias of FBG Brick, so the bare record matches the merged row.
  It creates only names the universe does not hold **anywhere**; a name already
  borne by a row on another set is exactly the shape that produced the tag-prefix
  duplicates, so it is printed for adjudication and never created. First run:
  3 created (Lil Harvey, Folly Fatz, HellBoy Rell), 11 listed for review, 4,968
  already present. Second run: 0.
- `tools/sync_chicago_incidents.py` is the incident equivalent. It imports
  `seed_chicago_incidents.py` (its top half is pure computation) to drive the
  **same grouping and the same `resolve_person`**, then writes only the
  difference: PATCH a group whose incident exists and differs, POST a group with
  no incident, and leave anything the extraction does not know about alone. First
  run: 46 corrected, 20 created, 6 hand-made incidents untouched (the T-Slick
  murder among them), 6 victims flagged as ambiguous. Second run: 0 and 0.

  Using the seed's resolver is what made this safe. The local resolver in
  `fix_misattributed_incidents.py` had estimated 236 missing groups; the seed's,
  which scopes names by page, alliance and person-page subject set, found **20**.
  Creating 236 incidents would have duplicated 200-odd that already existed under
  a differently-resolved victim.

  With that, the two gaps documented as unreachable are closed: The God Father
  has his kills of Lil Harvey and Anthony, and Lil Harvey has a fiche.

### "la fusillade de sa mort" was read as the target's death

`DEADP` matches "mort", so the annotation `Wooski (STL.EBT, la fusillade de sa
mort)` on page 6273 flagged **Wooski** as dead. It sits under **HK**'s FUSILLADES
list, and "sa" is HK - whose own sentence says "Il est decede", and whom Wooski's
CORPS list names as one of his three bodies. The site puts fatalities under CORPS,
never under FUSILLADES, so the annotation can only be about the shooter.

Only three lines in the whole source contain "de sa mort", two of them these. The
pattern now refuses to fire on "sa mort", and Wooski and Skinny - the two men it
had killed off - are alive again (Skinny is LOCKED: "il est actuellement
incarcere pour une fusillade").

`sync_chicago_members.py` grew a status audit for this class of error, because a
member's status is written once at creation and never revisited. It corrects only
the one safe direction - the row says DEAD, no incident kills them, and the source
does not say they died - and matches on **aliases** as well as the name, or
"Edwin « Eazy Tarentino » Cook (decede)" reads as nobody having died. Deaths the
source states in a set's prose rather than an entry annotation cannot be seen this
way and are listed in `KEEP_DEAD` (Jaro: "jusqu'a que «Jaro» ne soit tue").

### A variant row holds a name, its acronym and its number together

`name_variants` is not a list of strings. Each row has three slots - `name`,
`initials`, `number` - and a `lead` saying which one heads the display, so one row
can carry "Never Leave My Brothers", "NLMB" and a number at once and render as
`NLMB (Never Leave My Brothers)`.

`backfill_set_name_variants.py` filled the slots but split each stored variant on
its own and never joined rows, so NLMB kept an initials-only row beside a
name-only row saying the same thing - five entries in the edit form for three
names. `merge_set_variants.py` joins them where the acronym is demonstrably the
initials of the name: MOB with "Mind On Business", THF with "Trigga Happy Family",
NLMB with "Never Leave My Brothers". The acronym keeps leading, since the set is
filed under it.

Numbers stay separate on purpose. "1212", "8X13", "0725" and "500" sit beside
names on LOC City, 8X13, SackBoyz and No Limit 087, but they are numeric
**aliases** - names in their own right - not qualifiers of the name next to them.
Folding one in would invent a set number the source never states.

### A name must never restate its own set

"KTS Von" on the set KTS says KTS twice. The rule is that a member's name carries
only what the set does not, so he is **Von**, filed under KTS. Six members broke
it and were renamed - Bigz, Spazz, Tay, Bandz - and applying the rule exposed two
duplicates that were one man written both ways, "PBG Kemo" beside "Kemo" and
"O'Block Ocho" beside "Ocho".

The rule has a cost that has to be paid in the resolvers, not worked around in
the data: **the source still writes the long form.** Every page that mentions Von
calls him "KTS Von". So resolution has to bridge both directions:

- the row is tagged and the source is bare ("PBG Kemo" in the database, "Kemo" on
  the page) - `tagged_idx` in `sync_chicago_members.py`;
- the row is bare and the source is tagged ("Von" in the database, "KTS Von" on
  the page) - strip the leading tag, resolve it as a set, and look for the bare
  name inside it, in both `sync_chicago_members.py` and the seed's
  `resolve_person`.

Without the second half, removing "KTS Von" from his aliases - which is the right
thing to do under the rule - made the reconcilers want to strip Dre and Von from
30 incidents and re-create them as new members. Aliases are a crutch here, not the
mechanism; the resolvers must understand the naming rule directly.

### Roster parentheticals that were never sets

Thirteen sets existed only because the seed read "Name (anything)" as "Name, of
the set 'anything'": a charge ("condamne a 50 ans"), an arrest ("arrete en 2017"),
an age ("enfant de 9 ans" - Tyshawn Lee, the nine-year-old killed in 2015), a
slur, a role ("rappeuse", "tireur actif"), and a qualifier trailing a real set
name ("PMBMB affiliee"). `cleanup_chicago_junk_sets.py` covers all of them now.

Members are re-attached only from a MEMBRES roster: under CORPS or ASSISTANCE the
entry is a victim or a target, whose own set the page never states, so they are
left set-less rather than given a set they may not belong to. Searching the rest of the
source afterwards placed two of them on pages other than the one that stranded
them: **SG Ali** on Only The End (the rapper list writes "SG Ali (OTE)", a set tag
rather than an annotation) and **Crispin** on Death Trap (p7984 calls him
"Affilie Death Trap" in all three of its sections).

Seven the source genuinely never places, and they stay set-less: Tyshawn Lee,
named only as the nine-year-old victim; Lil Chello, Mikal, Tito and Lil Keith,
named only under Brickyard's ASSISTANCE as targets carrying an arrest note;
**Femme**, which is not a name at all but the French for "woman", an unnamed
female victim in the Wild 100's; and PC.

PC is left open rather than guessed. Two rows carry the name - one on No Limit
083, DEAD, from that page's MEMBRES roster ("PC (decede)"), and one set-less with
a single incident, from Killaward's FUSILLADES where PC is a target and no set is
stated. They may well be one man, since no other PC in the source has a set, but
nothing positively links them and merging on a two-letter nickname is the shape of
mistake that cost most of a day. Four were attached
that way (CK and Snake to No Limit 087, Boss Kat to GME/EBE, Mook Da Murderer to
FreeSmoke); the rest stay unattached, which is what the source supports.

### A resolution trap worth knowing

`candidates()` returns an **unordered set**, and a parenthetical title yields both
the full key and the bare one - "LOC CITY (BotY)" produces `loccityboty` *and*
`loccity`. Iterating that set directly sends such a title to either row at random.
`seed_chicago_incidents.py` already sorted by length descending; the scripts added
here did not, and now do. The same trap bit the LOC City fix itself: keeping "LOC
CITY (BotY)" as a name variant re-registered the bare `loccity` key on the wrong
row and re-created the collision the fix had just undone.

Eight resolution keys are still claimed by more than one set and deserve a look:
`abm` (Jaro City / Lil4Mobb), `bbgterrordome`, `cranktown`, `ebt`, `newmoney080`,
`stl`, `stlebt` (MurderVille / STL-EBT) and `tytoland`.

## Before seeding any of this

- **It is `UNVERIFIED`.** Where a fact here also appears in `../detroit/extraction/`, cite the
  court source and treat this as corroboration. Where it appears only here, mark it as such.
- **The content is French.** `décédé` = deceased, `incarcéré` = incarcerated, `a été tué` =
  was killed, `a balancé` = informed on, `sortira` = will be released, `au plus tôt` /
  `au plus tard` = earliest / latest.
- **Do not seed the unclassified 155 into Detroit.** Read them first.
- **Chicago must stay out.** It is 448 pages and would quietly double the universe with the
  wrong city's gangs.
- Several pages carry images. Those are not harvested here - that is a separate decision with
  storage cost attached.

## Reproducing the harvest

```bash
curl "https://public-api.wordpress.com/rest/v1.1/sites/184758954/posts/?type=page&status=publish&number=100&page=N"
```

`found` in the response gives the total. No authentication needed for published pages.

### Completeness, checked against the site's own dashboard

The wp-admin page list reports **1,109 pages: 1,107 published + 2 drafts**. This harvest holds
**1,105 published**, and the API's own `found` count agrees at 1,105.

- **The 2 drafts are accounted for and worthless.** Both are templates authored by
  `irishrugbyman`: "Mise en Page – Set" (the set-page layout) and "Fiches Prison". The set
  template is already reverse-engineered from the 22 pages that use it, documented above.
- **2 published pages remain unexplained.** They exist in the dashboard and not in the public
  API. Password protection is the likely cause - such pages keep `published` status but are
  excluded from public API listings - but this is unverified. It is 0.2% of the site and was
  not chased further.

A WXR export (`Settings → Export`) would resolve it, but **requires Administrator**. The
account used here has Editor rights only; the site owner is `FCK HEAD$HOT`
(`frenchsquiidape`), who authored 1,025 of the pages.

Note for anyone re-running this: an unauthenticated `status=draft` query returns 0 whether or
not drafts exist, because the public API cannot see them at all. That zero is not evidence.
