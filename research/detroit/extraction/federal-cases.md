# Detroit federal and state gang cases

Extracted 2026-08-21 from the fetched text in `../raw/fetched/`. Each case below is drawn
from a primary source: a DOJ press release, a federal court opinion, or a court PDF. Source
IDs in brackets map to `source-index.md` and to the filenames in `../raw/fetched/`.

**Nothing here has been written to the database.** This is a staging document.

## How to read the status column

The wiki treats `incident_participant.acquitted = False` as *attributed by research*, not
*convicted*. These cases are the rare material where the distinction is documented, so it is
preserved explicitly here:

- **charged** - named in an indictment, never tested at trial in the fetched source
- **pleaded** - admitted the conduct in a plea agreement
- **convicted** - found guilty at trial
- **acquitted** - affirmatively cleared. Maps to `acquitted = True`

Carry this column through to any seeding script. Losing it silently converts an allegation
into a finding.

---

## Seven Mile Bloods (SMB)

RICO prosecution before U.S. District Judge George Caram Steeh, E.D. Mich. The best-documented
Detroit gang case in this corpus: The Detroit News ran an eight-chapter series, "Death by
Instagram," by Robert Snell. [press-120 through press-128, legal-023 to legal-026]

Territory is the **"Red Zone"** on Detroit's east side. A junior sect, the **Seven Mile Blood
Juniors**, renamed itself **Hobsquad** to honor Ihab Maslamani after he gained notoriety for
the 2009 killing of Matt Landry. [press-122]

Gang Instagram account: **`000_big_blood`**, used to post hit lists of rivals. The gang posted
photos of 62 rivals during the war. Rival accounts: **`@all_new_victims55`** and one operating
as **"All Head Shots."** [press-122, press-125]

| Person | Aliases | Role | Status | Detail |
|---|---|---|---|---|
| Corey Bailey | Cocaine Sonny, Sonny | leader | charged (11 counts) | 30, Detroit. Rapper. Acquitted of first-degree murder in 2010. Took part in Detroit's "Stop the Violence" program in 2013 while active in the gang. Arrested Jul 2014, 55 months for a federal gun crime. DOJ declined the death penalty on 15 May. |
| Billy Arnold | B-Man, Berenzo, Killa | leader | charged (31 counts) | 31, Detroit. Former handyman. 2 murder counts, 9 attempted murder counts. DOJ signaled it would seek the **death penalty**. Magistrate Judge Mona Majzoub called his record an "unabated" stretch of lawlessness since 17. |
| Robert Brown | RO Da Great | founding member | charged (7 counts) | 36, Warren. Charged with the Jun 2006 killing of Cleo McDougal, 25 - a killing wrongly blamed on a man called "Lucky," who was exonerated after 7+ years in prison. Released a rap track threatening the witness: "'Bleek' a cop, so I gun him down." |
| Jeffery Adams | Brick, Product | member | hung jury, awaiting retrial | 29, Detroit. Linked to the `000_big_blood` account. Jun 2015: sent Arnold a photo of a rival and a map to his house. |
| Arlandis Shy | Grymee, VIL | long-standing member | charged (11 counts) | 28, Clinton Township. Raised on the east side, worked temp jobs in auto-parts factories. |
| Devon McClure | Block | leader | **killed 2015-05-01** | 26. Starred in YouTube rap videos. Killing unsolved; it is the inciting incident of the gang war. |
| Michael Rogers | | accused member | **acquitted 2018-03-16** | Shot 18 times Mar 2015. Freed after "two years and 15 days" in federal detention. |
| Donell Hendrix | Hardwork Jig | charged | charged | Rapper. Survived a shooting at Eastland Center mall, Aug 2014. |
| Jason Gill | White Boy | member | **killed Feb 2015** | 30. |
| Aaron Hayes | | member | **killed Sept 24** | 27. Executed on an east-side porch by two masked men with AR-15s after ~10 years in state prison for manslaughter. FBI believed there was a bounty on him: the teen he killed 12 years earlier was a Hustle Boy. |
| Jerome Gooch | | co-defendant | shot during the war | |
| Quincy Graham | | co-defendant | shot during the war | |
| Matleah Scott | M Thang | associate | plea deal on file [legal, blocked] | 24. McClure's girlfriend. Ran reconnaissance for Arnold on 2015-05-08, the day of McClure's funeral visitation. |
| Michael Davis | | witness | indicted for refusing to testify | 27. Defied Judge Steeh's order on 8 March; was shot in the incident that killed Djuan "Neff" Page. |
| Jonathan Murphey | Bleek | former member, witness | testified | Witnessed the McDougal killing. "(Brown) shot his face off." |
| Ihab Maslamani | | Seven Mile Blood Juniors | convicted | Killed Matt Landry, 21, abducted 2009 outside a Quiznos in Eastpointe; body found in a burned-out house on Maddelein Ave in the Red Zone. |

Seven accused SMB members were shot during the war; four died. [press-122]

Prosecutors: DOJ trial attorney Julie Finocchiaro, AUSA Christopher Graveline.

---

## Smokecamp / Original Paid Bosses (OPB)

Racketeering indictment unsealed 2017-11-08, thirteen members. [legal-037]

The gang renamed itself repeatedly: **Runyon Boys → Original Paid Bosses → Paid Bosses Inc.
→ Smokecamp**. That chain matters for entity resolution - the same crew appears under four
names across sources.

Territory: east side, around **Albion Street and Seven Mile**, an area members call
**"ABlock,"** inside the larger Bloods-claimed **"Red Zone."** Sold narcotics outside vacant
"trap houses" and from an East Seven Mile apartment complex they branded **"the Plaga."**
Members travelled to Kentucky, West Virginia and Ohio to sell.

| Person | Aliases | Age | From | Charges |
|---|---|---|---|---|
| Korey Sanders | No Loan Corleon, Stax | 26 | Detroit | RICO conspiracy; unlicensed firearms dealing |
| Jerray Key | Chino, Dre | 28 | Canton | RICO conspiracy; unlicensed firearms dealing |
| Deshawn Langston | Pook, Slips | 26 | Detroit | RICO conspiracy |
| Richard Langston | Dub, Rich, Blow | 27 | Detroit | RICO conspiracy |
| Hakeem Bunnell | LB Dub | 24 | Detroit | RICO conspiracy; assault with a dangerous weapon in aid of racketeering; firearm in relation to a crime of violence |
| Keenan Nielbock | Dolla, Keno | 30 | Taylor | RICO conspiracy; unlicensed firearms dealing |
| Caraun Key | Luch, Ron, Slick | 26 | Detroit | RICO conspiracy |
| Darryl Key | DB, Big Baby | 27 | Detroit | RICO conspiracy |
| Tyree Williams | Snoop | 24 | Detroit | RICO conspiracy; assault with a dangerous weapon in aid of racketeering; firearm in relation to a crime of violence |
| Romale Gibson Jr. | Santana | 24 | Detroit | RICO conspiracy |
| Cary Dailey | Cease | 28 | Detroit | RICO conspiracy |
| Antonio Langston | Tone | 29 | Detroit | RICO conspiracy |
| Carlos Davis | Los, Loso | 24 | Detroit | RICO conspiracy; assault with a dangerous weapon in aid of racketeering; firearm in relation to a crime of violence; unlicensed firearms dealing |

All **charged** only - the source is the unsealing announcement.

Three Key brothers (Jerray, Caraun, Darryl) and three Langstons (Deshawn, Richard, Antonio)
appear in one indictment. Worth modelling as family links once seeded.

---

## Bounty Hunter Bloods

Leader sentenced 2016-04-20 before U.S. District Judge Nancy G. Edmunds. [legal-035,
press-061, press-076, press-113]

Operated primarily in **northwest Detroit**, with activity from California to North Carolina.
Members used social media heavily for self-promotion, and recorded rap songs asserting
allegiance. Advancement came through "putting in work."

| Person | Aliases | Age | Outcome |
|---|---|---|---|
| Ramiah Jefferson | Nightmare | 27 | **30 years.** Convicted at trial (Aug) of RICO conspiracy and firearm possession in furtherance of a crime of violence. Directed murders and attempted murders of rivals, furnished guns. |
| Evan Johnson | Unkle Murda | 24 | **30 years.** RICO conspiracy + firearm. |
| Alexander Deshawn George | Bullet | 20 | **18 years.** RICO conspiracy + firearm. |
| David Lamar Gay | Glock | 22 (Toledo, OH) | **17.5 years.** Murder in aid of racketeering. |
| Drakkar Beral Cunningham | Rellz | 25 | **5 years.** RICO conspiracy + firearm. |
| Everette Ramon George | Klout | 21 | **4 years 9 months.** Assault with a dangerous weapon in aid of racketeering. |
| Mario Garnes | Bloodhound | 28 | **42 months.** RICO conspiracy. |
| Gerald Deshawn Turner | G-Red | 25 | **Time served** + 3 years supervised release. RICO conspiracy. |
| Marcus Andre Harvey | Ceasar | 23 | Convicted; sentencing set 2016-05-02. |

Alexander Deshawn George and Everette Ramon George share a surname and are close in age -
likely brothers, unconfirmed in the source.

Prosecuted by AUSAs Eric Doeh, Andrew Goetz, Eaton Brown.

**Associated state prosecutions** (Wayne County):
- Jamare Rucker and Jeremy Jackson, both Bounty Hunter members: **33-60 years** for second
  degree murder plus a consecutive 2 years for felony firearm, for the Feb 2014 carjacking
  outside a CVS on Schaefer Road that killed security guard **Courtney Meeks**.
- Jayjuan Watts: **life**, as the main shooter in the murder of **Marquise Robinson**, killed
  because he was believed to have refused to come to the aid of Bounty Hunter member David
  Lamar Gay.

---

## Phantom Outlaw Motorcycle Club / Vice Lords

Leader sentenced 2015-09-08 before U.S. District Judge Paul D. Borman. Thirteen defendants
convicted in total. [legal-033]

The Phantoms were headquartered in **northwest Detroit**. Their leadership was heavily
involved in the **Vice Lords**, and the club was used as a vehicle for Vice Lord business -
an unusually explicit example of an OMC and a street gang sharing a command structure.

| Person | Aliases | Age | From | Outcome |
|---|---|---|---|---|
| Antonio Johnson | Mister Tony, MT, Big Bro | 39 | Detroit | **35 years.** National President of the Phantom OMC *and* "Three-Star General" of the Vice Lords in Michigan. Convicted 2015-03-16 after a multi-week trial. |
| Marvin Nicholson | | 46 | Detroit | **40 years.** Includes assault of federal officers. |
| Brian Sorrell | | 28 | Detroit | **21 years.** |
| Matthew Schamante | | 33 | Waterford | **102 months.** RICO conspiracy. |
| Sherman Brown | | 44 | Detroit | **100 months.** Conspiracy to commit murder in aid of racketeering. |
| Brian Jackson | | 48 | Detroit | **96 months.** Conspiracy to commit murder in aid of racketeering. |
| Brandon Paige | | 21 | Detroit | **90 months.** Conspiracy to commit murder in aid of racketeering. |
| Roger Valdes | | 30 | Pontiac | **49 months.** |
| Raynard Brown | | 39 | Detroit | Convicted, RICO conspiracy - not yet sentenced at publication |
| Vicente Phillips | | 51 | Pontiac | Convicted, RICO conspiracy - not yet sentenced |
| Maurice Williams | | 34 | Detroit | Convicted, RICO conspiracy - not yet sentenced |
| Christopher Odum | | 30 | Detroit | Convicted, conspiracy to commit murder in aid of racketeering - not yet sentenced |
| William Frazier | | 37 | Auburn Hills | Convicted, assault + firearm - not yet sentenced |

Rival clubs named: **Satan Sidekick MC** and **Hell Lovers MC**.

Prosecuted by DOJ Organized Crime and Gang Section trial attorney Joseph Wheatley with AUSAs
Christopher Graveline and Louis Gabel.

---

## Mafia Insane Vice Lords

Sentenced 2015-01-13 before U.S. District Judge Bernard A. Friedman. [legal-032]

**Christopher LaJuan Tibbs**, a/k/a **"Chief Fatah,"** 38, of Detroit - **346 months**.
Leader of the Michigan branch, a local faction of the Chicago-origin Vice Lord nation,
operating primarily on Detroit's east side. Convicted 2014-08-29 of aiding and abetting the
armed robbery of a Little Caesars in Redford, Sept 2013. He "blessed" the robbery as a gang
mission, sent four subordinates, instructed them on disabling cameras and phones, had them
diagram the store, and took the majority of the proceeds. Evidence showed he recruited
children and young adults, and ordered the murder of a witness in the case.

**First use of the federal criminal street gang enhancement in the Eastern District of
Michigan.**

---

## Almighty Vice Lords Nation / Traveling Vice Lords (TVL)

Convicted 2024-04-24 after a seven-week trial. [legal-038]

| Person | Age | Role | Outcome |
|---|---|---|---|
| Terry Douglas | 44 | **Chief** of the TVL branch | Convicted. RICO conspiracy with special findings for the 2020 murder and 280+ g crack conspiracy. Mandatory **35 years** to life. |
| Schuyler Belew Jr. | 31 | **Universal Elite** of the TVLs in Michigan | Convicted. Mandatory **20 years** to life. |
| Davun Baskerville | 34 | **Chief of Security** | Convicted. Killed the victim and shot a witness. Mandatory **20 years** to life. |
| Lawon Carter | 36 | | **Acquitted of RICO conspiracy.** Convicted of drug and firearm counts; 15-year mandatory minimum to life. |

The 2020 murder took place at the **Shirley-Plymouth playground** on Detroit's west side, in
broad daylight. Baskerville killed a 29-year-old man in front of his two young children and
shot and injured the children's pregnant mother, who had witnessed it.

Note the rank vocabulary - **Chief**, **Universal Elite**, **Chief of Security** - which is
AVLN-specific and worth preserving verbatim on member records rather than flattening to
"leader."

A prior trial in **November 2023** convicted three national leaders of the AVLN in Detroit.

---

## Latin Counts

Two events. [legal-036, legal-044, press-071]

Operates in **southwest Detroit** and the downriver communities of **Lincoln Park** and
**Ecorse**. Eleven defendants in the racketeering indictment.

**Five guilty pleas unsealed 2017-01-23**, each facing 30 years:

| Person | Age | From | Admitted conduct |
|---|---|---|---|
| Devin Dantzler | 21 | Ecorse | Shot and killed **Mustafa Al-Yasiry** at the Big Apple Market, SW Detroit, **2014-04-18** |
| Victor Vasquez | 26 | Detroit | Responsibility for the Al-Yasiry death |
| Jonathan Estrada | 27 | Lincoln Park | Killing of **Terrence McClearen** + shooting of another victim, **2013-08-18** |
| Jesus Rodriguez | 25 | Lincoln Park | Same |
| Angel Rodriguez | 21 | Lincoln Park | Same |

Three other members had already pleaded guilty to roles in the Al-Yasiry murder. Jesus and
Angel Rodriguez are described as brothers.

**Christopher Nicholas Rishell**, a/k/a **"C-5,"** 30, of Lincoln Park - **20 years**,
sentenced 2019-12-03 by Judge Robert H. Cleland for assault with a dangerous weapon in aid of
racketeering. He was **president of the Toledo Mafia Counts set** of the Latin Counts, and
orchestrated a drive-by in a residential SW Detroit neighbourhood on **2017-10-07** that
killed one and injured two. Seven members were charged over that shooting; all pleaded guilty.

---

## YNS (Young and Skantless)

Superseding indictment unsealed 2017-05-12. [legal-041, press-126]

Operates in **northwest Detroit**, specifically the **Brightmoor** neighbourhood. The
indictment alleges YNS deliberately cultivated a reputation for ruthless violence and had
become the most dangerous group in Brightmoor and one of the most dangerous in the city -
partly by posting intimidating photographs and videos to social media.

| Person | Age | Charges |
|---|---|---|
| Corey Toney | 36 | RICO conspiracy; possession with intent to distribute |
| Edward Tavorn | 30 | RICO conspiracy; felon in possession |
| Andre Chattam | 27 | RICO conspiracy; murder in aid of racketeering; firearm causing death |
| Kevin Pearson | 25 | RICO conspiracy; murder in aid of racketeering; firearm causing death |
| Sontez Wells | 23 | Murder in aid of racketeering; firearm causing death |

All **charged** only.

---

## 6 Mile Chedda Grove

Indictment and arrests 2016-06-29. [legal-034, press-136, press-098]

Operates primarily on Detroit's **east side**; the indictment describes murders, assaults,
robberies and firearms/narcotics trafficking in metro Detroit and other states.

| Person | Aliases | Age | Charges |
|---|---|---|---|
| Edwin Lamont Mills | Edboy | 26 | 2 counts each: murder in aid of racketeering, assault with a dangerous weapon in aid of racketeering, firearm during a crime of violence causing death |
| Carlo Dajuan Wilson | Los | 22 | Same |

Both charged over a **2015-12-01** afternoon shooting near a market on **Hayes Street**,
east side: gunmen fired at a car, killing the 21-year-old driver and a 13-year-old passenger,
and pistol-whipping two other victims aged 13 and 7, causing serious injury.

Eleven 6 Mile Chedda Grove members were charged with racketeering conspiracy in total.
Rapper **Phillip Peaks ("Team Eastside Peezy")**, 29, is under indictment alongside ten
members and associates. [press-124]

---

## Bandgang

Convictions announced 2018-11-29. [legal-046, press-127]

A west-side Detroit gang whose economics were **credit card fraud and identity theft**, not
drugs - which makes it an outlier in this corpus and drove the violence directly.

| Person | Age | Outcome |
|---|---|---|
| Martez Bailey | 24 | Pleaded guilty before Judge David M. Lawson; plea calls for **25-30 years** |
| Khalil Wilson | 25 | Pleaded guilty earlier; plea calls for **25-30 years** |

On **2016-06-21** the two drove to **Biltmore Street** and fired repeatedly into a house
hoping to kill two rival gang members. Bailey fired a .45; Wilson emptied an Uzi with a
50-round extended magazine. A woman in the house, unconnected to any gang, was severely
injured.

The dispute was with rivals **Trust No One (TNO)** and **Too Much Cash (TMC)**, driven
largely by jealousy over credit card fraud proceeds, and by an earlier Bandgang shooting in
**February 2016** that left a five-year-old girl permanently disabled.

Scale of the wider investigation: **24 members and associates charged across 16 cases**,
sentences from 36 to 154 months; four credit card labs seized; **over 15,000 stolen credit
card accounts** linked to the gang.

Note: DOJ releases spell this both "Bandgang" and "Band Gang," and separately reference a
**"Band Crew"** gang - see the naming caution in `sets.md`.

---

## Hustle Boys

Sentenced 2013-06-04 before U.S. District Judge Patrick J. Duggan. [legal-043, press-112]

**Jeron Gaskin**, 22, of Detroit - **30 years** for drug trafficking, plus 46 months
concurrent for witness tampering (he admitted threatening the life of a witness, the
witness's minor child, and the child's mother before trial). Convicted by a jury Nov 2012.

From 2007 to March 2011 the conspiracy moved thousands of OxyContin, Opana and other
prescription pain pills from Detroit to **southern Ohio and West Virginia**, selling from
hotel rooms and three residences. Members at times **traded pills for firearms** and brought
the guns back to Detroit. A house on **Hamburg Street** in Detroit was used to store and
package the pills and to hold firearms and cash.

Co-defendants (all pleaded guilty before trial):

| Person | Sentence | Note |
|---|---|---|
| Darrell Ewing | 180 months | Also serving **life** for murder in MDOC |
| Mark Davis | 155 months | Also serving 3 years in Ohio DRC |
| Delmerey Morris | 144 months | Also serving **35-60 years** for murder in MDOC |
| Deonte Morris | 130 months | |
| William Crews | 50 months | Also serving 3 years in Ohio DRC |
| Pinkie Lewis | 1 year + 1 day | |
| Ashley Sallad | 1 day + 3 years supervised release | |
| Randi Fortner | indicted, S.D. W. Va. | Facing pretrial detention and removal |
| William Beal | charge dismissed | Following a guilty plea and sentence in a federal carjacking case |

Deonte and Delmerey Morris share a surname - likely brothers, unconfirmed.

---

## Delmarco Craig (no gang affiliation stated)

Arrested 2021-06-02 on felon-in-possession and machine gun charges. [legal-031]

Included because it is a clean, well-documented example of **social media driving a firearms
case**, and because NIBIN tied one rifle to seven shootings.

ATF reviewed an Instagram account Craig used to post photographs and live streams showing him
posing with firearms, including a Glock fitted with a conversion device. A search of his
residence recovered that Glock and six other firearms, two stolen, plus a tan and black
Palmetto State Armory 5.56 AR rifle with an obliterated serial number partly covered by a
black skull decal. On **2021-05-25** Craig streamed an Instagram Live brandishing what
appeared to be the same rifle.

NIBIN connected that rifle to **seven shootings since October 2020**, including:
- a homicide and double non-fatal shooting on **2021-05-25 at ~23:20**, near
  **8576 Strathmoor Street** - hours after the live video
- a shooting at a **CVS on Grand River Avenue on 2021-04-16**, where surveillance captured a
  newer-model white Escalade with black tires, rims and grille

A stolen 2021 white Cadillac Escalade was recovered from his backyard, containing a purple
LA Dodgers hat he often wore on Instagram.

---

## Cases in the corpus that are not Detroit

Fetched and stored, but out of scope for a Detroit universe. Listed so nobody re-fetches them:

- **Eight Maryland TTG members** convicted of RICO, nine murders [legal-039]
- **Holland Latin Kings**, W.D. Mich., final two sentenced [legal-040]
- **People v. Harris**, Supreme Court of Illinois, 1988 [legal-051, blocked]
- Toledo, Kalamazoo, Flint, Paterson NJ, St. Louis and West Virginia items in the press set

The West Virginia material is *arguably* in scope: both the Hustle Boys and Smokecamp ran
pills into southern Ohio and West Virginia, so `press-092` and `press-110` document a genuine
Detroit export route rather than an unrelated city.
