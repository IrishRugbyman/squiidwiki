"""Seed the September 2015 Band Crew federal RICO indictment into Metro Detroit.

Source: United States v. Mapp et al. (E.D. Mich., 16 Sep 2015), read via the
Equipo Nizkor mirror because justice.gov serves its own copy behind a
bot-verification wall. The charging document is the first HIGH-reliability
source in the Detroit universe: it is the only thing on file that carries
legal names, and it settles four separate questions the research corpus could
only assert.

  legal names   Seven of the eight defendants' a.k.a.s match nicknames already
                on the CMH and YNC rosters (Lil Corey, Mel, Bam, Joesky, Trick,
                Keem, Gwopp). The eighth, Rio, was already on file as Mario
                Perkins, which is what makes the other seven safe to attach:
                six-of-six overlap on a twelve-name roster is not coincidence.
  rank          "CEO" and "Co-CEO" are not decoration. The indictment states
                that the leaders of each subgroup were known by those titles,
                and SetRank already has exactly those two values, so every
                a.k.a. of the form "CEO X" lands in member_set.rank.
  structure     Band Crew had no formal hierarchy above its subgroup leaders.
  territory     A boundary box, finer than the municipality column can hold, so
                it goes in the alliance description with the graffiti tags.

Nothing is written to a biography: once legal_name, the affiliation, the rank
and the source link are filled, nothing survives the state-versus-circumstance
strip.

Idempotent - a member whose legal_name is already on file is left alone.
Dry-run by default; --go writes through the local API (port 8001, prod DB).
"""

import sys

from wikiapi import Api, q

DETROIT = "4f57cae1-ebfe-408c-b435-052e2bd0ca45"

INDICTMENT = {
    "url": "http://www.derechos.org/nizkor/corru/doc/bandcrew1.html",
    "title": "Band Crew RICO indictment, United States v. Mapp et al. (E.D. Mich.)",
    "publication": "U.S. District Court, Eastern District of Michigan",
    "published_at": {"year": 2015, "month": 9, "day": 16, "precision": "YMD", "approx": False},
    "accessed_at": "2026-08-24",
    "reliability": "HIGH",
    "notes": (
        "Charging document. Names eight defendants with their aliases, defines Band Crew "
        "as an association of CMH, YNC, PBF and FOE Life, and fixes the territory and the "
        "graffiti used to claim it. Read via the Equipo Nizkor mirror; justice.gov serves "
        "its own copy behind a bot-verification wall."
    ),
}

PRESS_RELEASE = {
    "url": (
        "https://www.justice.gov/archives/opa/pr/"
        "eight-members-violent-detroit-street-gang-charged-rico-and-firearms-offenses"
    ),
    "title": "Eight members of violent Detroit street gang charged with RICO and firearms offenses",
    "publication": "U.S. Department of Justice",
    "published_at": {"year": 2015, "month": 9, "day": 22, "precision": "YMD", "approx": False},
    "accessed_at": "2026-08-24",
    "reliability": "HIGH",
    "notes": (
        "Press release announcing the indictment. Gives each defendant's age and charges. "
        "Mirror without the bot wall: http://www.derechos.org/nizkor/corru/doc/bandcrew.html"
    ),
}

# nickname, legal name, set name, rank, aliases as charged
ROSTER = [
    ("Lil Corey", "Corey Deandre Mapp", "CMH", "CEO", ["CEO Corey"]),
    ("Mel", "Jamell Loval Smith", "CMH", "CEO", ["CEO Mel"]),
    ("Trick", "Travontae Javon Joseph", "CMH", "CEO", ["CEO Trick"]),
    ("Joesky", "Joseph Hezekiah Ford", "CMH", "CO_CEO", ["Co-CEO Joesky"]),
    ("Bam", "Leo James Johnson", "CMH", None, []),
    ("Keem", "Akeem Arteaze Walker", "CMH", None, []),
    ("Gwopp", "Alexander Teontae Johnson", "YNC", "CEO", ["CEO Gwopp"]),
]

BANDCREW_DESCRIPTION = (
    "An association of smaller gangs with no formal hierarchy above the leadership of "
    "each subgroup. Its territory sits in northwest Detroit around Seven Mile Road, "
    "bounded by the Southfield Freeway to the west, Greenfield Road to the east, "
    "Eight Mile Road to the north and West McNichols Road to the south. Members claimed "
    "it in graffiti reading #22 BandCrew, BAND CREW, 22 BAND CREW, YNCMH and PBF.\n\n"
    "https://www.facebook.com/profile.php?id=100068233114723"
)


def main(go):
    """Create the two sources, the YNC set and the seven members, then patch BandCrew."""
    api = Api()
    sets = {
        r["name"]: r["id"]
        for r in q(f"SELECT name, id::text FROM sets WHERE universe_id = '{DETROIT}'")
    }
    muni = q("SELECT id::text FROM municipality WHERE name = 'Detroit'")[0]["id"]
    bandcrew = q(
        f"SELECT id::text FROM alliance WHERE name = 'BandCrew' AND universe_id = '{DETROIT}'"
    )[0]["id"]
    on_file = {
        r["legal_name"]
        for r in q(
            f"SELECT legal_name FROM member WHERE universe_id = '{DETROIT}' AND legal_name <> ''"
        )
    }

    def write(method, path, payload=None):
        if not go:
            print(f"[dry] {method} {path}")
            return {"id": None}
        out = api.call(method, path, payload)
        if isinstance(out, dict) and "_error" in out:
            sys.exit(f"{method} {path} -> {out['_error']} {out['_body']}")
        return out

    source_ids = []
    for spec in (INDICTMENT, PRESS_RELEASE):
        hit = q(f"SELECT id::text FROM source WHERE url = '{spec['url']}'")
        source_ids.append(
            hit[0]["id"]
            if hit
            else write("POST", "sources/", {"universe_id": DETROIT, **spec})["id"]
        )
        print(f"source {'on file' if hit else 'created'}: {spec['title'][:60]}")

    if "YNC" not in sets:
        sets["YNC"] = write(
            "POST",
            "sets/",
            {
                "universe_id": DETROIT,
                "name": "YNC",
                "name_variants": [
                    {
                        "name": "Young N Crispy",
                        "initials": "YNC",
                        "lead": "initials",
                        "is_primary": True,
                    }
                ],
                "status": "ACTIVE",
                "alliance_id": bandcrew,
                "municipality_id": muni,
                "friend_ids": [sets["PBF"], sets["CMH"]],
                "enemy_ids": [sets["ASBH"], sets["TTO"]],
            },
        )["id"]
        print("set created: YNC")

    for nickname, legal, set_name, rank, aliases in ROSTER:
        if legal in on_file:
            print(f"skip (already on file): {nickname} / {legal}")
            continue
        write(
            "POST",
            "members/",
            {
                "universe_id": DETROIT,
                "nickname": nickname,
                "legal_name": legal,
                "aliases": aliases or None,
                "status": "UNKNOWN",
                "affiliations": [{"set_id": sets[set_name], "rank": rank, "is_primary": True}],
                "source_ids": source_ids,
            },
        )
        print(f"member created: {nickname} / {legal} ({set_name}{'/' + rank if rank else ''})")

    # Rio was on file before this document was read; attach it to him too.
    rio = q(
        f"SELECT id::text FROM member WHERE universe_id = '{DETROIT}' AND legal_name = 'Mario Perkins'"
    )
    if rio:
        write("PATCH", f"members/{rio[0]['id']}?universe_id={DETROIT}", {"source_ids": source_ids})
        print("member patched: Rio / Mario Perkins (sources)")

    write(
        "PATCH",
        f"alliances/{bandcrew}?universe_id={DETROIT}",
        {
            "aliases": ["NSC", "NevaStopCashing", "22 Band Crew", "BC"],
            "description": BANDCREW_DESCRIPTION,
        },
    )
    print("alliance patched: BandCrew (aliases, description)")


if __name__ == "__main__":
    main("--go" in sys.argv)
