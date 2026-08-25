# TTO - the killing of Tay, and the DWBI threads

Six r/CrimeInTheD threads, read 25 August 2026. Two of them are hours old and are what
started this; the rest came out of the local mirror and Arctic Shift behind them.

    1cxex86  2024-05-21  "(TTO) Dirty got locked for shooting (Dwbi) Dez 12 times last
                          year and Trey Trey killer is affiliate with tto , why is 8
                          still fw tto 😂?"                                    +5,  20c
    1cxd82a  2024-05-21  "Damn dawg so ya tellin me the big homie fakin like that..
                          then why tto darri act like big homie was a big dawg" +0,  18c
    1flang2  2024-09-20  "Did TTO Darri backdoor TTO Tay & if he did why?"     +41,  68c
    1ftr0o2  2024-10-01  "No Way Darri Did That"                               +7,   24c
    -        2026-08-25  "Darri must not be TTO no more"                       +3,    3c
    -        2026-08-25  "Damn ts wild"                                        +43,  50c

Method, so nobody re-runs it: `reddit_mirror.py search "<term>" --comments` answers the
corroboration questions locally and instantly, but its comment sync stops at 2024-08-09,
so anything later needs `reddit_fetch.py thread <id>` against Arctic Shift. Post *titles*
are mirrored to 2026-08-21, which is how the September 2024 thread was found at all.
Arctic Shift's `posts --query` was timing out on the day, and neither 2026 thread was in
the archive yet, so those two have no permalink here.

Two scripts wrote the result, each carrying its reasoning in its docstring:
`tools/seed_tto_dwbi_thread.py` and `tools/seed_tto_tay_killing.py`. Both idempotent.

## The killing of Tay, Houston, September 2024

Seeded as a `MURDER`: Tay victim and killed, **Darri** shooter. Location `Houston, Texas`,
so no `municipality_id`. Date September 2024 at month precision, approx.

The date is inferred, and this is the whole of it: no source gives one. By 2024-09-20 the
funeral had already been held (u/SpreadPrior9553, +17: "Darri didn't even attend the
funeral so the rumor might be true") and both suspects had been off Instagram "in 2 weeks".
No press account exists - searched, and nothing in Houston or Detroit coverage matches.

**Who.** In September 2024 this was a rumour with a name on it: "Rumor says Darri & Baby
Jay did that shit". By 25 August 2026 the sub argues about everything except that -
"This aint shit new 😂 mfs been knew this why you think j rock dont be around darri nomo"
(+30), "I swear everybody knew this", "facts been spoke on it", "People in this sub were
saying it was Darri and Baby Jay when it happened". Not one commenter in the 2026 thread
disputes it. That is what moved it from a note to an incident row.

**Why.** The motive corrected itself over two years and the correction is the interesting
part. September 2024: Tay ran off with a load - "He ran off wit darri shipment", "I heard
he ran off with some work". 2024-10-02, u/AggravatingIce999: "They saying tay ain't run
off darri just jumped the gun early no pun intended". August 2026 completes it -
u/HatingAssNgga55 (+17): "Allegedly Darri thought Tay ran off with some pape whole time
TSA took it", and when asked how Darri could not believe an airport seizure receipt,
"Darri thought tay made fake papers". Tay had flown down to clear it up.

**Kin.** Tay is **Quwan's brother**, said independently in all three commented threads
(u/AdvantageAny5819 + u/Kingz810 in September 2024, u/AggravatingIce999 in October,
u/HatingAssNgga55 in 2026: "that's his dead bestfriend brother"). Quwan is created here so
the `family` link has something to point at: he is on file in the corpus as a TTO body -
`../../privedatabase/detroit.md` line 482 has 30 Boys' Lil B carrying "Corps: Quwan (TTO)"
- and Darri had ridden for him, "the nigga who was innat car the most fa quwan", his
Instagram "damn near dedicated to dog".

Tay is **886 Tay** in the September 2024 thread. 886 is already TTO's number in
`sets.name_variants`, which is the independent check that the man seeded off the roster
and the man these threads are about are the same man.

**Not written: Baby Jay** (also rendered "southwest jay"), named twice in 2024 as the
second man and never again. No set, no other mention, no member row.

## The DWBI threads, May 2024

| Member | Set | Enum | What it rests on |
|---|---|---|---|
| Dirty | TTO | LOCKED | Both May 2024 threads, two posters. u/Environmental-Rub669, 2023-12-16: "He snitched on TTO Dirty" - the case is on file five months before either post. |
| Dez | DWBI | FREE | Shot and survived. u/Choice_Marketing9481 (2024-05-31) has him on Instagram "everyday", so he is alive after it. |
| Trey Trey | DWBI | DEAD | `raw/murders.txt` line 34 carries him independently as "Trey🕊️(DWBI/TOB)". |
| 8 | DWBI | UNKNOWN | u/Prestigious-Slip-787, 2024-07-19: "He exposed 8 and the rest of Dwbi for being fakers". |

**The shooting of Dez**, 2023, Detroit, `SHOOTING`: Dirty shooter and unharmed, Dez victim
and injured. "Last year" in a post dated 21 May 2024 is 2023 at year precision. The count
is twelve in the post title and twelve again from u/Tweaker-Taliban44 on 2024-06-09 ("Dez
did get popped 12x by them TTO niggas"); u/Confident_Society927 says eleven the same day as
the post. Twelve is written. Neither thread locates it, so the incident carries the
Detroit municipality and nothing finer - a gap, not a fact.

**Not written: who killed Trey Trey.** The post says a TTO *affiliate*.
u/Affectionate_Mud8033 says flatly "TTO killed (Dwbi) Trey Trey". But u/Treeymafiapantts
wrote on 2023-08-02 that "it ain't never been a single post or comment in this sub that
talked about tto killing trey trey", and a month later credited it to a **Dre**: "the beef
started because Dre killed trey trey". Three accounts, three attributions. He is seeded
DEAD with no death incident until one of them gets a second source.

**Not written: a TTO x DWBI edge.** u/ChampionshipNo2530, mid-argument: "I thought dwbi
fuck with tto tho shit I guess it be mini beefs in cliques". And `raw/murders.txt` line 60
carries **Kook/KJ🕊️ (TTO / DWBI)** - one dead man tagged to both. The 2026 poster assumes
the opposite ("ain't TTO and DWBI beefing or sum shiii?"). Ally and enemy are both
arguable, so neither is written.

## Darri

Seeded FREE, TTO, rapper. Everything else about him stayed out of the database:

- **Rank.** u/Carl_da_JungOG (+10): "Darri the youngest in charge and a real threat on
  these streets ... he earned his respect at a young age". u/Slimewave6, same thread:
  "Darri ain't tough as u think he is", "was not tough school like at all can't even
  fight", "He not original TTO". u/BennyFrankFrank: "He ran from Cino in Somerset".
  Reputation, argued both ways, by anonymous accounts. Not a `member_set.rank`.
- **Whether he is still TTO.** u/Tiny_Examination1251, 2026-08-25: "Darri ain't been
  around them boys a min now even before the tay situation"; the poster's own read is
  that he "happened to be gang but also does his own thing". First suggestion the
  affiliation lapsed, but nobody dates it and nobody says he left. His TTO spell stays
  open until something does.
- **Rapper** is a column, and it rests on a located record: "Gang Only (feat. King Von)",
  released 28 February 2019. Written up in `../sources/music-credits.md`.
- **Still free.** u/No-Neighborhood-7228, 2026-08-25: "It really is insane how much we
  know about all of this (so the PD HAS to know right?) and he's still a free man
  somehow?". Status FREE is doing exactly that work.

## Leads still to place

- **u/Environmental-Rub669: "I actually got the paperwork to that case"** (2024-05-22),
  and it is the same account that posted "He snitched on TTO Dirty". If Dirty's case
  number surfaces, MDOC OTIS gives the legal name and the sentence, and the Dez shooting
  gets a date and an address.
- **J Rock.** On the TTO roster in the corpus, not yet a member row, and twice relevant:
  he was in the Tee Grizzley run with Darri, and he stopped coming around him after Tay.
- **Cino.** Also on the corpus roster, no member row. "He ran from Cino in Somerset" is
  the only thing on file.
- **The other TTO death.** u/DetroitDoge: "The last TTO member died over a doordash
  order", corrected by u/Negative_Song8881 and u/gbob9000600 to a man shot by **security
  at his workplace** while collecting food a driver was not being let through with - he
  got back in his car to leave and was shot at as he drove off. Not named, not dated, and
  not the same man as Tay. A workplace shooting by a licensed guard would leave a paper
  trail, which makes this the most findable open item here.
- **Mari and 1125.** u/Slimewave6: "I kno a few 1125 niggas personally, Mari was one of my
  hoes lil cousin". The TTO roster in the corpus also has a Mari. 1125 is not a set in the
  wiki, and `raw/murders.txt` line 51 has "Lil Quez🕊️ (BTB / 1125)". Do not assume the
  two Maris are one man.
- **TTO's era.** u/Slimewave6: "TTO 2009-2013 was lacing niggas boots thru this bitch
  outskirts and all", against u/BennyFrankFrank's "TTO not on shit" and "it's 2024 nobody
  talking bout 2011". One man's account; it stays here rather than in the set bio.
- **DWBI's fallen.** u/Most-Use-8894, 2024-05-30, lists who DWBI never got back for:
  "trey, DB, scoot, risky, jj, 4, gutta". Four are already in `raw/murders.txt` with sets
  - Trey (DWBI/TOB), DB (GMO/CMO), Risky (YBN/DWBI), Scooter/Scoot (GMO/DWBI). DWBI's
  roster in the wiki is five men; this is the shape of the rest of it.
- **"Dez is savagesquad?"** (u/No-Telephone3257, 2024-05-28) went unanswered. Dez is
  seeded to DWBI alone.
- **Permalinks for the two 2026 threads.** Both source rows carry the subreddit URL and
  the title in `notes`. Worth patching when Arctic Shift catches up, or from the browser.
