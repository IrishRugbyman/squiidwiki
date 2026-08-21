# Detroit homicide victim lists, 2003-2013

Parsed 2026-08-21 from **chamspage.blogspot.com**, a personal blog that maintained
year-by-year homicide victim lists for Detroit (and separately for Baltimore and
Philadelphia, which are not included here).

**Reliability: `UNVERIFIED`.** This is a blog, not a medical examiner or police release. It
is included because it is the only continuous multi-year victim index in this corpus, and
because it survives a spot check - see "Does it hold up" below.

**Nothing here has been written to the database.**

## Coverage

| Year | Victims | Unidentified | With notes | Ages given | Mean age | Under 18 |
|---|---|---|---|---|---|---|
| [2003](2003.md) | 403 | 0 | 0 | 398 | 30.9 | 32 |
| [2004](2004.md) | 409 | 0 | 0 | 404 | 32.9 | 33 |
| [2005](2005.md) | 373 | 3 | 0 | 367 | 31.9 | 32 |
| [2006](2006.md) | 406 | 1 | 0 | 404 | 32.5 | 30 |
| [2007](2007.md) | 391 | 0 | 0 | 389 | 32.9 | 35 |
| [2008](2008.md) | 339 | 0 | 0 | 338 | 31.0 | 30 |
| [2009](2009.md) | 361 | 2 | 0 | 359 | 33.4 | 24 |
| [2010](2010.md) | 308 | 0 | 0 | 308 | 33.0 | 18 |
| [2011](2011.md) | 344 | 0 | 0 | 344 | 32.3 | 20 |
| [2012](2012.md) | 404 | 14 | 159 | 392 | 32.3 | 28 |
| [2013](2013.md) | 281 | 205 | 274 | 217 | 35.1 | 10 |
| **Total** | **4019** | 225 | 433 | | | 292 |

Eleven consecutive years, no gaps. Each year is a separate file in this directory.

## Columns

- **Date** - as published, converted to ISO. Maps to a `FuzzyDate` at `YMD` precision.
- **Name** - `Unidentified Male` / `John Doe` entries are left as published. Names published
  in all caps (2003-2011) have been title-cased; the 2012-2013 lists were already mixed case.
- **Age** - as published. Some entries give a decade (`20s`, `50s`) rather than a number;
  those are preserved verbatim and excluded from the age statistics above.
- **Block** - block-level address as published. `R/O` means rear of. Entries with a slash
  (`MEYERS/SCHOOLCRAFT`) are intersections, not street numbers.
- **Notes** - present only for 2012 and 2013, where the blog began recording circumstances
  and, in some cases, the name of a charged suspect. **433 rows carry a note**, and these are
  the most immediately useful records in the set.

## Does it hold up

One hard cross-check was available, and it passed. The 2011-08-08 drive-by killing of
**Kionte Atkins** is documented in a federal RICO plea by Rollin 60s founder Jerome Hamilton
[press-067]. Entry 215 of the 2011 list records **Kiontae Atkins**, 34, at 8208 Carlin, on
exactly that date. Reaching an independently court-verified killing from this blog, on an
exact date match, means the list is not invented.

Note the spelling divergence, **Kiontae** vs **Kionte**. Expect that generally: match on
date plus approximate name, never on name alone.

## The count discrepancy - do not ignore this

The parsed 2012 list holds **404 victims**. The Justice Department, announcing the Phantom
OMC sentences, put Detroit's 2012 homicide count at **386** [legal-033].

That is an 18-victim gap and this document does not resolve it. Plausible explanations
include justifiable homicides counted here but excluded from the DOJ figure, deaths
reclassified after publication, or simple blog error. **No source in this corpus settles it.**
Treat these counts as a victim index, not as a homicide statistic, and cite DOJ or DPD for
any figure that needs to be defensible.

## Seeding guidance

If these are ever loaded, they are `Incident` records of type `MURDER` with a `FuzzyDate` at
`YMD` precision and **no participants attached**. A victim name on a blog list does not
establish a `Member`, and it certainly does not establish gang affiliation - the great
majority of these 4,019 deaths have no gang connection at all.

The 2012-2013 notes are the exception worth mining by hand: entries such as "Killed for his
leather jacket. Donald Taylor, charged" name a suspect and a motive, which is enough to
justify a real record once the underlying case is confirmed against a court source.

## Source pages

| Year | URL |
|---|---|
| 2003 | https://chamspage.blogspot.com/2011/11/2003-detroit-homicidemurder-victim-list.html |
| 2004 | https://chamspage.blogspot.com/2011/11/this-is-list-of-detroit-homicide.html |
| 2005 | https://chamspage.blogspot.com/2011/11/2005-detroit-homicidemurder-victim-list.html |
| 2006 | https://chamspage.blogspot.com/2011/11/2006-detroit-homicidemurder-victim-list.html |
| 2007 | https://chamspage.blogspot.com/2011/11/2007-detroit-homicidemurder-list.html |
| 2008 | https://chamspage.blogspot.com/2011/11/2008-detroit-homicidesmurder-list.html |
| 2009 | https://chamspage.blogspot.com/2011/11/2009-detroit-homicidesmurders-list.html |
| 2010 | https://chamspage.blogspot.com/2011/11/2010-detroit-homicidemurder-list.html |
| 2011 | https://chamspage.blogspot.com/2012/02/2011-detroit-homicidemurder-victim-list.html |
| 2012 | https://chamspage.blogspot.com/2012/05/2012-detroit-homicidesmurders-partial.html |
| 2013 | https://chamspage.blogspot.com/2013/01/2013-detroit-homicides.html |

The blog's own statistics posts (age ranges, gender, manner of death, homicides by day of
month) were fetched but are **charts rendered as images**, so no data was recoverable from
them. The 2012 page is titled "partial" by its author, and the 2013 list stops in September.
