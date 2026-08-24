"""Complete the Band Crew alliance: its eight subsets, Squid, Malik, and a founding date.

Follows seed_bandcrew_indictment.py, which seeded the 2015 federal case. This one
works from the source's own Band Crew page (1389) plus one external confirmation.

  subsets     The Band Crew page names eight member sets - MOA, LCM, LCF, CMH,
              LPB, SHN, YNC, YPB. Only CMH and YNC were on file (PBF is a ninth,
              from the federal indictment, and is not on that page). The other
              six are created here, rosterless by design - the gap is a queue,
              not a claim that they are empty. Their allies need no wiring:
              _sync_alliance_auto_allies fires on create and makes every set in
              an alliance FRIEND with every other, which is why the nine end up
              fully connected. That is the app's model of an alliance, so MOA,
              LCM and LCF get allies the source never listed for them.
  founded_at  "aux environs de Novembre 2011", so YM precision and approx.
              The same page confirms the CEO / Co-CEO titles independently of
              the indictment.
  Squid       Marcus Jackson, killed 11 May 2012 aged 23, YNC before Band Crew
              existed and one of its founders. Confirmed by an outside 2012
              Detroit homicide list, which is also where the location comes
              from: entry 122 of that year, 9900 St. Mary's Street. Geocoded
              via Nominatim, so the incident carries a real point and not just
              a municipality.
  Malik       The one person the Band Crew page ties to YPB.

The incident carries no narrative and Squid's biography is one sentence, because
the date, the place, the set, the status and the victim role are all columns.
Founding an alliance is not, and that is the only thing left to write down.

Idempotent. Dry-run by default; --go writes through the local API (port 8001, prod DB).
"""

import sys

from wikiapi import Api, q

DETROIT = "4f57cae1-ebfe-408c-b435-052e2bd0ca45"

HOMICIDE_LIST = {
    "url": "http://chamspage.blogspot.com/2012/05/2012-detroit-homicidesmurders-partial.html",
    "title": "2012 Detroit Homicides/Murders List",
    "publication": "Miscellaneous Posts (blog)",
    "published_at": {"year": 2012, "month": 5, "day": None, "precision": "YM", "approx": False},
    "accessed_at": "2026-08-24",
    "reliability": "MEDIUM",
    "notes": (
        "Volunteer-compiled partial list of the 386 Detroit homicides of 2012, one row per "
        "victim: number, date, name, age and the address block where the body was found. "
        "Entry 122 is Marcus Jackson, 23, 9900 St. Mary's Street, 05/11/12, which matches "
        "the name, age and date already on file for Squid and adds the location."
    ),
}

# Band Crew subsets named on page 1389 that were not already on file. YPB, LPB
# and SHN are also on the Detroit set index and on the CMH and YNC ally lists;
# MOA, LCM and LCF are named nowhere but the alliance page.
NEW_SETS = ["YPB", "LPB", "SHN", "MOA", "LCM", "LCF"]

SQUID_LOCATION = "9900 block of St. Mary's Street"
SQUID_LAT, SQUID_LNG = 42.367842, -83.204486


def main(go):
    """Create the six subsets, Squid with his incident, Malik, and date the alliance."""
    api = Api()
    sets = {
        r["name"]: r["id"]
        for r in q(f"SELECT name, id::text FROM sets WHERE universe_id = '{DETROIT}'")
    }
    muni = q("SELECT id::text FROM municipality WHERE name = 'Detroit'")[0]["id"]
    bandcrew = q(
        f"SELECT id::text FROM alliance WHERE name = 'BandCrew' AND universe_id = '{DETROIT}'"
    )[0]["id"]

    def write(method, path, payload=None):
        if not go:
            print(f"[dry] {method} {path}")
            return {"id": None}
        out = api.call(method, path, payload)
        if isinstance(out, dict) and "_error" in out:
            sys.exit(f"{method} {path} -> {out['_error']} {out['_body']}")
        return out

    hit = q(f"SELECT id::text FROM source WHERE url = '{HOMICIDE_LIST['url']}'")
    source_id = (
        hit[0]["id"]
        if hit
        else write("POST", "sources/", {"universe_id": DETROIT, **HOMICIDE_LIST})["id"]
    )
    print(f"source {'on file' if hit else 'created'}: {HOMICIDE_LIST['title']}")

    for name in NEW_SETS:
        if name in sets:
            print(f"skip (already on file): set {name}")
            continue
        sets[name] = write(
            "POST",
            "sets/",
            {
                "universe_id": DETROIT,
                "name": name,
                "status": "ACTIVE",
                "alliance_id": bandcrew,
                "municipality_id": muni,
            },
        )["id"]
        print(f"set created: {name} (auto-allied to the rest of BandCrew)")

    # Squid. The incident is what makes him dead: creating it with outcome=KILLED
    # fires the death sync, which sets status, date_of_death and death_incident_id.
    squid = q(
        f"SELECT id::text FROM member WHERE universe_id = '{DETROIT}' AND legal_name = 'Marcus Jackson'"
    )
    if squid:
        print("skip (already on file): Squid / Marcus Jackson")
    else:
        squid_id = write(
            "POST",
            "members/",
            {
                "universe_id": DETROIT,
                "nickname": "Squid",
                "legal_name": "Marcus Jackson",
                "status": "UNKNOWN",
                "biography": "One of the founders of Band Crew.",
                "affiliations": [{"set_id": sets["YNC"], "is_primary": True}],
                "source_ids": [source_id],
            },
        )["id"]
        print("member created: Squid / Marcus Jackson (YNC)")

        write(
            "POST",
            "incidents/",
            {
                "universe_id": DETROIT,
                "type": "MURDER",
                "date": {"year": 2012, "month": 5, "day": 11, "precision": "YMD", "approx": False},
                "municipality_id": muni,
                "location_text": SQUID_LOCATION,
                "lat": SQUID_LAT,
                "lng": SQUID_LNG,
                "participants": [{"member_id": squid_id, "role": "VICTIM", "outcome": "KILLED"}],
                "source_ids": [source_id],
            },
        )
        print(f"incident created: 2012-05-11 MURDER, {SQUID_LOCATION} ({SQUID_LAT}, {SQUID_LNG})")

    malik = q(
        f"SELECT m.id::text FROM member m JOIN member_set ms ON ms.member_id = m.id "
        f"JOIN sets s ON s.id = ms.set_id "
        f"WHERE m.universe_id = '{DETROIT}' AND m.nickname = 'Malik' AND s.name = 'YPB'"
    )
    if malik:
        print("skip (already on file): Malik")
    else:
        write(
            "POST",
            "members/",
            {
                "universe_id": DETROIT,
                "nickname": "Malik",
                "status": "UNKNOWN",
                "affiliations": [{"set_id": sets["YPB"], "is_primary": True}],
            },
        )
        print("member created: Malik (YPB)")

    write(
        "PATCH",
        f"alliances/{bandcrew}?universe_id={DETROIT}",
        {
            "founded_at": {
                "year": 2011,
                "month": 11,
                "day": None,
                "precision": "YM",
                "approx": True,
            },
        },
    )
    print("alliance patched: BandCrew (founded_at ~November 2011)")


if __name__ == "__main__":
    main("--go" in sys.argv)
