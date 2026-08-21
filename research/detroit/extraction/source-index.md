# Detroit source index

Every citation from `sources/legal-sources.txt` and `sources/press-sources.txt`, with the
result of a fetch run on 2026-08-21 and a proposed reliability rating for the wiki's
`Source` entity. Recovered full text lives in `../raw/fetched/<id>.txt`.

Ratings follow the `SourceReliability` enum: `HIGH` = primary court record or federal
agency release; `MEDIUM` = established news outlet; `LOW` = crime blog, rap/culture press
or aggregator; `UNVERIFIED` = forum, wiki-style site or user-generated post.

**Nothing here has been written to the database.**

## Fetch results

| Result | Count |
|---|---|
| fetched | 97 |
| no text recovered | 29 |
| blocked (Cloudflare) | 11 |
| fetch error | 6 |
| not a source | 4 |

**97 of 147** documents yielded usable text.

The blocked and errored ones are not dead links, they are refusals: `documentcloud.org`,
`law.justia.com`, `casetext.com`, `casemine.com`, `leagle.com`, `mlive.com` and
`cases.justia.com` all sit behind Cloudflare and return 403 to this server's datacenter IP.
A browser on a residential connection reaches them normally, so these are worth opening by
hand rather than treating as lost. Two federal PDFs (`legal-045`, `press-064`) downloaded
successfully but are scanned images with no text layer and would need OCR.


## Legal and documentary sources

| ID | Rating | Outlet | Title | Status |
|---|---|---|---|---|
| - | HIGH | casemine.com | United States v. Fisher / Case No. 15-20652 / E.D. Mich. / Judgment / Law / Ca | no text recovered |
| - | HIGH | casemine.com | United States v. Robert Brown D-6 / Case No. 15-20652 / E.D. Mich. / Judgment  | no text recovered |
| - | HIGH | cases.justia.com | 07a0738n-06-2011-02-25.pdf | fetch error |
| - | HIGH | cases.justia.com | Cash Flow Posse | fetch error |
| - | HIGH | cases.justia.com | COA 327731 PEOPLE OF MI V CORDELL DANIEL JONES Opinion - Per Curiam - Unpublis | fetch error |
| - | HIGH | casetext.com | BLOCK SQUAD | no text recovered |
| - | HIGH | casetext.com | People v. Chapel, No. 348244 / Casetext Search + Citator | no text recovered |
| - | HIGH | casetext.com | YOUNG CERIGNOLA | no text recovered |
| `legal-008-9078e767` | HIGH | courtlistener.com | People of Michigan v. Jajuan Marcellous Cannon – CourtListener.com | fetched |
| `legal-009-04bfaeeb` | HIGH | courtlistener.com | United States v. Ramiah Jefferson – CourtListener.com | fetched |
| - | HIGH | documentcloud.org | Bailey Fighting Old Murder | blocked (Cloudflare) |
| - | HIGH | documentcloud.org | Billy Arnold Death Penalty | blocked (Cloudflare) |
| - | HIGH | documentcloud.org | Billy Arnold Government Response to Bond motion | blocked (Cloudflare) |
| - | HIGH | documentcloud.org | Bloods List of Rap Videos | blocked (Cloudflare) |
| - | HIGH | documentcloud.org | Deadly impact in West Virginia | blocked (Cloudflare) |
| - | HIGH | documentcloud.org | Graham Motion to Suppress Rap Lyrics | blocked (Cloudflare) |
| - | HIGH | documentcloud.org | Jeffery Adams Plea Deal | blocked (Cloudflare) |
| - | HIGH | documentcloud.org | Matleah Scott Plea Deal | blocked (Cloudflare) |
| - | HIGH | documentcloud.org | Seven Mile Bloods 2018 Indictment | blocked (Cloudflare) |
| - | HIGH | documentcloud.org | Seven Mile Bloods Chronology | blocked (Cloudflare) |
| - | LOW | fr.scribd.com | Band Crew Indictment / Conspiracy (Criminal) / Intimidation | no text recovered |
| - | LOW | fr.scribd.com | Paperworks | not a source |
| - | LOW | fr.scribd.com | Related Through Money Indictment | no text recovered |
| `legal-023-81fc8b44` | HIGH | govinfo.gov | Microsoft Word - 15-20652-03 Fisher Amended M Suppress.docx - USCOURTS-mied-2_ | fetched |
| `legal-024-985fd2f4` | HIGH | govinfo.gov | Microsoft Word - 15-20652-04 Bailey M Suppress cell phone evidence.docx - USCO | fetched |
| `legal-025-454a235f` | HIGH | govinfo.gov | Microsoft Word - 15-20652.Davis.contempt.ord.docx - USCOURTS-mied-2_15-cr-2065 | fetched |
| `legal-026-18bbb893` | HIGH | govinfo.gov | PORTER SMB | fetched |
| `legal-027-c60548ee` | HIGH | govinfo.gov | S:\__Judge's Desk\14-20119 USA v. Jefferson -- Final Order Denying Rule 29 and | fetched |
| `legal-028-17395e42` | HIGH | govinfo.gov | S:\Hood\FILED OPINIONS AND ORDERS\2007\4 Apr 2007\stamper.op.wpd - USCOURTS-mi | fetched |
| `legal-029-10c2edd9` | HIGH | govinfo.gov | USCOURTS-mied-2_17-cr-20740-0.pdf | fetched |
| `legal-030-a85e63bb` | HIGH | govinfo.gov | YMF | fetched |
| `legal-031-1bbf4864` | HIGH | justice.gov | BIG HOMIE | fetched |
| `legal-032-7e54069d` | HIGH | justice.gov | Detroit Gang Leader Sentenced to 346 Months in Prison for Planning Armed Robbe | fetched |
| `legal-033-0276c136` | HIGH | justice.gov | Detroit Gang Leader Sentenced to 35 Years for Violent Racketeering-Related Cri | fetched |
| `legal-034-658e9ef3` | HIGH | justice.gov | Detroit One Collaboration Arrests Gang Members for Shooting Involving Children | fetched |
| `legal-035-22b8d725` | HIGH | justice.gov | Detroit One Collaboration Leads to 30-Year Sentence of Major Gang Leader for V | fetched |
| `legal-036-5a1679dc` | HIGH | justice.gov | Detroit One Collaboration Leads to Five Guilty Pleas for Latin Count Gang Memb | fetched |
| `legal-037-f0bea61d` | HIGH | justice.gov | Detroit One Collaboration Leads to Racketeering Indictment of Violent Gang Mem | fetched |
| `legal-038-e98ef0a4` | HIGH | justice.gov | Eastern District of Michigan / Three Members of a Violent National Gang Convic | fetched |
| `legal-039-029f19d4` | HIGH | justice.gov | Eight Maryland TTG Members and Associates Convicted on Federal Racketeering an | fetched |
| `legal-040-a1a2e188` | HIGH | justice.gov | Final Two Holland Latin King Gang Members Sentenced to Over 20 Years for Racke | fetched |
| `legal-041-75b6c599` | HIGH | justice.gov | Five Members of Violent Detroit Street Gang Charged with Racketeering, Narcoti | fetched |
| `legal-042-ebd5da3a` | HIGH | justice.gov | Gang-Drug Trafficking Organization Connections Affecting Suburban Areas - Atto | fetched |
| `legal-043-b74f97cc` | HIGH | justice.gov | Hustle Boys Gang Member Sentenced To 30 Years In Prison For Drug Trafficking C | fetched |
| `legal-044-4242305b` | HIGH | justice.gov | Latin Counts Gang Leader Sentenced to 20 Years in Prison for Orchestrating Dri | fetched |
| `legal-045-32ef8619` | HIGH | justice.gov | Six Men Charged for Roles in Scheme to Defraud Businesses of Luxury Goods and  | fetched |
| `legal-046-a26ea851` | HIGH | justice.gov | Two Gang Members Convicted Of Attempted Murder In Drive-By Shooting / USAO-EDM | fetched |
| - | HIGH | law.justia.com | PEOPLE OF MI V ANTONIO CADDELL :: 2020 :: Michigan Court of Appeals - Publishe | no text recovered |
| - | HIGH | law.justia.com | PEOPLE OF MI V DERRICO DEVON SEARCY :: 2014 :: Michigan Court of Appeals - Unp | no text recovered |
| - | HIGH | law.justia.com | PEOPLE OF MI V DONELL CHRISTOPHER THOMPSON :: 2018 :: Michigan Court of Appeal | no text recovered |
| - | HIGH | law.justia.com | PEOPLE OF MI V DONRIKO RUEMONDO-EMAN GOOSBY :: 2020 :: Michigan Court of Appea | no text recovered |
| - | HIGH | law.justia.com | People v. Harris :: 1988 :: Supreme Court of Illinois Decisions :: Illinois Ca | no text recovered |
| - | HIGH | leagle.com | PEOPLE v. SEARCY / Nos. 308101, 308527, 311177. / 20140328358 / Leagle.com | no text recovered |
| - | HIGH | leagle.com | U.S. v. ROBINSON / Case No. 15-20652-16. / By... / 20190118924/ Leagle.com | no text recovered |
| `legal-054-c2fb34b9` | HIGH | ncjrs.gov | 147227NCJRS.pdf | fetched |
| - | UNVERIFIED | streamable.com | Billy Arnold charges - Streamable | not a source |

## Press sources

| ID | Rating | Outlet | Title | Status |
|---|---|---|---|---|
| `press-056-b9a129d0` | MEDIUM | 13abc.com | Three suspects indicted in murder of Toledo toddler | fetched |
| `press-057-3d2c4cf0` | UNVERIFIED | answers.com | What street gangs are in Southwest Detroit - Answers | fetched |
| - | HIGH | ATF | Detroit One Collaboration Leads to Racketeering Indictment of Violent Gang Mem | no text recovered |
| - | HIGH | ATF | Latin Counts Gang Members Charged and Arrested for Committing a Shooting in So | no text recovered |
| `press-060-de0a0354` | MEDIUM | Bellingcat | bellingcat - Gangs of Detroit: OSINT and Indictment Documents - bellingcat | fetched |
| `press-061-ea0f8f10` | MEDIUM | CBS Detroit | Authorities: Leader Of Detroit’s Bounty Hunter Bloods Gang Gets 30 Years In Pr | fetched |
| `press-062-e25d5cf1` | MEDIUM | CBS Detroit | Local Gang Leaders Plead Guilty In Racketeering, Firearm Charges – CBS Detroit | fetched |
| `press-063-399bec58` | MEDIUM | CBS Detroit | playboy-ind.pdf | fetched |
| `press-064-0e673b91` | MEDIUM | CBS Detroit | us-district-court-detroit-11-1-17.pdf | fetched |
| `press-065-fe190963` | UNVERIFIED | chamspage.blogspot.com | Miscellaneous Posts: 2011 Detroit Homicide/Murder Victim List | fetched |
| `press-066-cf5ece07` | MEDIUM | ClickOnDetroit (WDIV) | (sans titre) | fetched |
| `press-067-3bb63b0e` | MEDIUM | ClickOnDetroit (WDIV) | 2 leaders of Detroit's Rollin 60s Crips street gang sentenced for racketeering | fetched |
| `press-068-d25f296a` | MEDIUM | ClickOnDetroit (WDIV) | Band Crew street gang leader sentenced to 20 years for violence, shootings in  | fetched |
| `press-069-93d9fa69` | MEDIUM | ClickOnDetroit (WDIV) | Defenders look at Detroit's criminal groups | fetched |
| `press-070-0d624aa8` | MEDIUM | ClickOnDetroit (WDIV) | Judge: CVS security guard killer is 'poster child' for gang life | fetched |
| `press-071-f480417f` | MEDIUM | ClickOnDetroit (WDIV) | Latin Counts gang member sentenced to 30 years in prison for southwest Detroit | fetched |
| `press-072-e652103a` | MEDIUM | ClickOnDetroit (WDIV) | Wrongfully imprisoned Detroit man sues city for $1.5 million | fetched |
| `press-073-b7b352af` | LOW | crimeindetroit.com | Microsoft Word - Document1 - 101905_Puritan_Avenue_Gang[1].pdf | fetched |
| - | HIGH | dea.gov | https://www.dea.gov/sites/default/files/states/newsrel/2003/detroit120403.html | no text recovered |
| `press-075-1edf4808` | MEDIUM | Deadline Detroit | Deadline Detroit / Did Napoleon Misspeak When He Said 'There Are No Organized  | fetched |
| `press-076-a1b80498` | MEDIUM | Detroit Free Press | Detroit leader of Bounty Hunter Bloods gang gets 30 years | fetched |
| `press-077-34724996` | MEDIUM | Detroit Free Press | Facebook, feds bust Rollin 60s Crips in Detroit, arrest 12 | fetched |
| `press-078-18788fd0` | MEDIUM | Detroit Free Press | Feds bust 8 gang members who bragged on Facebook, Twitter | fetched |
| `press-079-45fd8c9c` | MEDIUM | Detroit Free Press | Man cleared in killing as teen now part of gang bust | fetched |
| `press-080-084029b1` | MEDIUM | Detroit Free Press | Man gets prison in fatal shooting at Detroit drive-thru | fetched |
| - | UNVERIFIED | drive.google.com | Purple Heart Vets Full Indictment.pdf - Google Drive | no text recovered |
| `press-082-2f0859de` | MEDIUM | eu.northjersey.com | Archive: Brazen gangs in turf battle | fetched |
| `press-083-fe317b50` | UNVERIFIED | forms.cloud.microsoft | Formulaire d'inscription à l'association des anciens élèves du LFI de Dublin. | fetched |
| `press-084-4fbb3799` | MEDIUM | FOX 2 Detroit | 14 members of Detroit's Playboy Gangster Crips gang arrested for slew of crime | fetched |
| `press-085-83c830f5` | MEDIUM | FOX 2 Detroit | ICE raid leads to 1,000 gang arrests, including 20 in Michigan / FOX 2 Detroit | fetched |
| `press-086-9427ee2d` | MEDIUM | FOX 2 Detroit | More than 40 shots fired at scene of man's murder in Detroit / FOX 2 Detroit | fetched |
| `press-087-eb907cad` | MEDIUM | FOX 2 Detroit | Social media bragging by Detroit gang members lead to prosecution / FOX 2 Detr | fetched |
| `press-088-8455a04b` | MEDIUM | FOX 2 Detroit | Video of gunmen who murdered 21, 13-year-old in car released / FOX 2 Detroit | fetched |
| `press-089-eb758787` | LOW | Gangster Report | Chief Keef-Backed Rapper YNS Cheeks Charged In RICO, Named A Leader Of Detroit | fetched |
| `press-090-bfa3662f` | LOW | Gangster Report | Convictions Across The Board In Detroit Feds' Latest Assault Launched On Seven | fetched |
| `press-091-7b2274c4` | LOW | Gangster Report | PA Boys Power Slim Brantley Back On The Outside, Detroit Drug Chief Checks Int | fetched |
| `press-092-6b9fe772` | LOW | Gangster Report | Take Me Home, Country Roads: Feds Bag West Virginia Branch Of Detroit's 'Young | fetched |
| `press-093-9fb91393` | LOW | Gangster Report | The Face That Launched 1,000 Ships: SW Detroit Crime Lord Scarface Viramontez  | fetched |
| - | UNVERIFIED | gannett-cdn.com | 636600906950913275-gill-combo-wide.jpg (Image WEBP, 1900 × 1000 pixels) - Redi | no text recovered |
| `press-095-8e5214a2` | UNVERIFIED | Google (recherche) | Detroit Gang Map (W.I.P) - Google My Maps | fetched |
| - | UNVERIFIED | Google (recherche) | pa boys detroit indictment – Recherche Google | not a source |
| - | UNVERIFIED | Google (recherche) | smokecamp indictment - Recherche Google | not a source |
| `press-098-0057de05` | LOW | idoc.pub | 6 Mile Chedda Grove Indictment [x4e6jzzdy8n3] | fetched |
| - | UNVERIFIED | lipstickalley.com | I Want Some Detroit Gossip! Part II / Page 716 / Lipstick Alley | blocked (Cloudflare) |
| - | UNVERIFIED | media.mlive.com | Band Crew indictment.pdf | fetch error |
| - | UNVERIFIED | metrotimes.com | yns_superseding_indictment__1__2.pdf | fetch error |
| `press-102-643b2479` | HIGH | Michigan Courts | Block Squad | fetched |
| `press-103-8afff8f9` | HIGH | Michigan Courts | Kalamazoo | fetched |
| `press-104-be6599e2` | HIGH | mied.uscourts.gov | SCB | fetched |
| - | MEDIUM | MLive | A glimpse inside Detroit's 6 Mile Chedda Grove gang - mlive.com | no text recovered |
| - | MEDIUM | MLive | Flint street gang taken down by same law used against the mafia - mlive.com | no text recovered |
| - | MEDIUM | MLive | Flint's battlefield: A three-year homicide map - mlive.com | no text recovered |
| - | MEDIUM | MLive | Robert 'Fat Daddy' Taylor sentenced to life in prison for Matt Landry murder - | no text recovered |
| `press-109-100cac56` | MEDIUM | Motor City Muckraker | Detroit rappers take credit for brutal assault, robbery of Doughboyz star | fetched |
| `press-110-8d3dc320` | MEDIUM | Motor City Muckraker | Gangs from Detroit bring violence, drugs to West Virginia communities – Motor  | fetched |
| - | UNVERIFIED | newmcfallbrothersfuneral | Obituary for Davon Fondren / New McFall Brothers Funeral Home | no text recovered |
| `press-112-42beac21` | MEDIUM | officer.com | Cops Bust Detroit Hustle Boys Gang / Officer | fetched |
| `press-113-4740bc2e` | HIGH | opn.ca6.uscourts.gov | Bounty Hunter Bloods | fetched |
| `press-114-57b7c690` | MEDIUM | Patch | 9 More Alleged Gang Members Charged with Murder, Racketeering / Detroit, MI Pa | fetched |
| `press-115-45f1af19` | MEDIUM | Patch | Chaldean 'Godfather,' Other Metro Detroit Iraqis Can Stay 2 More Weeks / Detro | fetched |
| `press-116-21bc40b4` | MEDIUM | patersontimes.com | Paterson drug dealing ring linked to Bloods street gang broken up / Paterson T | fetched |
| - | UNVERIFIED | Reddit | Bigg 🕊 from Toledo’s Mafia Counts (TMC), a Latino gang in southwest detroit, h | no text recovered |
| - | UNVERIFIED | Reddit | The Color Red: Bringing Terror To Detroit's Eastside, Seven Mile Bloods Roll C | no text recovered |
| `press-119-0b5a959c` | LOW | Rolling Out | How Detroit Bloods used Instagram to fuel deadly gang war - Rolling Out | fetched |
| `press-120-8c4d2634` | MEDIUM | The Detroit News | 'Death by Instagram' trial ends in convictions | fetched |
| `press-121-bdc01b70` | MEDIUM | The Detroit News | Death by Instagram / Chapter 10: Rap tracks | fetched |
| `press-122-6354e80e` | MEDIUM | The Detroit News | Death by Instagram, Chapter 3: Smaller east-side gangs team up | fetched |
| `press-123-f7e78187` | MEDIUM | The Detroit News | Death by Instagram, Chapter 5: Laughing emojis mark another victim | fetched |
| `press-124-fee8cdf8` | MEDIUM | The Detroit News | Death by Instagram, Chapter 8: Fresh bloodshed as racketeering trials begin | fetched |
| `press-125-869d38e4` | MEDIUM | The Detroit News | Death by Instagram: Biographies of key figures in the deadly gang war | fetched |
| `press-126-1dcad6a0` | MEDIUM | The Detroit News | Feds: Brightmoor area gang waged murderous campaign | fetched |
| `press-127-59932281` | MEDIUM | The Detroit News | Free Band Gang stole $2M from Walmart during crime spree, feds say | fetched |
| `press-128-2dc3fd98` | MEDIUM | The Detroit News | Rapper Doughboy Roc targeted by feds before death | fetched |
| - | MEDIUM | The New York Times | AROUND THE NATION; Charges Against 6 Dropped In Illinois Prison Riot Trial - T | no text recovered |
| `press-130-cfb01038` | MEDIUM | The Toledo Blade | g13BLADEGangMap - Blade-gang-map-1.pdf | fetched |
| `press-131-c6502412` | MEDIUM | The Toledo Blade | The Blade obtains Toledo Police Department's “Gang Territorial Divisions” map  | fetched |
| `press-132-792de09f` | MEDIUM | theoaklandpress.com | Pontiac families grieve over six recent homicides WITH VIDEO / News / theoakla | fetched |
| `press-133-971b1596` | UNVERIFIED | thestreetsdontloveyoubac | REAL LIFE DETROIT GANGS FROM THE 70S ,80S,EARLY 90S – THE STREETS DON'T LOVE Y | fetched |
| - | LOW | unitedgangs.com | Hoover Criminals | no text recovered |
| `press-135-e8252f97` | MEDIUM | WXYZ Detroit | 2 people shot and killed on Detroit's west side | fetched |
| `press-136-3b115620` | MEDIUM | WXYZ Detroit | 6 Mile Chedda Grove gang members Edwin Mills and Carlo Wilson facing federal c | fetched |
| `press-137-13536a4a` | MEDIUM | WXYZ Detroit | Detroit Police Department arrests two men connected to murders of teens in par | fetched |
| `press-138-6d5fc943` | MEDIUM | WXYZ Detroit | Detroit's Most Wanted: Dejuan "Montana" Jackson is wanted for murder | fetched |
| `press-139-3d25224f` | MEDIUM | WXYZ Detroit | Detroit's Most Wanted: Jerome McNeil a documented member of the Bloods | fetched |
| `press-140-5294bf64` | MEDIUM | WXYZ Detroit | Gangs of Detroit: Videos bring spotlight to violence of city's organized crime | fetched |
| `press-141-c07f6bae` | LOW | xxlmag.com | Doughboy Roc of Doughboyz Cashout Shot and Killed in Detroit - XXL | fetched |
| `press-142-249383de` | LOW | Stone Greasers | Venturers - The Death of DOC - Desi's Story | fetched |
| - | UNVERIFIED | Michigan Mugshot Search | Michigan Mugshot Search | fetch error |
| `press-144-a3e904a1` | MEDIUM | 13abc (WTVG Toledo) | Chase suspects were under investigation for counterfeiting, buying guns | fetched |
| - | MEDIUM | St. Louis Post-Dispatch | Man gets 15 years for his role in St. Louis County murder, kidnapping / Metro  | no text recovered |
| `press-146-bd2f0eb0` | MEDIUM | Downriver Sunday Times | Dearborn police provide updates on recent arrests, ongoing cases | fetched |
