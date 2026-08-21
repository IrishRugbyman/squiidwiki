# Detroit gang incidents from primary sources

Extracted 2026-08-21 from `../raw/fetched/`. Every incident below is dated and attributed to a
named source. Source IDs map to `source-index.md`.

**Nothing here has been written to the database.**

## Seeding notes

- **Dates map to `FuzzyDate`.** Precision is marked in the table: `YMD` where the source gives
  a full date, `YM` where only a month is given, `Y` where only a year. Never widen a date to a
  plain `DATE` column.
- **Roles and outcomes** use the `incident_participant` vocabulary: role
  `SHOOTER | ASSISTED | BYSTANDER | VICTIM`, outcome `KILLED | INJURED | UNHARMED | UNKNOWN`.
- **`acquitted` is significant here.** Several of these are charged-but-untried allegations.
  Setting `acquitted = False` is correct for those (it means *attributed by research*), but
  where a source records an actual acquittal it is called out in bold and must be
  `acquitted = True`.
- **Incident-driven death sync** will set `status=DEAD`, `date_of_death` and
  `death_incident_id` on any member given `outcome=KILLED`. That is desirable for the victims
  below, so seed the incident *after* the member exists.

---

## Timeline

| Date | Prec. | Event | Attributed to | Source |
|---|---|---|---|---|
| 2006-06-07 | YMD † | **Cleo McDougal**, 25, shot dead at **14299 Fordham**. A man known as "Lucky" was wrongly convicted and exonerated after 7+ years. | Robert Brown (SMB) - charged | press-125 + press-065 |
| 2009-02-04 | YMD † | **Marquise Robinson**, 18, murdered at **18704 Stahelin** because he was believed to have refused to come to the aid of Bounty Hunter member David Lamar Gay. | Jayjuan Watts (shooter) - convicted, **life** | legal-035 + press-065 |
| 2009-08-13 | YMD † | **Matt Landry**, 21, abducted outside a Quiznos in Eastpointe and killed; body found in a burned-out house at **14711 Maddelein** in the Red Zone. | Ihab Maslamani (SMB Juniors) - convicted | press-122 + press-065 |
| 2010-03 | YM | AK-47 sold on Facebook for $200. | Dawon Taylor (PGC) - charged | press-084 |
| 2010-12-27 | YMD | Facebook post directing the murder/attempted murder of rival **Avon Gangster** members: "knock them down one by one," "huntin' season." | Ramiah Jefferson (Bounty Hunter Bloods) - convicted | legal-035 |
| 2011-08-08 | YMD † | **Kionte Atkins**, 34, killed in a drive-by at **8208 Carlin**. | Jerome Hamilton (Rollin 60s) - pleaded guilty | press-067 + press-065 |
| 2011-10 | YM | .380 handgun sold for $275, listed with gang orthography. | Andre Tinsley (PGC) - charged | press-084 |
| 2011-12 | YM | A victim shot in front of the **Apollo Market on West Seven Mile**. | Ron Benson Jr. + Andre Tinsley (PGC) - charged | press-084 |
| 2013-08-18 | YMD | **Terrence McClearen** killed; a second victim shot. | Jonathan Estrada, Jesus Rodriguez, Angel Rodriguez (Latin Counts) - pleaded guilty | legal-036 |
| 2013-09-08 | YMD | Phantoms ordered to forcibly take the "rags" (vests) of rival **Satan Sidekick MC** members. A Satan Sidekick was shot in the face; a Phantom was stabbed. | Antonio Johnson, ordering (Phantom OMC) - convicted | legal-033 |
| 2013-09 | YM | Armed robbery of a **Little Caesars in Redford**. Tibbs "blessed" it as a gang mission, sent four subordinates, instructed them to disable cameras and phones, and took most of the proceeds. | Christopher Tibbs (Mafia Insane Vice Lords) - convicted | legal-032 |
| 2013-09/10 | YM | Plot to murder three **Hell Lovers MC** members and then shoot every Hell Lover attending the wake. ATF and FBI intervened before it was carried out. | Antonio Johnson + Phantoms - convicted | legal-033 |
| 2014-02 | YM | Attempted carjacking outside a **CVS on Schaefer Road**; security guard **Courtney Meeks** murdered while preventing the carjacking of a mother and infant. | Jamare Rucker + Jeremy Jackson (Bounty Hunter Bloods) - convicted, 33-60 years each | legal-035, press-070 |
| 2014-04-18 | YMD | **Mustafa Al-Yasiry** assaulted by several Latin Counts and shot dead at the **Big Apple Market**, SW Detroit. | Devin Dantzler (shooter) + Victor Vasquez - pleaded guilty; 3 others already pleaded | legal-036 |
| 2014-07-14 | YMD | Between 10am and 12pm, a shooting at the **Lawton parole office**. Four men were travelling in a car: **Djuan "Neff" Page**, 22, shot in the eye; **Michael Davis** shot in the chest; his twin **Martaze Davis**; and **Corey Crawford**. Page spent several weeks in a coma and **died in August 2014**. **This killing forged the anti-SMB alliance** of Hustle Boys, 6 Mile Chedda Grove, Maxout 220 and others. | Billy Arnold + Corey Bailey (SMB) - charged; identified by a CHS and by Michael Davis at trial | legal-023, legal-024, press-119, press-122 |
| 2014-08 | YM | **Donell Hendrix** ("Hardwork Jig") shot at **Eastland Center mall**; survived. | rivals of SMB | press-122 |
| 2015-02 | YM | **Jason "White Boy" Gill**, 30, killed. | rivals of SMB | press-122 |
| 2015-03 | YM | **Michael Rogers** shot 18 times; survived. | rivals of SMB | press-122 |
| 2015-05-01 | YMD | ~13:15. **Devon "Block" McClure**, 26, shot in the head and killed in a blue Ford Crown Victoria at **Hayes and Houston Whittier**, after a tan SUV pulled alongside. **Unsolved.** Rivals posted his photo to `@all_new_victims55`: "We got block out the way. Bman you know u next." | unknown | press-122 |
| 2015-05-08 | YMD | 17:44. Reconnaissance near **Denby High School** on the day of McClure's funeral visitation - passing makes, models and colours of target vehicles to Billy Arnold. | Matleah Scott (associate) - plea deal | press-123 |
| 2015-05-08 | YMD | ~18:44. Drive-by at **Duchess Avenue and Craft Street**. A grey Chrysler 300 pulled alongside a Pontiac G6 carrying three **Mapleridge Boys**. **Dvante "Little" Roberts**, 19, killed by a head shot at close range. **Darrio Roberts** shot in the head, survived. **Marquis Wicker**, 25, hit nine times, critical for days. 15 shell casings recovered. SMB posted the dead teenager's photo with three laughing emojis and "got 'em." | Seven Mile Bloods - charged | press-123 |
| 2015-05-10 | YMD | Mother's Day. Two gunmen fired **at least 64 bullets** into a black Chevrolet Impala at **State Fair and Hoover**, including 36+ rounds from the same AR-15-style rifle used two days earlier. Target **Darnell Canady** (Hustle Boys) was missed; another Hustle Boy was wounded. | Billy Arnold, Robert Brown + a third man (SMB) - charged | press-123 |
| 2015-06 | YM | A **Roseville banquet centre** baby shower shot up. Canady hit in the leg; a bystander struck. | Billy Arnold (SMB) - charged | press-123 |
| 2015-06 | YM | A photo of a rival target and a map to the man's house sent to Billy Arnold. | Jeffery Adams (SMB) - hung jury | press-125 |
| 2015-07 | YM | **Ralpheal Carter** shot and **paralysed** at a **Southfield pool party**. Arnold was hunting rapper Phillip Peaks, could not find him, and shot the first associated person he found. | Billy Arnold (SMB) - charged | press-124 |
| 2015-12-01 | YMD | Afternoon. Gunmen fired at a car near a market on **Hayes Street**, east side, killing the **21-year-old driver and 13-year-old passenger** and pistol-whipping two more victims, aged **13 and 7**, causing serious injury. | Edwin "Edboy" Mills + Carlo "Los" Wilson (6 Mile Chedda Grove) - charged | legal-034 |
| 2016-02 | YM | A shooting that left a **five-year-old girl permanently disabled**. | Bandgang members | legal-046 |
| 2016-06-21 | YMD | Drive-by into a house on **Biltmore Street**, targeting two rival gang members. Bailey fired a .45; Wilson emptied an Uzi with a 50-round magazine. An unconnected woman in the house was severely injured. | Martez Bailey + Khalil Wilson (Bandgang) - pleaded guilty | legal-046 |
| 2017-09-24 | YMD ? | **Aaron Hayes**, 27, executed on an east-side porch by two masked men with AR-15s, weeks after release from ~10 years for manslaughter. FBI believed a bounty was on him: the teen he killed 12 years earlier was a Hustle Boy. **Year inferred** - the source says only "Sept. 24." | rivals of SMB | press-124 |
| 2017-10-07 | YMD | Drive-by in a residential SW Detroit neighbourhood: **one killed, two injured**. Seven Latin Counts charged; all pleaded guilty. | Christopher "C-5" Rishell, orchestrating (Toledo Mafia Counts) - pleaded guilty, 20 years | legal-044 |
| 2018-02-04 | YMD | Rapper **Phillip Peaks** ("Team Eastside Peezy") shot and wounded in **Warren** during an apparent gas-station robbery, four days after his photo was shown at the SMB trial. **Unsolved.** Warren police were "looking at the possibility it could be related to the indictments"; his lawyer called the timing coincidental. | unknown | press-124 |
| 2020 | Y | Murder and attempted murder at the **Shirley-Plymouth playground**, west side, in broad daylight. A 29-year-old man killed in front of his two young children; the children's pregnant mother, a witness, shot and injured. | Davun Baskerville (shooter), Terry Douglas + Schuyler Belew Jr. (aiding) - convicted 2024 | legal-038 |
| 2021-04-16 | YMD | Shooting at a **CVS on Grand River Avenue**. Surveillance captured a newer-model white Escalade with black tires, rims and grille. | linked by NIBIN to Delmarco Craig's rifle | legal-031 |
| 2021-05-25 | YMD | ~23:20. Homicide and double non-fatal shooting near **8576 Strathmoor Street**, hours after Craig streamed an Instagram Live brandishing what appeared to be the same rifle. | linked by NIBIN to Delmarco Craig's rifle | legal-031 |

**†** The date, age and address in these four rows come from combining a court source with the
homicide lists in `homicides/`. The court source alone gave only a month or a year. See
"Cross-reference" below for the matching evidence on each.

---

## Aggregates worth recording as universe-level notes

- **Seven of the accused Seven Mile Bloods were shot during the gang war; four died.**
  [press-122]
- The SMB Instagram account `000_big_blood` posted photos of **62 rivals**. A rival account
  posted a hit list of **10 SMB members** after Djuan Page's killing. [press-122]
- **Date caution on the Page shooting.** The privedatabase site dates it to 24 July 2014.
  The court record is 14 July 2014 for the shooting and August 2014 for the death, so the
  site's single date is neither, and 24 looks like a transposition of 14. Where a date in
  that corpus has no court counterpart, treat it as a lead rather than a correction.
- **Detroit homicides fell from 386 in 2012 to 300 in 2014.** [legal-033] By 2017, DOJ put the
  post-2013 trend at homicides down 20% and non-fatal shootings down 25%, with 174 fewer
  homicides across four years than the preceding four. [legal-036]
- The Bandgang investigation linked **over 15,000 stolen credit card accounts** and seized
  four credit card labs. [legal-046]
- The Playboy Gangster Crips indictment lists **72 documented offenses**, 2010 to 2017-09-01.
  [press-084]
- NIBIN tied a single rifle to **seven shootings since October 2020**. [legal-031]

## Unsolved, as recorded

Three killings and shootings are explicitly unsolved in the sources, which makes them useful
`Incident` records with no `SHOOTER` participant:

1. **Devon "Block" McClure**, 2015-05-01 - "remains unsolved and factors prominently into the
   Seven Mile Bloods case as an inciting incident"
2. **Phillip Peaks** shooting, 2018-02-04 - "The shooting of 'Team Eastside Peezy' is unsolved"
3. **Djuan "Neff" Page**, 2014-07-14 - *not* unsolved after all. Court filings identify
   Billy Arnold and Corey Bailey as the shooters, and cell-site data placed Arnold's phone
   at the Lawton parole office during the shooting window. The complication is the
   surviving victim: **Michael Davis was indicted for refusing to name them** from the
   stand, then testified at trial that Arnold and Bailey were the shooters.

## Cross-reference: the homicide lists corroborate, and fill gaps

`homicides/` holds **4,019 Detroit homicide victims across 2003-2013**, one file per year.
Four killings in the timeline above fall inside that window with a name to match. **Three
match, and each one supplies detail the court source omits.**

**1. Kionte Atkins** - court source [press-067], list entry 2011-08-08

| Field | Court record | Homicide list |
|---|---|---|
| Name | Kion**te** Atkins | Kion**tae** Atkins |
| Date | 2011-08-08 | 2011-08-08 |
| Age | not given | **34** |
| Location | not given | **8208 Carlin** |

**2. Cleo McDougal** - court source [press-125], list entry 2006-06-07

| Field | Court record | Homicide list |
|---|---|---|
| Name | Cleo McDougal | Cleo Mc**d**ougall |
| Date | "June 2006" | **2006-06-07** |
| Age | 25 | 25 |
| Location | not given | **14299 Fordham** |

The killing Robert Brown is charged with, and the one a man called "Lucky" served 7+ years
for before exoneration. The list turns a month-precision `FuzzyDate` into a full `YMD` one.

**3. Marquise Robinson** - court source [legal-035], list entry 2009-02-04

| Field | DOJ release | Homicide list |
|---|---|---|
| Name | Marquise Robinson | Marquise Robinson |
| Date | not given | **2009-02-04** |
| Age | "a young man" | **18** |
| Location | not given | **18704 Stahelin** |

The biggest gain of the four. DOJ gave no date and no age for the murder that Jayjuan Watts
is serving life for. Stahelin is on the west side, consistent with the Bounty Hunter Bloods'
stated northwest Detroit base.

**4. Matt Landry** - court source [press-122], list entry 2009-08-13

| Field | Detroit News | Homicide list |
|---|---|---|
| Name | Matt Landry | Matt**hew** Landry |
| Date | "2009" | **2009-08-13** |
| Age | 21 | 21 |
| Location | "a burned-out house on Maddelein Avenue" | **14711 Maddelein** |

Street name confirmed independently, plus a house number and an exact date.

### The one that does not match

**Terrence McClearen**, killed 2013-08-18 per the Latin Counts plea [legal-036], is **absent**
from the 2013 list. This is not a contradiction. The 2013 list is **73% unidentified** (204
of 279 entries carry no name), so a missing name is the expected failure mode. Three entries
exist for 2013-08-18, all unnamed, and none matches the double-shooting the plea describes.

### What this means

Reaching four court-documented killings and matching three of them on exact dates promotes
this blog above what "personal blog" would suggest, but **does not make it a primary source**.
Use it the way it is used here: to sharpen a date, recover an age, or find a block address
that a press release left out - then cite the court record, not the blog.

Two handling rules follow from the divergences above:

- **Match on date plus approximate name, never name alone.** Three of four matches had a
  spelling variation (Kiontae/Kionte, Mcdougall/McDougal, Matthew/Matt).
- **Carry both spellings** into alias fields, or a later automated pass will miss the link.
