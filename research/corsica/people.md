# Corsica people

Curated extraction, ready (or close to ready) to seed `Member` / `Incident` / `Source`
records in a Corsica universe. Same role as `research/detroit/extraction/`.

**Scope note.** The four names this file started as are not four separate leads. They are
one case: the 1982 assassination of Daniel Ziglioli and the three Brise de Mer men tried
for it at Dijon in 1985. Everything below is organised around that.

Primary source is the Lazard & Galland book in this folder (see "Sources" at the bottom).
Page-level anchors are chapter files inside the EPUB, cited as `[V:PLn]`.

---

## Correction applied

- `Robert Moraquini` was a misspelling. Correct form is **Robert Moracchini**.

---

## The gang: Brise de Mer

**Seeds as a `Gang`, not a `Set`.** The schema has three tiers, `Gang` > `Alliance` > `Set`
(table `sets`, model `GangSet`), with `Set`, `Alliance` and `Member` each carrying an
independent nullable `gang_id`. `Gang` is the "top-level gang nation ... that spans
multiple sets/alliances" (`backend/app/models/gang.py`).

The Brise was never one crew. It fragmented into clans (Mariani, Guazzelli, Santucci) that
killed each other through the late 2000s. `SetRelationship` is set-to-set, so modelling the
Brise as a single `Set` leaves nowhere to record that war. As a `Gang` with each clan as a
`Set`, the internal war becomes ordinary set relationships, and the `from_date`/`until_date`
dimension carries "allied until 2007, enemies after".

```
Gang  Brise de Mer
  Set clan Mariani     Set clan Guazzelli     Set clan Santucci
Gang  Petit Bar (Ajaccio)          peer rival, Corse-du-Sud
Gang  clan Memmi                   the older rival; may stay a bare Set, it had no sub-crews
```

- Formed late 1970s around the bar **La Brise de Mer** on the old port of Bastia, run by
  Antoine Castelli. The bar gave the group its name.
- Base: Bastia and the surrounding mountain villages, Haute-Corse. Later reach into
  mainland France, Italy, North Africa and Latin America.
- Rackets: gaming and slot machines, bars and nightclubs, racketeering, armed robbery,
  later drug trafficking and laundering.
- Founding-generation names that recur: Guazzelli (Francis, Paul-Louis, Jean-Angelo),
  Mariani (Francis, then his son Jacques), Santucci (François-Marie "Francis" and
  Pierre-Marie), Seatelli, Moracchini, Richard Casanova, Christian Leoni (the "banker").

### First war: the elimination of the Memmi clan (1980-1983)

The Brise wanted the Haute-Corse nightclub and gaming economy, which **Louis Memmi**
already held. Francis Santucci went up to Corte to tell Memmi the clubs now belonged to
the young men. Memmi laughed it off. `[V:PL5]`

- **10 Sep 1981** - Louis Memmi shot dead at 04:40 under the olive tree in his garden at
  Corte, after a night of cards at the Niolu fair. Two gunmen hidden in the scrub. Never
  judicially solved. `[V:PL5, PL32]`
- **Autumn 1982** - Pierre-Jean Memmi, Louis's brother, who had sworn to avenge him,
  killed on the cours Paoli in Corte. `[V:PL5]`
- **14 Sep 1982** - Daniel Ziglioli (below).
- **28 Nov 1982** - bomb in the back room of the La Brise de Mer bar itself, ~200g charge,
  five people inside, material damage only. `[V:PL5]`
- **28 Dec 1982** - Georges Seatelli's family house at Cardo, above Bastia, destroyed by
  two gas bottles plus several kilos of dynamite, in broad afternoon. `[V:PL5]`
- **Apr 1983** - Gérard Ziglioli (below).

Book's own tally: **20+ killed on the Memmi side between 1980 and 1983**, no deaths on the
Brise side. Press-derived figure elsewhere: 15 murders and 6 attempted murders in
Haute-Corse between Sep 1981 and Nov 1983. Treat both as approximate, they count
different windows.

---

## 1. Daniel Ziglioli  (victim)

| field | value |
|---|---|
| status | `DEAD` |
| date_of_death | 1982-09-14 (precision `YMD`) |
| affiliation | none, close to the **Memmi clan** |

- Age **32**. Ran a family wholesale drinks business, and was also the owner of the
  **Le Castel** discothèque at Taglio-Isolaccio. `[V:PL5]`
- Killed **14 Sep 1982 at 18:00** leaving his warehouse. Hit **eight times** with
  large-calibre rounds. Died in the ambulance to hospital. `[V:PL5]`
- Motive: the Brise wanted Le Castel. Two of its members had been thrown out of the club
  by force. An affair, more precisely a deception and a resulting affront, is said to have
  been grafted onto that dispute. `[V:PL5]`
- Contemporary press described him as "époux modèle", "travailleur assidu",
  "père admirable" (Le Provençal-Corse, 16 Sep 1982). Note the friction with the Brise's
  own framing: he seeds as a `VICTIM` with no gang affiliation of his own.

**Related member to create: Gérard Ziglioli**, his brother. Killed **14 Apr 1983**, having
come back from the mainland to carry out the vendetta. `[V:PL5]`

---

## 2. Robert Moracchini  (defendant, acquitted)

| field | value |
|---|---|
| date_of_birth | 1959-06-06, La Porta (precision `YMD`) |
| date_of_death | 2025-03-29, Bastia (precision `YMD`) |
| status | `DEAD` |
| affiliation | Brise de Mer, co-founder |

- Manager of a bar on **place Saint-Nicolas, Bastia**; later patron of **Le Continental**.
  Described as sharp-featured, tight-lipped, as impulsive as his inseparable friend
  **François-Marie "Francis" Santucci**. The clan often worked in pairs and those two were
  a pair. `[V:PL5]`
- **Principal accused** in the Ziglioli case (see the trial section). `[V:PL17]`
- **Oct 1986** - swept up in the first serious attempt to dry up the Brise's revenue: a
  50-officer task force in Bastia, backed by prefect François Garsi, who had sworn to "get
  them the way the Americans got Al Capone". Moracchini taken into custody at 27, single,
  driving a Porsche bought in the name of his bar, of which **his mother was the official
  manager**. Searches at Le Continental, the Palais des Glaces and the Saint-Nicolas. Double
  books found at the Palais des Glaces, profit understated by roughly one million francs.
  `[V:PL8]`
- **1987** - 20 months (12 suspended) for *abus de biens sociaux* over his stake in
  Le Continental.
- **2000s onward** - stepped back from crime, ran a bistro and a tabac in Bastia.
- **May 2023** - summited **Everest**, aged 63.
- **29 Mar 2025** - shot dead with a **9mm**, several rounds, around 08:00 in the street on
  **rue du Commandant Luce-de-Casabianca**, central Bastia, near his home. Bastia
  prosecutor opened a *meurtre en bande organisée* investigation, handed to the Haute-Corse
  DIPN. Unsolved as of this writing.
- Family: son **Robert Moracchini junior**, who in the 2010s was seen with Christophe
  Guazzelli and with lieutenants of the Ajaccio **Petit Bar**. `[V:PL17]`

By the 2010s he was one of the very few surviving old guard of the Brise. `[V:PL17]`

---

## 3. Pierre-Marie Santucci  (defendant, acquitted)

| field | value |
|---|---|
| date_of_death | 2009-02-10, Arena-Vescovato (precision `YMD`) |
| status | `DEAD` |
| affiliation | Brise de Mer, founding member; led one of its clans |

- Younger brother of **François-Marie "Francis" Santucci**. The two were too different to
  work together: Francis was the calm, charismatic strategist with the bearing of an
  executive; Pierre-Marie was impulsive and violent, and quickly became the group's
  **"gâchette"** (trigger). A custody photograph shows a mocking look on a young face
  under black curls. `[V:PL5]`
- Francis died of **cancer in July 1992**. `[V:PL30, PL32]`
- At the 1985 trial he gave his profession as **waiter, at La Brise de Mer**, and told off
  the presiding judge when a question displeased him ("J'ai la tête comme une cafetière").
  `[V:PL5]`
- **5 Jul 2000** - arrested at Sartène (Corse-du-Sud) with Francis Mariani and Maurice
  Costa. `[V:PL32]`
- **31 May 2001** - the **fake fax escape**. A fax reached Borgo prison purporting to come
  from the Ajaccio tribunal, ordering the release of Santucci, Francis Mariani and Maurice
  Costa. It was actually sent from the Hôtel Campanile in Aix-en-Provence, "signed" by the
  president of the Ajaccio tribunal, and even named the correct *juge des libertés*. The
  three gathered their things and walked out in sandals through a door opened for them.
  Later parodied in the song "Il est libre fax" by I Mantini. `[V:PL9, PL32]`
- **10 Feb 2009** - killed at 52 (the book's own chronology says 51; the narrative chapter
  says 52 - **unresolved, verify**). He had grown quiet with age and barely went out except
  for his near-nightly card game at the same bar in Vescovato, **Chez Fanfan**, on the
  route nationale. Habit, a professional error in the milieu. Leaving the bar after dark,
  he was lit by a streetlamp on the near-empty car park. A **sniper** posted across the
  road, about **80 metres** away, fired **a single round through the heart**.
  `[V:PL13, PL30, PL32]`
- No one was ever charged. `[V:PL27]`
- Family: a daughter, who in the 2010s was seeing Christophe Guazzelli. `[V:PL17]`

Context: his killing sits inside the Brise's **second, internal war** of the late 2000s,
which also took Richard Casanova (2008), Francis Mariani (12 Jan 2009, killed in the
explosion of a farm shed at Casevecchie) and Francis Guazzelli (15 Nov 2009, on the road
up to La Porta). `[V:PL32]`

---

## 4. Georges Seatelli  (defendant, acquitted)

| field | value |
|---|---|
| date_of_death | 1998-08-21, Biguglia (precision `YMD`, **verify day**) |
| status | `DEAD` |
| affiliation | Brise de Mer, founding member |
| nickname | **"le Gris"** |

Nickname-first identity: **le Gris** is the display name; Georges Seatelli is the legal name.

- The most enigmatic profile in the band, and the odd one out socially: **son and grandson
  of a notary**. Blond hair falling on the forehead, short-trimmed moustache, the look of a
  brooding American actor. A brilliant student, he never finished his law degree at
  **Aix-en-Provence**, and by Dec 1982 had left the faculty for good to join the clan.
  `[V:PL5]`
- His brother did finish. **Me Jean-Louis Seatelli** is a leading criminal barrister at the
  Bastia courthouse, who has defended Corsican gangsters (Brise and others), and advised
  Bernard Tapie, Parisian businessmen and footballers. He never speaks about Georges's
  murder. `[V:PL5]`
- **28 Dec 1982** - his family house at **Cardo**, above Bastia, blown up (see the war
  timeline above). `[V:PL5]`
- Childhood friend of **Augustin-Dominique "Mimi" Viola**, mayor of Saint-Pierre-de-Venaco,
  nicknamed "l'homme du président", named in a 1999 prefecture note as the Brise's
  intermediary close to the president of the Haute-Corse conseil général (Paul Giacobbi).
  Never convicted; he signed nothing and did not speak on the phone. `[V:PL8]`
- **Aug 1998** - shot dead while having lunch on the terrace of a beach restaurant south of
  Bastia. `[V:PL5, PL30]` Press reporting places it at **Biguglia on 21 Aug 1998**, several
  rounds **in the back**, two unidentified gunmen, 9mm and 11.43mm. Linked at the time to
  the fight for control of nightlife venues, the same racket behind the Ziglioli killings.
- His son was killed at **18**, shot by a shopkeeper he was trying to rob. `[V:PL5]`

---

## The Ziglioli trial (Dijon, 28 May - 1 June 1985)

Seeds as one `Incident` (the 1982 murder) plus a set of `Source` records. Described in the
book as **the first mafia-type trial** in France, and the only Memmi-war killing that ever
produced one: the sole case where police gathered enough to identify the shooters.
`[V:PL5]`

**How the case was built**
1. A witness saw two silhouettes reach a vehicle after the shots, in the Bastia suburbs.
2. Minutes later an off-duty **PAF** (border police) officer driving home passed the car
   and saw a passenger throw a large package into the **Golo**, the island's biggest
   coastal river. He thought he recognised Robert Moracchini, then doubted himself, since
   Moracchini should have been in prison. He checked the files: Moracchini had been
   released a few days earlier. It was him.
3. The Golo was dredged at the road bridge. The package held **the murder weapon**.
4. Moracchini went straight back to prison. Seatelli and Santucci vanished, and were caught
   **2 Dec 1982** holed up in an old house in the middle of **Sorbo-Ocagnano**, ~30km south
   of Bastia, equipped with a shotgun, an Italian military rifle, large-calibre weapons,
   **wigs and gloves**.

**Charges**: Seatelli with **complicity**, Santucci with **assassinat**, both committed to
the assize court along with Moracchini.

**Why it collapsed** (venue moved to Dijon to avoid pressure)
- The PAF officer, the main witness, **retracted** again at trial. He no longer remembered
  whether he had seen Moracchini, and on reflection thought not. He had already gone back
  and forth once during the investigation.
- Other witnesses sent medical certificates recommending rest and did not travel.
- **Nine Sporting Club de Bastia players** flew to Dijon to shore up the defendants' alibi.
- **Christian Leoni**, Daniel Ziglioli's **own cousin**, gave Moracchini an alibi, saying he
  was with him at the Casone stadium in Borgo that evening. He had never mentioned this and
  had never been interviewed in the case. The Ziglioli family shouted betrayal in court.
  Leoni went on to become the Brise's **banker**, distributing profits among members and
  investing them in the legal economy.
- Men in black sat in the front row throughout, staring at the jurors.
- The presiding judge was notably mild. Only the *avocat général* denounced the vanishing
  witnesses and the providential alibis, sighing about a strange "alchimie de la mémoire",
  then requested the sentences anyway.

**Sentences requested**: 15 years for Moracchini and Santucci, 8 to 10 for Seatelli.
**Verdict, 1 June 1985: general acquittal.** The jury had 40 questions to answer and
deliberated **30 minutes**.

Civil-party counsel **Me Christine Courrégé**: "Le procès Ziglioli est l'un des dossiers
qui m'ont le plus marquée dans ma carrière. J'étais ivre de rage, d'impuissance, devant
cette parodie de justice." She never took another Corsican case. `[V:PL5]`

Coda: in **1991** a lawyer who had pleaded alongside her for the Ziglioli family, **Jean
Grimaldi**, was shot dead at the wheel of his 4x4 outside his home near Bastia (6 Nov
1991). A priori unconnected to this case. `[V:PL5]`

After Dijon the Brise was stronger than ever. The Memmi clan no longer existed. `[V:PL5]`

---

## Modelling notes for the wiki

- All four are `Member` records. Three of the four are also incident victims, so they carry
  `death_incident_id` once the corresponding `Incident` exists.
- **Affiliation fields**: Moracchini, Santucci and Seatelli each get
  `gang_id` = Brise de Mer plus a `set_id` for their clan via `MemberSet` (which has the
  same time dimension, so a clan switch is recordable). Daniel Ziglioli gets no `gang_id`;
  he was a club owner aligned with the Memmi side, not a member of it. `Member.gang_id` is
  independent of `set_id`, so a man whose clan is unknown can still be tagged to the Brise.
- The Corsica universe carried five Chicago gang nations (Black Disciples, Black P. Stones,
  Gangster Disciples, Latin Kings, Mickey Cobras), backfilled into every then-existing
  universe by migration `33ac22d53ce8` on 2026-05-08, not by anything Corsica-specific.
  Deleted 2026-08-20, nothing referenced them. The Corsica `gang` table should hold only
  Brise de Mer, Petit Bar and the Memmi clan.
- **The 1982 Ziglioli murder is one `Incident`** linking all four:
  - Daniel Ziglioli - role `VICTIM`, outcome `KILLED`
  - Pierre-Marie Santucci - role `SHOOTER`, outcome `UNHARMED`
  - Robert Moracchini - role `SHOOTER`, outcome `UNHARMED`
  - Georges Seatelli - role `ASSISTED`, outcome `UNHARMED` (charged as *complicité*)
  - **All three were acquitted.** The schema has no "alleged / acquitted" qualifier on
    participants, so this must be carried in the incident description, or the roles
    downgraded. Decide before seeding: recording an acquitted man as `SHOOTER` is a factual
    claim the court rejected.
- Incident type: existing enum has `SHOOTING` and `MURDER`. The Seatelli house bombing
  (28 Dec 1982) and the Brise bar bombing (28 Nov 1982) need `BOMBING`, which now exists.
- Dates are all at least year-precision; most are full `YMD`. Where only the month is known
  (Seatelli's death per the book, Pierre-Jean Memmi in "autumn 1982"), use precision `YM`
  or `Y` with `approx: true` rather than guessing a day.
- Municipalities to create: Bastia, Corte, Cardo, Taglio-Isolaccio, Cervione, Vescovato
  (Arena), Sorbo-Ocagnano, Biguglia, Borgo, La Porta, Saint-Pierre-de-Venaco.

## Open questions

- Santucci's age at death: 51 or 52? The book contradicts itself.
- Georges Seatelli's exact date of death. Book says only "August 1998"; press reporting
  says 21 Aug 1998 at Biguglia. Confirm against Corse-Matin.
- Daniel Ziglioli's date of birth (age 32 in Sep 1982 implies 1949 or 1950).
- Gérard Ziglioli: exact circumstances and place, and whether he had a separate trial.
- Whether Seatelli was a *founding* member or a slightly later joiner. The book's glossary
  calls both him and Pierre-Marie Santucci "membre fondateur", but the narrative has him
  merely hanging around the bar at first, still a law student at Aix.

---

## Sources

**Primary (in this folder)**
- Violette Lazard & Marion Galland, *Vendetta*, Plon, 2020, ISBN 9782259277525. EPUB in
  this directory. Cited above as `[V:PLn]` where `PLn` is the chapter file inside the EPUB.
  Relevant chapters: PL5 (the Memmi war and the Dijon trial), PL8 (the 1986 financial
  crackdown, Mimi Viola), PL9 (the fax escape), PL13 (Santucci's death), PL17 (the sons'
  generation), PL27 (unsolved killings of the barons), PL30 (glossary of figures),
  PL32 (chronology).
- Reliability: `HIGH`. Two investigative journalists, sourced to court files, police
  records, named interviews and dated press citations.

**Press cited inside the book** (worth pulling directly for `Source` records)
- Corse-Matin, 11 Sep 1981 (Memmi killing)
- Le Provençal-Corse, 16 Sep 1982 (Ziglioli killing)
- Corse-Matin, 31 May 1985 and 29 Jun 1985 (the Dijon trial)
- Louis-Marie Horeau, Le Canard enchaîné, Jun 1985 (the trial)

**Online, consulted 2026-08-20**
- Liste de personnes assassinées en Corse, fr.wikipedia.org - reliability `MEDIUM`
- Robert Moracchini, fr.wikipedia.org - reliability `MEDIUM`
- Gang de la Brise de Mer, en.wikipedia.org - reliability `MEDIUM`
- France 24, 10 Feb 2009, "Pierre-Marie Santucci, figure du banditisme corse, abattu" -
  reliability `HIGH` (403s non-browser clients, open in a browser)
- Le JDD, "Brise de mer: Santucci abattu" - reliability `MEDIUM`
- Police & Réalités, 29 Mar 2025, on the Moracchini killing - reliability `LOW`, blog
- 20 minutes (CH), Mar 2025, on the Moracchini killing - reliability `MEDIUM`

**Not yet consulted**
- The Canal+ documentary series *Omerta, le gang de la Brise de Mer* (Patrick Spica
  Productions, 4x52).
