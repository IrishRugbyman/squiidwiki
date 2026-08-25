# Open leads

Fragments that name something real but don't yet resolve to a wiki row. One entry per
lead, newest first. A lead leaves this file when it either becomes an entity (say where)
or is ruled out (say why). Nothing here is wiki data.

Record the exact wording seen. Half of what these fragments are worth is in the phrasing,
and a paraphrase written from memory a week later loses it.

---

## J-Nutty (BCB) killed FOE Life Chris - 2026-08-25

**J-Nutty got LIFE, at about 15 years old**, for killing **Chris** of **FOE Life**. He
shot Chris, then walked up to him and finished him on the ground. Early 2010s.

Corrects an earlier reading in this file: "took like at 15" is his **age**, not a
fifteen-year sentence.

### FOE Life is its own set, and is not PBF

An earlier version of this entry said FOE Life was the set the wiki holds as PBF. **That
was wrong.** The Band Crew RICO indictment (E.D. Mich., federal, HIGH) names them as two
separate component sets in one sentence:

> Band Crew was an association of existing smaller gangs that principally included members
> of Constantly Making Hundreds (CMH, formerly Cash Money Hoes), Young N Crispy (YNC),
> Pushit (or Pusha) Boy Family (PBF), and Family Over Everything Love is Forever (FOE Life).

So **FOE Life = "Family Over Everything Love is Forever"**, and it does **not** exist in
the database - a `%foe%` search over Detroit sets returns nothing. privedatabase merges
the two onto a single `/pbf-foe-life/` page, which is where the error came from. The
indictment outranks it. Read the merged page as two sets from here on.

Band Crew context from the same document, useful for dating: it **formed in November 2011**
at a Burger King meeting and ran until the arrests of autumn 2015. Its territory is
northwest Detroit, centred on Seven Mile - **8 Mile north, W McNichols south, Greenfield
east, Southfield Freeway west**.

### What this needs before it can be seeded

- **FOE Life** as a new Set.
- **Chris** as a new Member under it.
- The killing as a new `MURDER` incident: J-Nutty `SHOOTER`, Chris `VICTIM`/`KILLED`.
  That sets Chris's `status` and `death_incident_id` through the incident-driven death
  sync, so **the date is the piece to pin first**.
- J-Nutty's sentence. He is already a member (BCB, `LOCKED`, no legal name recorded).

### Search record, so nobody repeats it

**The article was not found.** Searched 2026-08-25: Detroit press by victim name and by
the MO, Michigan Court of Appeals opinions, the juvenile-lifer coverage, and
detroitstreetgangs.com. Nothing surfaced. This is the normal outcome for Detroit street
homicides of that period rather than a sign the account is wrong.

**Do not mistake the 2022 gas-station case for this one.** Mekhi Green, 15, shot Rob
Harris, 15, at a gas station on the 11000 block of E 7 Mile on 7 January 2022, then stood
over him and fired five more times at close range. The MO matches almost word for word and
the shooter's age matches, but the decade does not, the victim is not a Chris, and it is
east side rather than the Band Crew box. Different case.

**Candidate victims** from `homicides/` (chamspage, UNVERIFIED, incomplete, and it stops
at 2013). None sits cleanly inside the Band Crew box, so treat the list as a prompt rather
than a shortlist:

| Date | Name | Age | Block |
|---|---|---|---|
| 2009-09-27 | Christopher Williams | 21 | 14838 Snowden |
| 2009-12-22 | Chris Craig | 19 | 9333 Jefferson Ave |
| 2010-06-26 | Christopher Harris | 25 | Edmore & Mohican |
| 2011-04-07 | Christopher Rice | 38 | 19245 8 Mile Rd |
| 2012-04-17 | Christopher Wilcher | 22 | 19317 Lumpkin |
| 2012-06-22 | Christopher Woodard | 24 | Fordham and Chalmers |
| 2012-09-02 | Christopher Jones | 25 | 15100 Petoskey |

**Better routes than press search**, in order:

1. **A juvenile lifer is a documented person.** Michigan's roughly 400 juvenile lifers all
   came up for resentencing after *Miller* (2012) and *Montgomery* (2016), and Wayne County
   holds the largest share. That produces a named court record - the resentencing docket -
   for someone sentenced to life at 15 in the early 2010s. It needs his legal name, or a
   list to scan.
2. **OTIS**, once his legal name is known. Blocked from this server's Helsinki IP, so it
   wants a browser elsewhere.
3. **Ask for the date, or the neighbourhood.** Either one collapses the candidate list
   immediately.

### Corroboration already in the repo, both captured 2021-03-30

- `sources/social-links.txt` line 36 - `free.jnutty`, tagged BCB, filed under the `PRISON`
  bookmark folder: `https://www.facebook.com/free.jnutty`. Consistent with a life sentence
  being served in 2021.
- `sources/mdoc-records.txt` line 67 - MDOC **378938**, tagged `FOE`. Unresolved whether
  that tag is the set or a nickname, and it is not obviously Chris or J-Nutty. Given FOE
  Life is now a confirmed distinct set, this row is worth a lookup.

---

## BCB Nutty, "free bloody" - 2026-08-25

**Source.** Instagram story by **Nutty** (BCB), relayed via
https://www.instagram.com/p/DcbXtMLnOAL/. Wording as given:

    damn free bloody we was pressin shit

**The post did not render from this server.** Both the post page and
`/embed/captioned/` returned Instagram's generic JS shell - 616 KB of bundle, zero
`cdninstagram.com` image URLs, the shortcode appearing only as the echoed URL. So the
frame behind this quote has not been read, and the story itself is gone by now. Retrieving
it needs a browser on a residential connection. Note this contradicts the
`~/squiidape/ig/CLAUDE.md` claim that post pages render to a logged-out fetch - that route
worked for the 752/PJC sweep on 2026-08-24 and did not work here, so treat it as
sometimes-works rather than reliable.

**"Bloody" is not a name.** It is a term of address, roughly "bro", and affectionate.
Do not create a member from it, and do not read it as an alias on anyone. The subject of
the sentence is unnamed.

**Nutty and J-Nutty are two different people.** Both are BCB, and the shared stem means
nothing - it is not evidence they are the same man, and it is not evidence the one is
talking about the other. J-Nutty's incarceration is separately accounted for (above), so
he is **not** the subject of this line by default. Whoever Nutty is calling for here is
still unidentified.

**What the fragment carries:**

- `free ___` - someone close to Nutty is **incarcerated**, as of the story's date.
- `we was pressin shit` - past tense, first person plural. Nutty and this person ran
  together, and "pressing" is the activity. That is a shared-history claim about a
  named member and an unnamed one, and it is exactly the kind of fact no column holds -
  biography material, once there is someone to attach it to.

---

## Standing note: BCB's gang tag

BCB's ten members all carry the gang `Unknown Vice Lords`, while a BCB member addresses
his people as "bloody". Worth checking whether that tag is real or is fallout from
migration `33ac22d53ce8`, which backfilled five Chicago nations into every universe that
existed at the time. Detroit still carries those.
