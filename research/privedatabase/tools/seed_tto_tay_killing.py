"""Seed the killing of TTO Tay and what four threads agree on about it.

    1flang2  2024-09-20  "Did TTO Darri backdoor TTO Tay & if he did why?"    +41, 68c
    1ftr0o2  2024-10-01  "No Way Darri Did That"                              +7, 24c
    -        2026-08-25  "Darri must not be TTO no more"                      +3, 3c
    -        2026-08-25  "Damn ts wild"                                       +43, 50c

The 2024 pair came back off Arctic Shift (`reddit_fetch.py thread <id>`); the local
mirror holds their titles but no comment bodies, its comment sync stopping at
2024-08-09. The 2026 pair were read on the day they were posted and have no permalink
here yet - both are `YoungAmazing313`, hours apart, and the second is what made this
worth writing: the sub now treats the killing as settled where in 2024 it was a rumour.

What every account agrees on, across two years and a dozen commenters:

  who      Darri killed Tay. In September 2024 that was "the rumor" (u/Academic_Pattern_941,
           "Rumor says Darri & Baby Jay did that shit") and the thread's evidence was that
           neither man had posted in two weeks and that Darri did not attend the funeral
           (u/SpreadPrior9553, +17). By August 2026 it is common ground: "This aint shit
           new mfs been knew this" (+30), "I swear everybody knew this", "facts been spoke
           on it". Nobody in the 2026 thread disputes it.
  what     Tay flew to Houston to see him and was killed there. u/imbrandetta: "So you
           travel hours to another state with the intentions of linking with yo mans ...
           then he turn round and smoke you?"
  why      Money. In 2024 the story was that Tay ran off with a load ("He ran off wit darri
           shipment"). u/AggravatingIce999 gave the correction on 2024-10-02 - "They saying
           tay ain't run off darri just jumped the gun early" - and 2026 completes it: the
           money had been seized by the TSA and Darri took the receipt for a forgery
           (u/HatingAssNgga55, +17: "Allegedly Darri thought Tay ran off with some pape
           whole time TSA took it" / "Darri thought tay made fake papers").
  kin      Tay is **Quwan's brother**, said independently in all three commented threads
           (u/AdvantageAny5819 and u/Kingz810 in 2024-09, u/AggravatingIce999 in 2024-10,
           u/HatingAssNgga55 in 2026: "that's his dead bestfriend brother"). Quwan is on
           file in the corpus as a TTO body - `privedatabase/detroit.md` line 482 has
           30 Boys' Lil B carrying "Corps: Quwan ( TTO )" - and Darri rode for him:
           "Darri was tearing shit up about Quwan", "the nigga who was innat car the most
           fa quwan". Quwan is created here so the brother link has something to point at.

Tay is **886 Tay**, which is TTO: 886 is already TTO's `name_variants` number. That is the
independent check that the man seeded off the roster is the man these threads are about.

Date: no source gives one. The 2024-09-20 thread has the funeral already held and both
suspects off Instagram "in 2 weeks", so September 2024 at month precision, approx. No
press account of it exists - searched, and Detroit's press names almost nobody.

Location is Houston, Texas, which is outside the universe, so `municipality_id` stays
null and the text column carries the city.

Not written: **Baby Jay** (and "southwest jay"), named in 2024 as the second man and never
again. He has no set, no other mention, and one rumour is not a member row.

Idempotent: the incident is matched by its victim, members by nickname within the set.
"""

import sys

from wikiapi import Api, q

DETROIT = "4f57cae1-ebfe-408c-b435-052e2bd0ca45"
TTO = "65567fc2-f41b-419d-b569-3eccabdf2161"
SUB = "https://www.reddit.com/r/CrimeInTheD/"
ACCESSED = "2026-08-25"

SOURCES = [
    {
        "url": "https://www.reddit.com/r/CrimeInTheD/comments/1flang2/",
        "title": "r/CrimeInTheD thread asking whether TTO Darri backdoored TTO Tay",
        "publication": "Reddit",
        "published_at": {"year": 2024, "month": 9, "day": 20, "precision": "YMD"},
        "accessed_at": ACCESSED,
        "reliability": "LOW",
        "notes": (
            "u/Famous-Eye-5602, 68 comments, read through Arctic Shift. The thread that "
            "first named Darri, two weeks or so after the killing. Carries the funeral "
            "absence, the two-weeks-off-Instagram detail, the shipment motive, Baby Jay "
            "as a second name, and three commenters confirming Tay was Quwan's brother."
        ),
    },
    {
        "url": "https://www.reddit.com/r/CrimeInTheD/comments/1ftr0o2/",
        "title": "r/CrimeInTheD thread on Darri, eleven days later",
        "publication": "Reddit",
        "published_at": {"year": 2024, "month": 10, "day": 1, "precision": "YMD"},
        "accessed_at": ACCESSED,
        "reliability": "LOW",
        "notes": (
            "u/Thatshitova, 24 comments, read through Arctic Shift. Where the motive is "
            "first corrected: u/AggravatingIce999, 'They saying tay ain't run off darri "
            "just jumped the gun early'. Also 'That was quwan brother'."
        ),
    },
    {
        "url": SUB,
        "title": "r/CrimeInTheD thread on the killing of TTO Tay, two years on",
        "publication": "Reddit",
        "published_at": {"year": 2026, "month": 8, "day": 25, "precision": "YMD"},
        "accessed_at": ACCESSED,
        "reliability": "LOW",
        "notes": (
            "u/YoungAmazing313, 'Damn ts wild', +43 and 50 comments within the hour. "
            "Permalink not captured. The thread where the sub stops hedging: Darri killed "
            "Tay in Houston over money the TSA had seized, Tay having flown down to clear "
            "it up. Also that J Rock stopped coming around him, that he is still free, and "
            "that TTO were Tee Grizzley's people when he broke."
        ),
    },
    {
        "url": SUB,
        "title": "r/CrimeInTheD thread asking whether Darri is still TTO",
        "publication": "Reddit",
        "published_at": {"year": 2026, "month": 8, "day": 25, "precision": "YMD"},
        "accessed_at": ACCESSED,
        "reliability": "LOW",
        "notes": (
            "u/YoungAmazing313, 'Darri must not be TTO no more', posted hours before the "
            "other. Permalink not captured. u/Tiny_Examination1251: 'Darri ain't been "
            "around them boys a min now even before the tay situation'. Not enough to "
            "close his TTO spell, but it is the first suggestion the affiliation lapsed."
        ),
    },
]

NARRATIVE = (
    "Tay flew to Houston to see Darri, who believed he had run off with his money. "
    "The money had been seized by the TSA."
)


def main():
    """Create the four sources, Quwan, the brother link and the killing."""
    go = "--go" in sys.argv
    api = Api()

    def write(method, path, payload=None):
        if not go:
            print(f"[dry] {method} {path}")
            return {"id": None}
        out = api.call(method, path, payload)
        if isinstance(out, dict) and "_error" in out:
            sys.exit(f"{method} {path} -> {out['_error']} {out['_body']}")
        return out

    src = []
    for spec in SOURCES:
        hit = q(f"SELECT id::text FROM source WHERE title = $${spec['title']}$$")
        src.append(
            hit[0]["id"]
            if hit
            else write("POST", "sources/", {"universe_id": DETROIT, **spec})["id"]
        )
        print(f"source {'on file' if hit else 'created'}: {spec['title']}")
    src = [s for s in src if s]

    def member(nickname, set_id):
        hit = q(
            "SELECT m.id::text FROM member m JOIN member_set ms ON ms.member_id = m.id "
            f"WHERE m.universe_id = '{DETROIT}' AND ms.set_id = '{set_id}' "
            f"AND m.nickname = '{nickname}'"
        )
        return hit[0]["id"] if hit else None

    tay, darri = member("Tay", TTO), member("Darri", TTO)
    if not (tay and darri):
        sys.exit("Tay and Darri must both be on TTO before this runs")

    quwan = member("Quwan", TTO)
    if quwan:
        print("member on file: Quwan")
    else:
        quwan = write(
            "POST",
            "members/",
            {
                "universe_id": DETROIT,
                "nickname": "Quwan",
                "status": "DEAD",
                "affiliations": [{"set_id": TTO, "is_primary": True}],
                "source_ids": src[:2],
            },
        )["id"]
        print("member created: Quwan (DEAD)")

    def sources_of(mid):
        return {
            r["source_id"]
            for r in q(f"SELECT source_id::text FROM member_source WHERE member_id = '{mid}'")
        }

    if go:
        write(
            "PATCH",
            f"members/{tay}?universe_id={DETROIT}",
            {"family": {"brother": [quwan]}, "source_ids": sorted(sources_of(tay) | set(src))},
        )
        print("member updated: Tay, brother of Quwan")
        write(
            "PATCH",
            f"members/{quwan}?universe_id={DETROIT}",
            {"family": {"brother": [tay]}},
        )
        print("member updated: Quwan, brother of Tay")
        # "Gang Only (feat. King Von)", released 2019-02-28 under the name Darri.
        write(
            "PATCH",
            f"members/{darri}?universe_id={DETROIT}",
            {"is_rapper": True, "source_ids": sorted(sources_of(darri) | set(src))},
        )
        print("member updated: Darri, rapper")

    hit = q(
        "SELECT i.id::text FROM incident i JOIN incident_participant p ON p.incident_id = i.id "
        f"WHERE i.universe_id = '{DETROIT}' AND i.type = 'MURDER' AND p.member_id = '{tay}'"
    )
    if hit:
        print("incident on file: the killing of Tay")
    else:
        write(
            "POST",
            "incidents/",
            {
                "universe_id": DETROIT,
                "type": "MURDER",
                "date": {"year": 2024, "month": 9, "day": None, "precision": "YM", "approx": True},
                "location_text": "Houston, Texas",
                "narrative": NARRATIVE,
                "participants": [
                    {"member_id": tay, "role": "VICTIM", "outcome": "KILLED"},
                    {"member_id": darri, "role": "SHOOTER", "outcome": "UNHARMED"},
                ],
                "source_ids": src,
            },
        )
        print("incident created: the killing of Tay, Houston, September 2024")

    if not go:
        print("\ndry run. re-run with --go to write.")


if __name__ == "__main__":
    main()
