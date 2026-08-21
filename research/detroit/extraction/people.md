# Detroit people from primary sources

Extracted 2026-08-21 from `../raw/fetched/`. Consolidated roster of every named individual in
the fetched corpus who is a candidate `Member` record, with the set, the evidentiary status,
and the source. Full case context is in `federal-cases.md`.

**Nothing here has been written to the database.**

## Seeding notes

- The wiki is **nickname-first**: `display_name` uses the nickname by default, and the legal
  name only when `nickname_unknown=True`. Most people below have a documented alias, so the
  alias is the display name and the legal name goes in the name fields.
- **Status column** is evidentiary, not the `MemberStatus` enum. The rightmost column maps to
  the enum: `LOCKED` for anyone serving a sentence, `DEAD` for the killed, `FREE` where a
  source records release or acquittal, `UNKNOWN` otherwise.
- **Do not infer `DEAD` from a long sentence** and do not infer `FREE` from an acquittal on
  one count where other counts convicted.
- Ages are **as reported at the time of the source**, not current. Store them as a birth-year
  estimate at `Y` precision with `approx=True`, or not at all - never as a current age.

---

## Leadership

The clearest organisational signal in the corpus. Each of these is sourced to a court record
that states the rank explicitly.

| Person | Alias | Set | Rank as stated | Outcome | Enum |
|---|---|---|---|---|---|
| Antonio Johnson | Mister Tony, MT, Big Bro | Phantom OMC / Vice Lords | **National President** of the Phantoms *and* **"Three-Star General"** of the Vice Lords in Michigan | 35 years | LOCKED |
| Christopher LaJuan Tibbs | Chief Fatah | Mafia Insane Vice Lords | **Leader, Michigan branch** | 346 months | LOCKED |
| Terry Douglas | | Traveling Vice Lords | **Chief** of the TVL branch | 35 years to life | LOCKED |
| Schuyler Belew Jr. | | Traveling Vice Lords | **Universal Elite** in Michigan | 20 years to life | LOCKED |
| Davun Baskerville | | Traveling Vice Lords | **Chief of Security** | 20 years to life | LOCKED |
| Ramiah Jefferson | Nightmare | Bounty Hunter Bloods | **Leader** | 30 years | LOCKED |
| Jerome Hamilton | | Rollin 60s Crips (Detroit) | **Founder** of the Detroit line, 2008 | 30 years | LOCKED |
| Darriyon Mills | | Rollin 60s Crips (Detroit) | **Second-in-command** | 24 years | LOCKED |
| Christopher Nicholas Rishell | C-5 | Toledo Mafia Counts (Latin Counts) | **President** of the set | 20 years | LOCKED |
| Corey Bailey | Cocaine Sonny, Sonny | Seven Mile Bloods | **Leader** | charged, 11 counts | LOCKED |
| Billy Arnold | B-Man, Berenzo, Killa | Seven Mile Bloods | **Leader** | charged, 31 counts, DOJ sought death | LOCKED |
| Devon McClure | Block | Seven Mile Bloods | **Leader** | killed 2015-05-01 | DEAD |
| Robert Brown | RO Da Great | Seven Mile Bloods | **Founding member** | charged, 7 counts | LOCKED |

## Seven Mile Bloods

| Person | Alias | Status | Enum | Source |
|---|---|---|---|---|
| Corey Bailey | Cocaine Sonny, Sonny | Charged. Acquitted of first-degree murder in 2010. 55 months for a federal gun crime after a Jul 2014 arrest. Took part in "Stop the Violence" in 2013 while gang-active. | LOCKED | press-125 |
| Billy Arnold | B-Man, Berenzo, Killa | Charged, 31 counts incl. 2 murders and 9 attempted murders. Former handyman. | LOCKED | press-125 |
| Robert Brown | RO Da Great | Charged, 7 counts. Threatened a witness via a rap track. | LOCKED | press-125 |
| Jeffery Adams | Brick, Product | **Hung jury** March; awaiting retrial. Linked to `000_big_blood`. | LOCKED | press-125 |
| Arlandis Shy | Grymee, VIL | Charged, 11 counts. Clinton Township. | LOCKED | press-125 |
| Michael Rogers | | **Acquitted 2018-03-16.** Freed after "two years and 15 days." Wrote a novel in prison; renounced music. | FREE | press-124 |
| Donell Hendrix | Hardwork Jig | Charged. Rapper. Survived being shot Aug 2014. | UNKNOWN | press-122 |
| Devon McClure | Block | **Killed 2015-05-01.** Unsolved. | DEAD | press-122 |
| Jason Gill | White Boy | **Killed Feb 2015**, age 30. | DEAD | press-122 |
| Aaron Hayes | | **Killed Sept 24** (year inferred 2017), age 27. Bounty believed on his head. | DEAD | press-124 |
| Jerome Gooch | | Co-defendant, shot during the war | UNKNOWN | press-122 |
| Quincy Graham | | Co-defendant, shot during the war | UNKNOWN | press-122 |
| Matleah Scott | M Thang | Associate. McClure's girlfriend. Ran reconnaissance for Arnold. Plea deal on file. | UNKNOWN | press-123 |
| Ihab Maslamani | | Seven Mile Blood Juniors. Convicted of the Matt Landry killing; the Juniors renamed themselves Hobsquad in his honour. | LOCKED | press-122 |
| Michael Davis | | Witness, age 27. **Indicted for refusing to testify.** Shot in the incident that killed Djuan Page. | LOCKED | press-122 |
| Jonathan Murphey | Bleek | Former member turned witness. Testified despite the threat track. | UNKNOWN | press-125 |

## Smokecamp / OPB - all charged 2017-11-08

| Person | Aliases | Age | From |
|---|---|---|---|
| Korey Sanders | No Loan Corleon, Stax | 26 | Detroit |
| Jerray Key | Chino, Dre | 28 | Canton |
| Caraun Key | Luch, Ron, Slick | 26 | Detroit |
| Darryl Key | DB, Big Baby | 27 | Detroit |
| Deshawn Langston | Pook, Slips | 26 | Detroit |
| Richard Langston | Dub, Rich, Blow | 27 | Detroit |
| Antonio Langston | Tone | 29 | Detroit |
| Hakeem Bunnell | LB Dub | 24 | Detroit |
| Keenan Nielbock | Dolla, Keno | 30 | Taylor |
| Tyree Williams | Snoop | 24 | Detroit |
| Romale Gibson Jr. | Santana | 24 | Detroit |
| Cary Dailey | Cease | 28 | Detroit |
| Carlos Davis | Los, Loso | 24 | Detroit |

Three Keys and three Langstons in one indictment - candidate family links.

## Bounty Hunter Bloods

| Person | Alias | Age | Outcome | Enum |
|---|---|---|---|---|
| Ramiah Jefferson | Nightmare | 27 | 30 years | LOCKED |
| Evan Johnson | Unkle Murda | 24 | 30 years | LOCKED |
| Alexander Deshawn George | Bullet | 20 | 18 years | LOCKED |
| David Lamar Gay | Glock | 22 | 17.5 years, murder in aid of racketeering. Toledo, OH. | LOCKED |
| Drakkar Beral Cunningham | Rellz | 25 | 5 years | LOCKED |
| Everette Ramon George | Klout | 21 | 4 years 9 months | LOCKED |
| Marcus Andre Harvey | Ceasar | 23 | Convicted; sentencing 2016-05-02 | LOCKED |
| Mario Garnes | Bloodhound | 28 | 42 months | LOCKED |
| Gerald Deshawn Turner | G-Red | 25 | **Time served** + 3 years supervised release | FREE |
| Jamare Rucker | | | 33-60 years, second degree murder (Wayne County) | LOCKED |
| Jeremy Jackson | | | 33-60 years, second degree murder (Wayne County) | LOCKED |
| Jayjuan Watts | | | **Life**, main shooter, Marquise Robinson murder | LOCKED |

The two Georges share a surname and are close in age - likely brothers, unconfirmed.

## Playboy Gangster Crips - all charged October 2017

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

Every one of the fourteen has a documented alias, which makes this the cleanest set in the
corpus for nickname-first seeding.

## Phantom Outlaw MC / Vice Lords

| Person | Alias | Age | From | Outcome | Enum |
|---|---|---|---|---|---|
| Antonio Johnson | Mister Tony, MT, Big Bro | 39 | Detroit | 35 years | LOCKED |
| Marvin Nicholson | | 46 | Detroit | 40 years | LOCKED |
| Brian Sorrell | | 28 | Detroit | 21 years | LOCKED |
| Matthew Schamante | | 33 | Waterford | 102 months | LOCKED |
| Sherman Brown | | 44 | Detroit | 100 months | LOCKED |
| Brian Jackson | | 48 | Detroit | 96 months | LOCKED |
| Brandon Paige | | 21 | Detroit | 90 months | LOCKED |
| Roger Valdes | | 30 | Pontiac | 49 months | LOCKED |
| Raynard Brown | | 39 | Detroit | Convicted, unsentenced at publication | LOCKED |
| Vicente Phillips | | 51 | Pontiac | Convicted, unsentenced | LOCKED |
| Maurice Williams | | 34 | Detroit | Convicted, unsentenced | LOCKED |
| Christopher Odum | | 30 | Detroit | Convicted, unsentenced | LOCKED |
| William Frazier | | 37 | Auburn Hills | Convicted, unsentenced | LOCKED |

## Latin Counts

| Person | Alias | Age | From | Outcome | Enum |
|---|---|---|---|---|---|
| Christopher Nicholas Rishell | C-5 | 30 | Lincoln Park | 20 years | LOCKED |
| Devin Dantzler | | 21 | Ecorse | Pleaded guilty; shot and killed Al-Yasiry | LOCKED |
| Victor Vasquez | | 26 | Detroit | Pleaded guilty | LOCKED |
| Jonathan Estrada | | 27 | Lincoln Park | Pleaded guilty | LOCKED |
| Jesus Rodriguez | | 25 | Lincoln Park | Pleaded guilty | LOCKED |
| Angel Rodriguez | | 21 | Lincoln Park | Pleaded guilty | LOCKED |

Jesus and Angel Rodriguez are described as brothers.

## YNS - all charged 2017-05-12

| Person | Age | Charges |
|---|---|---|
| Corey Toney | 36 | RICO conspiracy; PWID |
| Edward Tavorn | 30 | RICO conspiracy; felon in possession |
| Andre Chattam | 27 | RICO conspiracy; murder in aid of racketeering |
| Kevin Pearson | 25 | RICO conspiracy; murder in aid of racketeering |
| Sontez Wells | 23 | Murder in aid of racketeering |

## 6 Mile Chedda Grove

| Person | Alias | Age | Status | Enum |
|---|---|---|---|---|
| Edwin Lamont Mills | Edboy | 26 | Charged, 2 murders in aid of racketeering | LOCKED |
| Carlo Dajuan Wilson | Los | 22 | Charged, 2 murders in aid of racketeering | LOCKED |
| Phillip Peaks | Team Eastside Peezy | 29 | Rapper. Under indictment with 10 members/associates. Shot and wounded 2018-02-04. | UNKNOWN |

## Bandgang

| Person | Age | Outcome | Enum |
|---|---|---|---|
| Martez Bailey | 24 | Pleaded guilty; plea calls for 25-30 years | LOCKED |
| Khalil Wilson | 25 | Pleaded guilty; plea calls for 25-30 years | LOCKED |

## Hustle Boys

| Person | Outcome | Enum |
|---|---|---|
| Jeron Gaskin | 30 years + 46 months concurrent for witness tampering | LOCKED |
| Darrell Ewing | 180 months federal; also serving **life** for murder (MDOC) | LOCKED |
| Mark Davis | 155 months; also 3 years Ohio DRC | LOCKED |
| Delmerey Morris | 144 months; also **35-60 years** for murder (MDOC) | LOCKED |
| Deonte Morris | 130 months | LOCKED |
| William Crews | 50 months; also 3 years Ohio DRC | LOCKED |
| Pinkie Lewis | 1 year + 1 day | LOCKED |
| Ashley Sallad | 1 day + 3 years supervised release | FREE |
| Randi Fortner | Indicted, S.D. W. Va. | UNKNOWN |
| William Beal | Charge dismissed after a plea in a federal carjacking case | UNKNOWN |
| Darnell Canady | Age 26. Shooting **victim** twice in 2015; testified. | UNKNOWN |

Deonte and Delmerey Morris share a surname - likely brothers, unconfirmed.

Darrell Ewing and Delmerey Morris both carry state murder sentences on top of the federal
term. The wiki has no field for concurrent sentences across jurisdictions; put the second
sentence in member notes rather than overwriting the release date.

## Victims and bystanders

Not gang members on this evidence. Worth `Member` records only where an incident needs a
`VICTIM` participant, and `nickname_unknown=True` in every case.

| Person | Age | Incident | Outcome |
|---|---|---|---|
| Courtney Meeks | | CVS Schaefer Road carjacking, Feb 2014. Security guard, killed preventing the carjacking of a mother and infant. | KILLED |
| Mustafa Al-Yasiry | | Big Apple Market, 2014-04-18 | KILLED |
| Terrence McClearen | | 2013-08-18 | KILLED |
| Cleo McDougal | 25 | Jun 2006 | KILLED |
| Matt Landry | 21 | Abducted 2009 in Eastpointe | KILLED |
| Kionte / Kiontae Atkins | 34 | Drive-by, 2011-08-08 | KILLED |
| Marquise Robinson | | Killed for refusing to aid a Bounty Hunter member | KILLED |
| Djuan Page | | Neff. Jul 2014. Killing triggered the anti-SMB alliance. | KILLED |
| Dvante Roberts | 19 | "Little." Duchess and Craft, 2015-05-08 | KILLED |
| Darrio Roberts | | Brother of Dvante. Shot in the head, survived. | INJURED |
| Marquis Wicker | 25 | Hit nine times, survived. Testified. | INJURED |
| Ralpheal Carter | | Southfield pool party, Jul 2015. **Paralysed.** | INJURED |
| Bernice Griffin | 70 | Neighbour and witness, Duchess and Craft | UNHARMED |

Two child victims of the 2015-12-01 Hayes Street shooting (aged 13 and 7) and the 13-year-old
passenger killed are **unnamed** in the source, as is the 21-year-old driver. Do not invent
names; seed the incident with unnamed participants or none.

The 2020 Shirley-Plymouth playground victim is given only as **"J.G."** in the DOJ release
[legal-038] - initials, deliberately. Leave it that way.

## Officials

Not `Member` records. Listed so their names are not mistaken for participants during any
automated extraction pass.

**Judges:** George Caram Steeh, Nancy G. Edmunds, Paul D. Borman, Bernard A. Friedman,
Patrick J. Duggan, Robert H. Cleland, David M. Lawson, Mona Majzoub (magistrate).

**Prosecutors:** Barbara L. McQuade, Daniel L. Lemisch, Matthew Schneider, Dawn N. Ison,
Saima Mohsin (US Attorneys); Julie Finocchiaro, Joseph Wheatley (DOJ); Christopher Graveline,
Louis Gabel, Eric Doeh, Andrew Goetz, Eaton Brown, Shane Cralle, Terrence Haugabook,
Louis Crisostomo, Robert VanWert, Eric Straus, Mark Chasteen, Margaret Smith, Jeanine Brunson,
Trevor Broad (AUSAs).

**Law enforcement:** James Craig, James E. White (DPD chiefs); Robin Shoemaker, Steven
Bogdalek, James Deir, Marcus Watson (ATF); Paul M. Abbate, David P. Gelios, Timothy R. Slater,
Robert D. Foley III (FBI); Steve Francis (HSI); Bill Dwyer (Warren PD).

**Other:** Robert Snell (Detroit News reporter, "Death by Instagram"); Carl Taylor (MSU
sociologist); Avneesh Gupta (assistant Wayne County medical examiner); Vincent Toussaint
(defence lawyer).
