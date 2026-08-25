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

## Not yet established - do not seed these as fact

- **That William Morton is J-Nutty.** The opinion contains no nicknames for the defendants,
  and "Nutty" appears nowhere in it. Everything else lines up - BCB member, roughly 15,
  life, victim is a FOE Life Chris - but the identification is currently an inference from
  the street account, and it is exactly the kind of link that wants a second source before
  it goes in a member row.
- **Age and sentence.** The opinion is a conviction affirmance and states neither. Press
  reporting has Morton at 15 and sentenced to life without parole, and Bell at 27-40 years,
  but that has not been read off a primary document yet. The sentencing record or an OTIS
  lookup settles both.
- **Whether anyone finished Walker on the ground.** The street account is that the shooter
  shot him and then walked up and killed him on the ground. The appellate recital does not
  describe that - it describes shooting into a crowd from outside a black Mazda. Note the
  one thing that could have produced the confusion: the prosecutor's closing has Morton
  "walked up to Christopher Walker **in school** and says To-To says what's up", but that
  is the earlier confrontation that led to the fistfight, not the shooting. Unresolved,
  and the trial transcript rather than the opinion would settle it.
- **The street account dates it to the early 2010s.** It is 2008. The appeal was decided in
  2012, which is a plausible source of the drift.

## Seeding plan

Nothing here is in the database yet. Order matters:

1. **FOE Life** as a new Set (alias "Family Over Everything"), rival to BCB.
2. **Christopher Walker** as a Member of FOE Life - `legal_name` "Christopher Walker",
   nickname unknown, so `nickname_unknown=True`.
3. **To-To** as a Member on the BCB side, `status=DEAD`, no date yet.
4. The **incident**: `MURDER`, 2008-10-16 `YMD`, at Evergreen & Pembroke.
   Participants: Morton `SHOOTER`/`UNHARMED`; Walker `VICTIM`/`KILLED`; McCants, Slater
   and Merriweather `VICTIM`/`INJURED`; Bell `ASSISTED`/`UNHARMED`.
5. **Derryck Brantley** with `acquitted=True` on his participant row. This is the textbook
   case for that flag: a court affirmatively cleared him. His `notes` should say acquitted
   of all charges at the joint trial.
6. Set the **bilateral BCB / FOE Life enemy** relationship.
7. Attach this opinion as a `Source`, HIGH, with the courts.michigan.gov URL.
