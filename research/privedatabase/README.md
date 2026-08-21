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

It also sharpens the court record. `Neff` dates Djuan Page's killing to **24 July 2014**; the
Detroit News gave only "July 2014" for the death that formed the anti-Seven-Mile-Bloods
alliance.

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
