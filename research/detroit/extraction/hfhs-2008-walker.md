# Henry Ford High School shooting, 16 October 2008 - BCB v FOE Life

Christopher Walker, 16, FOE Life, killed outside Henry Ford High School in a shooting by
BCB. Three others wounded. This is the killing behind the street account that "J-Nutty
took life at about 15 for killing FOE Life Chris".

**Primary source, and it is a good one.** *People v Morton*, No. 294823, and *People v
Bell*, No. 295573 (Mich Ct App, 24 May 2012, unpublished, per curiam), consolidated on
appeal from Wayne Circuit Court **LC No. 08-018563-FC**. Panel: Servitto, P.J., Cavanagh,
Fort Hood. Retrieved 2026-08-25 from courts.michigan.gov; unlike most Detroit legal
sources this one is **not** behind a Cloudflare wall and downloads to this server fine:

    https://www.courts.michigan.gov/4a349e/siteassets/case-documents/uploads/opinions/final/coa/20120524_c294823_41_294823.opn.pdf

Corroborated by the local homicide list, `homicides/2008.md` line 273:
`2008-10-16 | Christopher Walker | 16 | Evergreen Ave & Pembroke Ave`.

Rating this **HIGH**. A state appellate opinion reciting trial evidence.

## What the opinion settles outright

**BCB is `BCB-AL`, and it stands for "Burgess, Chapel, Blackstone Across Lahser".** From
footnote 3, verbatim:

> Evidence indicated that Morton was a member of BCB-AL (Burgess, Chapel, Blackstone
> Across Lahser). The murder victim, Christopher Walker, was acknowledged to be a member
> of the FOE-Life gang (Family Over Everything).

Three things follow, and each one corrects the database:

1. **BCB is a street-named northwest Detroit set** - Burgess, Chapel and Blackstone are
   streets, taken together "across Lahser". It is not a Chicago nation. The wiki currently
   tags all ten BCB members with the gang **`Unknown Vice Lords`**, which this makes almost
   certainly wrong and consistent with the `33ac22d53ce8` backfill. See the standing note
   in `leads.md`.
2. **FOE Life is real, distinct, and rival to BCB.** It is not PBF. The Band Crew RICO
   indictment lists PBF and FOE Life as two separate component sets, and this opinion has
   FOE Life as BCB's opposition three years before Band Crew was formed.
3. **The expansion differs slightly by source.** The court says "Family Over Everything";
   the federal indictment says "Family Over Everything Love is Forever". Record the court's
   as the alias and the indictment's as the full name, or hold both.

## The incident

- **Date** 16 October 2008 (`YMD`, exact).
- **Place** outside Henry Ford High School, Detroit. The homicide list puts the body at
  **Evergreen Ave & Pembroke Ave**, which is the school's corner - better than "outside
  HFHS" for the incident row, and precise enough to geocode.
- **Killed** Christopher Walker, 16, FOE Life.
- **Wounded** Kejuana McCants, Maleek Slater, Leon Merriweather.
- **Weapons** at least two, "an assault rifle and a handgun".
- **Sequence**, as the evidence was recited: Morton and Walker, known members of rival
  gangs, had a **fistfight earlier that day**, no weapons seen. Between the fight and the
  shooting Morton was on his phone and students were saying "time for some gun play".
  Brandy Patterson saw Morton with weapons outside the school just before. Maleek Slater
  saw Morton firing in his direction. Janay Greer saw Morton shoot toward a group of
  students. Jonathan Kinchen told police he saw **Morton exit a black Mazda and shoot into
  the crowd** - later recanted. Brantley identified Morton as the shooter. Morton's
  gunshot primer residue test that evening came back positive.
- **Motive** text messages show a plan to gather BCB-AL members at the school to take on
  FOE Life "in memory of or in retribution for a deceased friend, **To-To**". Afterwards
  Morton texted that "Word around that I was the shooter."

## People

| Name | Role | Set | Outcome |
|---|---|---|---|
| Christopher Walker, 16 | victim | FOE Life | killed |
| Kejuana McCants | victim | | injured |
| Maleek Slater | victim | | injured, testified |
| Leon Merriweather | victim | | injured |
| William Morton | shooter | BCB-AL | 1st-degree murder, 3x assault w/intent to murder, felony-firearm. Affirmed. |
| Devon Bell a/k/a Devon Cheo Bell | participant | | 2nd-degree murder, felony-firearm. Affirmed. |
| Derryck Brantley | charged | | **acquitted of all charges** |
| "To-To" | not present | BCB-AL side | deceased before this; the stated reason for it |

Morton was tried with Bell and Brantley but had a **separate jury**; Bell and Brantley
shared one.

## MDOC 744816, William Morton

Pulled from OTIS 2026-08-25 (reachable from this box through the configured proxy, so the
old Helsinki block no longer applies). **J-Nutty is William Morton**, confirmed.

- **Date of birth 8 January 1993**, so he was **15** on 16 October 2008.
- Five active sentences, court file **08018563-03-FC**, all dated **15 October 2009**:
  first-degree premeditated murder (MCL 750.316A) **LIFE to LIFE**; three counts of
  assault with intent to commit murder (MCL 750.83) 15 to 25 years each, one per wounded
  victim; felony firearm (MCL 750.227BA) 2 years. No earliest release date and no
  discharge date, as a life sentence gives neither.
- Saginaw Correctional Facility, security level II. SID 3534045J. 5'8", 150 lbs.
- **The marks list is the find.** A chest tattoo of "7 mile with two people both holding
  guns dressed in red with the initials BCB". A tattooed set affiliation, in Blood red,
  which is better evidence of BCB's nation than anything else on file and is one more
  reason the `Unknown Vice Lords` tag is wrong. Also "Brothers of the Hood role call" on
  the upper left arm, which is the shape of a memorial list and worth reading if a photo
  of it ever turns up.
- Recorded name variants: William Boden Morton, William James Boden Morton, William James
  Morton. **These are not aliases** and were deliberately kept out of the member's `aliases`
  column - they are spelling variants of a legal name the page already prints, and putting
  them there renders a meaningless a/k/a line. Same for the court caption's "a/k/a Devon
  Cheo Bell". Both live in the source notes instead.

## MDOC 666392, Devon Bell

Pulled 2026-08-25. **OTIS lists "D" among his aliases**, which independently confirms the
street nickname, so it is his `nickname` and the rest stay out of `aliases`.

- **Date of birth 1 August 1990**, so he was **18** on the day, against Morton's 15.
- Court file **08018563-01-FC** - he is defendant **-01** on the same case Morton is
  **-03** on.
- **Second-degree murder (MCL 750.317), 25 to 40 years**, plus felony firearm 2 years.
  Sentenced **24 November 2009**, five weeks after Morton. **Press reporting of 27-40 was
  wrong**; the record says 25 to 40.
- Earliest release **15 October 2035**, maximum discharge **15 October 2050**. Oaks
  Correctional Facility, security level II. SID 2876132P.
- Marks: one scar, a bite mark on the upper left shoulder.
- Other recorded names - Devon Cheo Bell, Devon Choodarius Bell, Devon Darius Bell - are
  legal-name spellings and stay in these notes rather than in `aliases`.

**Correcting something recorded earlier in this session, twice over.** An OTIS *name*
search for "Devon Bell" returned zero rows and was written up as "OTIS has neither
co-defendant". That was wrong: he is in OTIS. It was then written up a second time as the
name search being unreliable in general, and that reason was wrong too. Re-run, the same
search returns two Devon Bells, 666392 and 898058, both Prison. The zero was a transient
failure of one round trip through the proxy.

Two real limits, established by testing rather than assumed: the first name must be
**complete**, since "Dev"/"Bell" returns nothing while "Devon"/"Bell" returns two; and a
surname alone works fine ("Waller" returns 27). So **re-run a name search before reading a
zero as absence**, and prefer the offender number whenever one is available - not least
because two men here share a name.

## To-To: Otis Waller Jr

He was already a member - BCB, DEAD, born **16 October 1989**, killed **7 April 2008** -
created 2026-08-25 from the user's own research, with two Facebook-sourced photos. What he
had no trace of was a death: no incident row, no `death_incident_id`, no source. That is
now seeded (`../tools/seed_toto_death.py`).

**The retaliation was on his birthday.** He was born 16 October 1989. Christopher Walker
was killed 16 October 2008, the day To-To would have turned 19. That is not one source
repeating itself: the date of birth is the user's research, the date of death and address
come from the homicide list, and the motive comes from the appellate opinion. Three
independent inputs, which is what makes it worth stating rather than a coincidence of
transcription. It also explains why that day, and gives "To-To says what's up" its edge.

**He was killed on his own set's ground.** 18551 Pierson St, Sunbeam Heights, Detroit
48219, geocoded to **42.4251298, -83.2472397**. Burgess (42.4270, -83.2559), Chapel
(42.4360, -83.2549) and Blackstone (42.4355, -83.2513) are all 48219 and all within about
a kilometre - so the streets BCB is named for surround the place he died. Henry Ford High
School is about 1.5 km northeast of that cluster, which puts the retaliation off BCB's
core ground rather than on it.

**Nobody is attributed to killing him.** No press coverage exists - searched 2026-08-25 by
name, address and year, nothing. No obituary or memorial page surfaced. He has **no MDOC
record**: OTIS holds 27 Wallers and not one Otis, which fits someone killed at 18 who never
reached state prison. The incident row therefore carries a victim and nothing else. That
BCB blamed FOE Life is evidenced by what they did six months later, but BCB's belief is not
a finding, so no `incident_set_participant` was written either.

Source for the date and address is the 2008 chamspage homicide list, entry 74, seeded at
**MEDIUM** to match the 2012 list already on file.

## Seeded, 2026-08-25

Written to prod by `../tools/seed_hfhs_2008.py` (idempotent, dry-run by default):

- **Sources** - the appellate opinion and the OTIS profile, both HIGH.
- **FOE Life** - new Set, variants "Family Over Everything" and "FOE-Life", Detroit,
  **enemy of BCB** (the bilateral row exists).
- **Members** - Chris (Christopher Walker, FOE Life, DEAD); D (Devon Bell, LOCKED);
  Derryck Brantley (FREE, acquitted); Kejuana McCants, Maleek Slater and Leon Merriweather
  (Unknown set, UNKNOWN status). To-To reused, not recreated.
- **Both offenders' MDOC records** - `legal_name`, `mdoc_number`, `dob` and the OTIS
  mugshot on each, plus a `member_incarceration` spell carrying the facility, the case
  file and the release dates: Morton's flagged `life_sentence` with no release dates,
  Bell's with earliest release 2035 and maximum discharge 2050.
- **Incident** - MURDER, 2008-10-16, "Evergreen Rd & Pembroke St, outside Henry Ford High
  School, Detroit", **42.436772, -83.239136** (the intersection node from Overpass), seven
  participants, `verified`. Brantley carries `acquitted=True`. The death sync set Walker to
  DEAD and linked his `death_incident_id`.

No biographies were written. Set, status, dates, legal name and the death incident are all
columns.

## Still open

- **Whether anyone finished Walker on the ground.** The street account is that the shooter
  shot him and then walked up and killed him on the ground. The appellate recital does not
  describe that - it has him firing into a crowd from outside a black Mazda. The one thing
  that could explain the confusion is the prosecutor's closing, which has Morton "walked up
  to Christopher Walker **in school** and says To-To says what's up" - but that is the
  earlier confrontation that led to the fistfight. The trial transcript, not the opinion,
  would settle it. Nothing about this went into the narrative as fact.
- **Sets for the three wounded and for Bell and Brantley.** All five are parked in Unknown.
- **BCB's gang tag.** Ten members still carry `Unknown Vice Lords`. Between the court's
  street-name expansion and Morton's red BCB tattoo, that wants clearing.
