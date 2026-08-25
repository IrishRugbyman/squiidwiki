"""Seed what two r/CrimeInTheD threads of 21 May 2024 establish about TTO and DWBI.

    1cxex86  "(TTO) Dirty got locked for shooting (Dwbi) Dez 12 times last year
              and Trey Trey killer is affiliate with tto, why is 8 still fw tto?"
    1cxd82a  "Damn dawg so ya tellin me the big homie fakin like that.. then why
              tto darri act like big homie was a big dawg"

Both were read out of the local Reddit mirror (`reddit_mirror.py thread <id>`), not
off the site, so the comment bodies here are the archived ones and include the two
that reddit now renders as [deleted].

Four men come out of it with a set and a state, each corroborated by a commenter who
is not the poster:

  Dirty (TTO)      locked for shooting Dez. u/Confident_Society927 says the same
                   thing in the other thread the same day ("(TTO) dirty is locked
                   for shooting (dwbi) Dez 11 times rn"), and u/Environmental-Rub669
                   posted "He snitched on TTO Dirty" five months earlier, which puts
                   the case on file before either thread.
  Dez (DWBI)       shot and survived. u/Tweaker-Taliban44, 2024-06-09: "Dez did get
                   popped 12x by them TTO niggas". u/Choice_Marketing9481 has him
                   posting on Instagram in May 2024, so he is alive.
  Trey Trey (DWBI) dead. `raw/murders.txt` carries him independently as
                   "Trey (DWBI/TOB)", and TOB is his brother's set - u/Treeymafiapantts
                   calls Tob Juan "trey trey lil brother".
  8 (DWBI)         u/Prestigious-Slip-787, 2024-07-19: "He exposed 8 and the rest of
                   Dwbi for being fakers". Both threads have him still running with
                   TTO after the two attacks, which is the whole point of the posts.

The shooting of Dez is seeded as an incident. "Last year" in a post dated 2024-05-21
is 2023, at year precision. The count is 12 in two accounts and 11 in one; 12 is used.
There is no address anywhere in either thread, so the incident carries the Detroit
municipality and no location text - a gap to fill, not a fact.

Three things are deliberately NOT written:

  Trey Trey's killer. The OP says a TTO affiliate, u/Affectionate_Mud8033 says TTO
  did it, and u/Treeymafiapantts denied in August 2023 that anyone had ever said so
  and elsewhere credits "Dre". A disputed attribution is not an incident row, so he
  is seeded DEAD with no death incident.
  TTO x DWBI as an edge. u/ChampionshipNo2530 read the two sets as friendly
  ("I thought dwbi fuck with tto tho shit I guess it be mini beefs in cliques").
  Ally and enemy are both arguable from the same thread, so neither is written.
  Darri's rank. u/Carl_da_JungOG calls him "the youngest in charge"; two other
  commenters in the same thread say he is nothing. Reputation, not rank.

Idempotent: sources are matched by URL, members by nickname within the set, and the
incident by its participant pair.
"""

import sys

from wikiapi import Api, q

DETROIT = "4f57cae1-ebfe-408c-b435-052e2bd0ca45"
DETROIT_CITY = "55d40a23-fdbe-4e83-b5b0-5670a04df4c9"
TTO = "65567fc2-f41b-419d-b569-3eccabdf2161"
DWBI = "fcbdb7c7-af32-437c-93f0-0f4ae5cd880a"
ACCESSED = "2026-08-25"

POSTED = {"year": 2024, "month": 5, "day": 21, "precision": "YMD", "approx": False}
LAST_YEAR = {"year": 2023, "month": None, "day": None, "precision": "Y", "approx": False}

THREAD_A = {
    "url": "https://www.reddit.com/r/CrimeInTheD/comments/1cxex86/",
    "title": "r/CrimeInTheD thread on TTO Dirty shooting DWBI Dez",
    "publication": "Reddit",
    "published_at": POSTED,
    "accessed_at": ACCESSED,
    "reliability": "LOW",
    "notes": (
        "u/Embarrassed_Pace2128, 21 May 2024, video post. Titles TTO Dirty as locked "
        "for shooting DWBI Dez twelve times the year before, says the man who killed "
        "Trey Trey is a TTO affiliate, and asks why 8 still runs with TTO. Comments "
        "date TTO's peak to 2009-2013 and place a Mari with 1125."
    ),
}

THREAD_B = {
    "url": "https://www.reddit.com/r/CrimeInTheD/comments/1cxd82a/",
    "title": "r/CrimeInTheD thread on TTO Darri and the killing of DWBI Trey Trey",
    "publication": "Reddit",
    "published_at": POSTED,
    "accessed_at": ACCESSED,
    "reliability": "LOW",
    "notes": (
        "u/ChampionshipNo2530, 21 May 2024. Same day and same subject as the other "
        "thread. Carries the second account of the Dez shooting (eleven shots there), "
        "the claim that TTO killed DWBI Trey Trey, and an argument over TTO Darri's "
        "standing in which one commenter calls him the youngest in charge and two say "
        "he is not original TTO and cannot fight."
    ),
}

MEMBERS = [
    {"nickname": "Dirty", "set": TTO, "status": "LOCKED", "sources": ("A", "B")},
    {"nickname": "Dez", "set": DWBI, "status": "FREE", "sources": ("A", "B")},
    {
        "nickname": "Trey Trey",
        "set": DWBI,
        "status": "DEAD",
        "aliases": ["Trey"],
        "sources": ("A", "B"),
    },
    {"nickname": "8", "set": DWBI, "status": "UNKNOWN", "sources": ("A", "B")},
]


def main():
    """Create the two source rows, the four members and the shooting."""
    go = "--go" in sys.argv
    api = Api()

    def write(method, path, payload=None):
        if not go:
            print(f"[dry] {method} {path} {payload if payload else ''}"[:160])
            return {"id": None}
        out = api.call(method, path, payload)
        if isinstance(out, dict) and "_error" in out:
            sys.exit(f"{method} {path} -> {out['_error']} {out['_body']}")
        return out

    src = {}
    for key, spec in (("A", THREAD_A), ("B", THREAD_B)):
        hit = q(f"SELECT id::text FROM source WHERE url = '{spec['url']}'")
        src[key] = (
            hit[0]["id"]
            if hit
            else write("POST", "sources/", {"universe_id": DETROIT, **spec})["id"]
        )
        print(f"source {'on file' if hit else 'created'}: {spec['title']}")

    ids = {}
    for m in MEMBERS:
        hit = q(
            "SELECT m.id::text FROM member m JOIN member_set ms ON ms.member_id = m.id "
            f"WHERE m.universe_id = '{DETROIT}' AND ms.set_id = '{m['set']}' "
            f"AND m.nickname = '{m['nickname']}'"
        )
        if hit:
            ids[m["nickname"]] = hit[0]["id"]
            print(f"member on file: {m['nickname']}")
            continue
        out = write(
            "POST",
            "members/",
            {
                "universe_id": DETROIT,
                "nickname": m["nickname"],
                "status": m["status"],
                "aliases": m.get("aliases"),
                "affiliations": [{"set_id": m["set"], "is_primary": True}],
                "source_ids": [src[k] for k in m["sources"] if src[k]],
            },
        )
        ids[m["nickname"]] = out["id"]
        print(f"member created: {m['nickname']} ({m['status']})")

    # Darri was seeded ahead of this script, off the same thread; give him its source.
    darri = q(f"SELECT id::text FROM member WHERE universe_id = '{DETROIT}' AND nickname = 'Darri'")
    if darri and go:
        have = {
            r["source_id"]
            for r in q(
                f"SELECT source_id::text FROM member_source WHERE member_id = '{darri[0]['id']}'"
            )
        }
        if src["B"] not in have:
            write(
                "PATCH",
                f"members/{darri[0]['id']}?universe_id={DETROIT}",
                {"source_ids": sorted(have | {src["B"]})},
            )
            print("member updated: Darri, sourced to thread B")

    if ids.get("Dirty") and ids.get("Dez"):
        hit = q(
            "SELECT i.id::text FROM incident i "
            "JOIN incident_participant a ON a.incident_id = i.id "
            "JOIN incident_participant b ON b.incident_id = i.id "
            f"WHERE i.universe_id = '{DETROIT}' AND a.member_id = '{ids['Dirty']}' "
            f"AND b.member_id = '{ids['Dez']}'"
        )
        if hit:
            print("incident on file: the shooting of Dez")
        else:
            write(
                "POST",
                "incidents/",
                {
                    "universe_id": DETROIT,
                    "type": "SHOOTING",
                    "date": LAST_YEAR,
                    "municipality_id": DETROIT_CITY,
                    "narrative": "Dez was shot twelve times and survived.",
                    "participants": [
                        {"member_id": ids["Dirty"], "role": "SHOOTER", "outcome": "UNHARMED"},
                        {"member_id": ids["Dez"], "role": "VICTIM", "outcome": "INJURED"},
                    ],
                    "source_ids": [s for s in src.values() if s],
                },
            )
            print("incident created: the shooting of Dez, 2023")

    if not go:
        print("\ndry run. re-run with --go to write.")


if __name__ == "__main__":
    main()
