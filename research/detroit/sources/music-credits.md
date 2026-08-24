# Old song credits worth investigating

Music-video credit lines that name people **with their set, at a known date**.

That combination is rare and it is why this file exists. Almost everything else
in Detroit research is present-tense: a forum thread in 2025 tells you what
someone claims *now*, or what a stranger remembers. A credit line from 2012 is
contemporaneous. It records who stood next to whom, under which name, in that
year, and it does not drift the way memory does.

Two things they are good for:

1. **Dating affiliations.** A set on a 2012 credit is evidence for 2012, not for
   today. Where somebody's affiliation has since changed, the credit dates the
   earlier spell, which `member_set.from_date` / `until_date` can hold.
2. **Dating relationships.** A diss track is a hostile act with a release date.
   If two sets appear on one track they were at least cooperating; if one track
   attacks another set, that beef existed by then.

None of this is proof of membership on its own. Rappers guest on each other's
records, and a credit can be a courtesy. Treat a credit as evidence that the
association existed, not that the person was a member.

---

## 2012 - "Broke Ass Niggas"

```
(MVHN) Reo · (TMCNE/MVHN) Ching · (TMCNE) Scoop · Maino
```

**Why this one matters most.** Ching is credited as **TMCNE/MVHN** - one foot in
each - in 2012. Those two are enemies now: MVHN sits in The Family and TMC/CNE
in TMCNE, and the sets carry an ENEMY spell opened around 2015. His dual
credit is independent evidence that they were friendly beforehand, which is what
the closed FRIEND spell on MVHN↔TMC records. Without this line that friendship
rests on one person's say-so.

Unresolved:

- **Reo** (MVHN) - not in the wiki
- **Scoop** (TMCNE) - not in the wiki. Reported on Reddit as "got life" and
  "locked for murder", which would make him findable on OTIS *if* a legal name
  turns up. Worth a search.
- **Maino** - no set given. Note the name collides with the New York rapper, so
  do not assume search results are the same person.
- **Ching** - in the wiki, currently MVHN\*/TMC

## 2013 - "Not Boyz" (StuntHard HotBoyz diss)

```
TMC Doe · TMC Fat Rob · TMC Zell 🕊 · CNE Zeek · MVHN Ralph
```

**Why this one matters.** It is a diss aimed at **StuntHard**, which independently
corroborates the TMC↔Stunthard beef dated to about 2013 from a completely
separate thread (the one where TMC's founding is described, and where Toonk is
said to have been shot "behind it"). Two unrelated sources putting the same beef
in the same year is about as good as it gets here.

It also has TMC, CNE and MVHN on one track in 2013 - again before the split.

Unresolved:

- **Doe** (TMC) - not in the wiki
- **Ralph** (MVHN) - not in the wiki
- **Zell** (TMC, 🕊 dead) - the wiki has a `Zell` in set **700**, status UNKNOWN.
  Different set and different status, so treat as a possible collision, not a
  match, until something else ties them together.
- **Zeek** (CNE) - the wiki has `Zeke` (Ezekiel), **TMC**, DEAD. Different
  spelling *and* different set. Same caution.
- **Fat Rob** (TMC) - in the wiki, TMC, and named as a TMC founder in the 2010
  Wendy's meeting account

---

## How to work these

1. **Find the record.** Neither track has been located yet. Old Detroit videos
   live on YouTube and WorldStar, and channels get deleted, so an archive.org
   snapshot is worth checking before assuming it is gone.
2. **Read the description and the comments.** Credits, dates and @-handles in a
   video description are usually more precise than the title.
3. **Legal names are the prize.** A rapper's stage name plus a set gets you
   nowhere on OTIS, which searches on legal names and offender numbers. But a
   video description, a distributor credit or a copyright registration sometimes
   carries the real name, and that is the bridge to a court and MDOC record.
4. **Do not write a credit into a biography.** The set belongs in `member_set`,
   the date in `from_date`, and the track itself in a `source` row. If a fact has
   a column it does not go in prose.

## Other tracks mentioned but not yet run down

- **Ratchett** has a song with **Baby Threat** (per r/CrimeInTheD). Baby Threat is
  in the wiki in set 637 and is described as the one Inkster 30/CashGang member
  who also claims TR30, so a track linking him to a Detroit artist would help
  date that overlap.
- **Key videos** are said to feature 30 Boyz members. Key is in the wiki
  (CashGang), so those would be another cross-set snapshot.
