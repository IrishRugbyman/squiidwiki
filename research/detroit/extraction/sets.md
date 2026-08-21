# Detroit sets and gangs from primary sources

Extracted 2026-08-21 from `../raw/fetched/`. Every entry is sourced to a court record, a
federal agency release, or named press reporting. Source IDs map to `source-index.md`.

This complements `bloods-sets-extraction.md`, which covers the DetroitStreetGangs.com Bloods
overview. Where the two disagree, the primary source here should win.

Most of this has **not** been written to the database. What has is marked per section.

---

## Naming caution: read this before seeding

Five distinct problems will corrupt the Set table if handled naively.

**1. Gangs rename themselves.** Smokecamp went **Runyon Boys → Original Paid Bosses (OPB) →
Paid Bosses Inc. → Smokecamp** [legal-037]. All four names appear across sources for the same
crew. The Seven Mile Blood Juniors became **Hobsquad** [press-122]. These are renames, not
separate sets.

**2. "Band" is three different gangs.** DOJ releases reference **Band Crew**, **Bandgang**
(also spelled **Band Gang**), and press references **Free Band Gang** [press-127]. The
2017-01-23 release lists Band Crew and Band Gang as *separate bullet points in the same
list* [legal-036], which confirms they are distinct organisations rather than a typo. Do not
merge them.

**3. National nation vs local set.** Vice Lords, Bloods and Crips are `Gang` records
(nations). **Mafia Insane Vice Lords**, **Traveling Vice Lords**, **Playboy Gangster Crips**,
**Rollin 60s Crips (Detroit line)** and **Bounty Hunter Bloods** are `Set` records under them.
The corpus is explicit that the Detroit Rollin 60s is a *line* started locally in 2008 under a
national gang founded in Los Angeles in the mid-1970s [press-067], and that the Mafia Insane
Vice Lords is "a local faction of the national Vice Lord gang that originated in Chicago"
[legal-032].

**4. One person, two hierarchies.** Antonio Johnson was simultaneously National President of
the Phantom Outlaw MC and a "Three-Star General" of the Vice Lords in Michigan [legal-033].
The schema's independent nullable `gang_id` on Set, Alliance and Member handles this; do not
force his set and nation to agree.

**5. "Seven Mile Bloods" is a set. "The 5s" is the bloc it grew into.** The east side runs two
Detroit-born alliances that are named after their founding sets, which is why everyone
mixes the two levels up. The **5s** are Blood-side and trace to the **55 Seven Mile Bloods**;
the **4s** are Crip-rooted and trace to the **42 Hustle Boyz**, **24 Boss Hoggs** and **42
Gutta Boyz** [detroitstreetgangs.com]. The 5s now covers thirty-plus affiliated cliques, so
the founding set's name gets used for the whole bloc, and **"RedZone Bloods" names both**.
SMB also has internal cliques of its own, every one of them carrying the 55 prefix (55 OEG,
55 52, 55 700 WaxGang, 55 TMB, 55 Psykoz, 55 DrenchGang, 55 50 Zone, 55 MG), so from the
inside it reads as an umbrella too. It is not: it is one `Set`, under the `Bloods` nation,
inside a `5s` `Alliance`. The 4s side of this is already modelled that way in the DB, as the
`4Gang` alliance holding Hustle Boyz, Gutta Boyz, Boss Hoggs, 264 and 1000Gang.

Two further traps on the same words. The Bounty Hunter Bloods maintain their own **"Seven
Mile Line"**, about fifteen members who identify with that stretch of their turf [legal-027] -
no relation to SMB. And several unrelated sets sit on Seven Mile Road: SmokeCamp at Albion,
MOB Pirus at Fenkell, Black P. Stones at Telegraph, 5674 at Van Dyke. **"The Bloods on Seven
Mile" is a geography, not an organisation**, and it is the thing people are usually describing
when they call SMB a conglomerate.

---

## Seven Mile Bloods (SMB)

**Seeded 2026-08-21** as set `seven-mile-bloods`, under the `Bloods` gang and the `5s`
alliance. See naming caution 5 above before adding anything to it.

| Field | Value |
|---|---|
| Nation | Bloods |
| Alliance | **The 5s** (the bloc SMB founded; do not merge the two) |
| Number | **55** |
| Territory | The **"Red Zone,"** east side 48205, written **4820-DIE**: Gratiot to Kelly, Seven Mile to Eight Mile |
| Scale | ~20 members and associates controlled the whole zip code, per federal investigators |
| Internal cliques | 55 OEG, 55 52, 55 700 WaxGang, 55 TMB, 55 Psykoz, 55 DrenchGang, 55 50 Zone, 55 MG |
| Sub-sects | **Seven Mile Blood Juniors**, renamed **Hobsquad** |
| Aliases | SMB, 55 SMB, RedZone Bloods, 726, HOBCITY, GrinchGang, ShottaGang, RyderBloxk, 55 Grinch |
| Economy | Detroit-to-West-Virginia prescription pill pipeline, reported at $80k/week |
| Instagram | `000_big_blood` |
| Status | ACTIVE at time of sources |
| Sources | press-120 to press-128, legal-023 to legal-026; clique list and the 5s/4s framing from detroitstreetgangs.com (`UNVERIFIED`) |

Case outcome: 21 charged in *US v. Arnold*, E.D. Mich. 2:15-cr-20652. Corey "Cocaine Sonny"
Bailey convicted 27 Aug 2018, sentenced Oct 2019 to two life terms plus three ten-year terms
concurrent. Billy Arnold convicted Dec 2023 on 22 counts, sentenced to life 10 Apr 2024 by
Chief Judge Sean Cox, the 20th member or associate convicted.

Historically the stronger east-side gang, which is why its rivals eventually combined against
it. The Juniors were "a sect initially composed of schoolkids from The Red Zone" who renamed
themselves Hobsquad to honour Ihab Maslamani after the Matt Landry killing gained him
notoriety [press-122].

**Rivals:** an alliance of **Hustle Boys**, **6 Mile Chedda Grove**, **Maxout 220** and
others, formed after the July 2014 killing of Djuan "Neff" Page. Also **Mapleridge Boys**
[press-122, press-123].

## Smokecamp / Original Paid Bosses (OPB)

| Field | Value |
|---|---|
| Former names | Runyon Boys; Original Paid Bosses; Paid Bosses Inc. |
| Nation | Within Bloods-claimed territory |
| Territory | **"ABlock"** - Albion Street and Seven Mile, east side, inside the Red Zone |
| Drug locations | Vacant "trap houses"; an East Seven Mile apartment complex branded **"the Plaga"** (c. 2014-2015) |
| Out-of-state | Kentucky, West Virginia, Ohio |
| Sources | legal-037 |

Thirteen members indicted 2017-11-08. Money came predominantly from narcotics - cocaine,
crack, heroin, marijuana, ecstasy and prescription pills - supplemented by robberies and
extortion. Members shared workers and firearms across the operation.

## Bounty Hunter Bloods

| Field | Value |
|---|---|
| Nation | Bloods |
| Territory | Northwest Detroit; activity extending California to North Carolina |
| Rivals | **Avon Gangsters** |
| Sources | legal-035, press-061, press-076, press-113 |

Crimes included murders, carjackings, armed robberies, drive-by shootings, home invasions,
arsons and witness intimidation. Advancement was by **"putting in work."** Members used social
media for self-promotion, posting photographs highlighting affiliation and "gang-related
accomplishments," and recorded rap songs asserting allegiance.

The Facebook post that anchors the case: on **2010-12-27** leader Ramiah Jefferson directed
the murder or attempted murder of rival Avon Gangster members, posting that fellow Bounty
Hunters needed to "knock them down one by one" and that it was **"huntin' season."**

## Playboy Gangster Crips (PGC)

| Field | Value |
|---|---|
| Also known as | **Thirty-Third Gangstas**, **Trey Trey Gangstas** |
| Nation | Crips |
| Territory | Northwest Detroit - Seven Mile Road between **Lahser and Evergreen** |
| Colours | Navy blue bandannas, called **"flags"** |
| Rivals | Bloods, Vice Lords, Band Crew, Rollin 60s Neighborhood Crips |
| Sources | press-084, press-063 |

The most completely documented internal structure in the corpus. Ranks below the **Original
Gangster (OG)**, in order: **Original Baby Gangster (OBG)**, **Young Baby Gangster (YBG)**,
**Baby Gangster (BG)**, **Tiny Gangster (TG)**. Rank depends on seniority and on how much
criminal work a member has done for the gang.

**Orthography** (useful for matching social media handles): members replace **K with C**
because of the Crips association, and avoid the letter **B** because it belongs to the Bloods.
A 2011 sale listing read: `"I bkang my set TTG P.B.G.C.^ 33rd if yall didn't kno im DVNG3R
Coripppp"`.

Regular meetings covered crime, rivalries and dues collection. Main income was drug sales
(heroin, cocaine, marijuana, prescription pills), supplemented by illegal gun sales,
carjackings and robberies. The OG decided how money was spent - guns, more drugs, or money
sent to members in prison.

Drug locations: the **Sunoco gas station at Seven Mile and Braile**, and vacant "trap houses"
on **Trinity**.

Fourteen members indicted October 2017, with **72 documented offenses** spanning 2010 to
2017-09-01:

| Person | Alias |
|---|---|
| Jvon Clements | Toon |
| Winston Hill | Shady Blue |
| Dawon Taylor | J-9 |
| Ron Benson Jr. | Duke |
| Devante Crockett | TBK |
| Deshaun Tisdale | Havoc |
| Davon Moultrie | Blue |
| Deondre Casey | Trouble |
| Andre Tinsley | Danger |
| Dangelo Davis | Black |
| Recharl Boynton | Bear |
| Anthony Marshall | Hitman |
| Nathaniel Brown | Nino |
| Darryl Grizzard | Deezy |

## Rollin 60s Crips - Detroit line

| Field | Value |
|---|---|
| Nation | Crips |
| Parent | National gang founded in Los Angeles, mid-1970s |
| Detroit line founded | **2008**, by Jerome Hamilton |
| Size | ~150 members |
| Territory | West side Detroit, near **Seven Mile Road and Tracey Street** |
| Sources | press-067, press-077, press-062 |

Responsible for assaults, robberies, carjackings and firearms/narcotics trafficking across
metro Detroit over roughly nine years. Uses violence for retribution against rivals, to
intimidate witnesses, and for internal advancement.

- **Jerome Hamilton**, 26 - founder. Pleaded guilty to RICO conspiracy and a firearm count
  causing death; took responsibility for the **2011-08-08 drive-by homicide of Kionte
  Atkins**. **30 years.**
- **Darriyon Mills**, 22 - second-in-command. Pleaded guilty to RICO conspiracy and a firearm
  count; committed armed robberies, carjackings and attempted murders, and trafficked drugs to
  fund the gang. **24 years.**

## The Skuddzone cluster (west side)

| Field | Value |
|---|---|
| Location | West side Detroit, off **Exit 9, Joy Road** |
| Sources | press-069 (WDIV Defenders, 2015-06-22) |

Not one gang but a contested area where several groups operate, each **defined by a crime
speciality** such as break-ins or street robberies. Building graffiti marks the boundaries.

- **RTM (Related Through Money)** - ten members charged with federal racketeering [legal-036]
- **YPB (Young Paid Bosses)** - rival of RTM
- **TNO (Trust No One)** - rival of RTM; also a Bandgang rival [legal-046]

Terminology from an unnamed insider interview: an order to kill is a **"TOS" (termination on
site)**, issued by a higher-ranking member. Killings are described as comparatively rare
because members cannot act without approval.

Treat the insider testimony as `UNVERIFIED`-grade colour; the RTM racketeering charge itself
is `HIGH`.

## Bandgang

| Field | Value |
|---|---|
| Also spelled | Band Gang |
| Territory | West side Detroit |
| Rivals | **Trust No One (TNO)**, **Too Much Cash (TMC)** |
| Economics | **Credit card fraud and identity theft**, not primarily drugs |
| Sources | legal-046, press-127 |

An outlier worth flagging in the wiki: the violence was driven by fraud proceeds, not
territory or narcotics. Over **15,000 stolen credit card accounts** were linked to members,
and four credit card labs were seized. Twenty-four members and associates were charged across
sixteen cases.

## YNS (Young and Skantless)

| Field | Value |
|---|---|
| Territory | Northwest Detroit, **Brightmoor** |
| Sources | legal-041, press-126 |

Charged as "the most dangerous group in Brightmoor and one of the most dangerous in the city
of Detroit." The indictment is explicit that YNS **purposefully cultivated** a reputation for
ruthless violence to make its other crimes easier, and that posting intimidating photographs
and videos to social media was part of that strategy - not incidental.

## 6 Mile Chedda Grove

| Field | Value |
|---|---|
| Territory | East side Detroit |
| Sources | legal-034, press-136, press-098, press-124 |

Responsible for murders, assaults, robberies and firearms/narcotics trafficking in metro
Detroit and other states. Eleven members charged with racketeering conspiracy. Part of the
alliance formed against the Seven Mile Bloods. Rapper **Phillip Peaks ("Team Eastside
Peezy")** is under indictment alongside ten members and associates.

## Hustle Boys

| Field | Value |
|---|---|
| Territory | Detroit; pill pipeline to **southern Ohio and West Virginia** |
| Sources | legal-043, press-112, press-092, press-110 |

Moved thousands of OxyContin, Opana and other prescription pills from Detroit to southern Ohio
and West Virginia between 2007 and March 2011, selling from hotel rooms and three maintained
residences, and at times **trading pills for firearms** that were brought back to Detroit. A
house on **Hamburg Street** served as the storage and packaging point.

Part of the alliance against the Seven Mile Bloods.

## Latin Counts

| Field | Value |
|---|---|
| Territory | Southwest Detroit; downriver **Lincoln Park** and **Ecorse** |
| Known set | **Toledo Mafia Counts** (Christopher "C-5" Rishell was its president) |
| Sources | legal-036, legal-044, press-071, press-069, press-131 |

A criminal enterprise responsible for murders, robberies and drug distribution, using violence
to stake out turf, retaliate against rivals, intimidate the community and advance members
internally. Described by WDIV as one of southwest Detroit's "established gangs," with a
hierarchy in which young members take direction from elders [press-069].

## Vice Lords in Michigan

Nation-level record with at least three distinct Detroit branches in the corpus:

| Set | Detail | Source |
|---|---|---|
| **Mafia Insane Vice Lords** | East side. Michigan branch led by Christopher "Chief Fatah" Tibbs. A local faction of the Chicago-origin nation. | legal-032 |
| **Traveling Vice Lords (TVL)** | Branch of the Almighty Vice Lords Nation (AVLN). Ranks named in evidence: **Chief**, **Universal Elite**, **Chief of Security**. | legal-038 |
| **Phantom Outlaw MC / Vice Lords** | Northwest Detroit. An outlaw motorcycle club whose leadership doubled as Vice Lord leadership. Rival clubs: **Satan Sidekick MC**, **Hell Lovers MC**. | legal-033 |

The AVLN is described as "a sprawling criminal enterprise which committed acts of violence,
drug dealing, and other crimes, across the country" - so its Detroit presence is a branch of a
national body, not a local invention.

---

## Gangs named in DOJ enumerations but not otherwise documented here

The 2017-11-08 and 2017-01-23 releases each list every Detroit gang prosecution to date
[legal-037, legal-036]. These appear there with a charge count but have no dedicated document
in the fetched corpus. Each is a real, chargeable organisation and a legitimate `Set` record:

| Set | Charged | Note |
|---|---|---|
| Band Crew | 3 under state gang statute + 8 federal RICO | Distinct from Bandgang |
| RTM (Related Through Money) | 10 federal RICO | Skuddzone |
| A1Killers | 3 federal narcotics | |
| HNIC | 4 for violent acts in aid of racketeering | |
| Free Band Gang | - | Stole $2M from Walmart in a crime spree [press-127] |
| Maxout 220 | - | Named as part of the anti-SMB alliance [press-122] |
| Mapleridge Boys | - | East side rival of SMB [press-123] |
| Avon Gangsters | - | Rival of Bounty Hunter Bloods [legal-035] |
| Too Much Cash (TMC) | - | Rival of Bandgang [legal-046] |
| Young Paid Bosses (YPB) | - | Skuddzone, rival of RTM [press-069] |

Two further enumerated operations are **geographic**, not named gangs, and should not become
Set records:

- 24 individuals charged over sixteen houses in the east-side **Ravendale** neighbourhood,
  distributing heroin, cocaine and crack, 2013-2015
- 14 individuals charged over drug distribution in the west-side **Warrendale** neighbourhood

---

## Territory note: the one bounding box in the corpus

The Bellingcat piece [press-060] quotes an indictment describing a territory as:

> Seven Mile Road, with Southfield Freeway to the west, West McNichols Road to the south,
> Eight Mile Road to the north and Greenfield Road to the east.

That is a usable polygon for the municipality/territory layer. **Caveat:** the article
analyses `gang-file-9-22-15.pdf` (a September 2015 indictment, also bookmarked as
`press-063`), and does not name the gang in the fetched text. Confirm which gang it belongs to
before attaching the geometry - the date lines up with the 2015-09-22 Band Crew case
[press-078].
