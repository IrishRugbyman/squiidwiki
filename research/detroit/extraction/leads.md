# Open leads

Fragments that name something real but don't yet resolve to a wiki row. One entry per
lead, newest first. A lead leaves this file when it either becomes an entity (say where)
or is ruled out (say why). Nothing here is wiki data.

Record the exact wording seen. Half of what these fragments are worth is in the phrasing,
and a paraphrase written from memory a week later loses it.

---

## J-Nutty (BCB) killed FOE Life Chris - 2026-08-25

**Roughly 15 years**, for killing **Chris** of **FOE Life**.

Neither the man nor the killing is in the database yet, and both are seedable once the
date is pinned:

- **J-Nutty** is already a member: BCB, `LOCKED`, no legal name, no sentence recorded.
- **FOE Life** is the set the wiki holds as **PBF** (`pbf`, ACTIVE). privedatabase carries
  it as the single set "PBF/FOE Life" at `/pbf-foe-life/`, and three other Detroit set
  pages list "PBF/FOE Life" as one ally, so the two names are one set, not two. **Chris is
  not on the PBF roster** - its seven members are Blair Nelson, Murda Mook, Black Steve,
  Tank, Skurf, Rio and Trigga Trey. So he is a new member row.
- **The killing** is a new `MURDER` incident: J-Nutty `SHOOTER`, Chris `VICTIM`/`KILLED`.
  Seeding it sets Chris's `status=DEAD` and `death_incident_id` through the normal
  incident-driven death sync, so the date is the one thing worth getting right first.

**Corroboration already in the repo**, both captured 2021-03-30:

- `sources/social-links.txt` line 36 - `free.jnutty`, tagged BCB, filed under the
  `PRISON` bookmark folder: `https://www.facebook.com/free.jnutty`. A "Free ___" page
  under that folder puts him inside by **March 2021 at the latest**, which is the outside
  bound on the sentence start until something narrows it.
- `sources/mdoc-records.txt` line 67 - MDOC **378938**, tagged `FOE`. Unresolved: the tag
  could be the set or a nickname, and it is not obviously Chris or J-Nutty. Worth a lookup,
  though OTIS 403s this server's Helsinki IP.

**What to pin down.** The date of the killing, Chris's real nickname if "Chris" is short
for something the street used, and whether the ~15 is a sentence range (a 15-to-N MDOC
spell) rather than a flat number - MDOC sentences are min-max, so "took like 15" most
likely names the minimum.

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
