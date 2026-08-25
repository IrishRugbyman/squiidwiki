"""Identify Beezy as Rodney Autrey and seed the killing of 26 October 2010.

Beezy was on file as BCB and DEAD, dated 26 October 2010, with no legal name
and no incident. The 2010 homicide list holds four Detroit killings on that
date:

    Cassandra Evans   35   15382 Woodingham
    Keylen Philyaw    31   21435 W. 8 Mile
    Rodney Autrey     22   21435 W. 8 Mile
    Tammy Hayton      49   Waltham & Collingham

Only one of them is both young and inside BCB's own streets. 21435 W 8 Mile Rd
geocodes to 42.44329, -83.25436, and from there **Chapel Street is 68 m away**,
Burgess 205 m, Blackstone 257 m and Lahser Road 370 m - which is to say the
killing happened at the corner of the streets the set is named for, "Burgess,
Chapel, Blackstone Across Lahser". The user confirmed the identification from
a photograph.

The alliance the set belongs to is called **1026Family**, alias BeezyBoyz. The
name is the date: 10/26. That goes into the alliance description, which is
empty and is the only place that fact can live.

Keylen Philyaw was killed at the same address on the same day. Whether he was
BCB is not established, so he is parked in Unknown.

Neither man is in OTIS - no state record - and no press account of the killing
was found, so nobody is attributed to it and no set participant is written.

Idempotent. Dry-run by default; --go writes through the local API on :8001.
"""

import json
import sys
import uuid

sys.path.insert(0, "/home/lbzgiu/squiidape/squiidwiki/research/privedatabase/tools")
from wikiapi import Api, q  # noqa: E402

U = "4f57cae1-ebfe-408c-b435-052e2bd0ca45"  # Metro Detroit
UNKNOWN_SET = "f4bfd8ab-c0ce-458f-93eb-8d741109b077"
DETROIT_MUNI = "55d40a23-fdbe-4e83-b5b0-5670a04df4c9"
BEEZY = "b268b665-a31a-4393-aa56-48c43fef6ae0"  # the DEAD Beezy, not the FREE one
ALLIANCE = "91becc85-30c3-40f6-90e2-87a5541cde92"  # 1026Family

DATE = {"year": 2010, "month": 10, "day": 26, "precision": "YMD", "approx": False}
LOCATION = "21435 W 8 Mile Rd, Detroit"
LAT, LNG = 42.443292, -83.254357

CHAMSPAGE_2010 = {
    "universe_id": U,
    "url": "https://chamspage.blogspot.com/2011/11/2010-detroit-homicidemurder-list.html",
    "title": "2010 Detroit Homicide/Murder Victim List",
    "publication": "chamspage.blogspot.com",
    "accessed_at": "2026-08-21",
    "reliability": "MEDIUM",
    "notes": (
        "Personal blog compiling Detroit homicide victims by year. The 26 October 2010 "
        "entries include Rodney Autrey, 22, and Keylen Philyaw, 31, both at 21435 W. 8 Mile "
        "- the address that identifies Beezy, since it sits 68 m from Chapel Street."
    ),
}

ALLIANCE_DESCRIPTION = (
    "The name is a date. Beezy was killed on 26 October 2010 at Eight Mile and Chapel, and "
    "the alliance is called for the day."
)

NARRATIVE = (
    "Rodney Autrey and Keylen Philyaw were shot dead at the same address on West 8 Mile "
    "Road, where it meets Chapel, at the northern end of the streets BCB is named for. "
    "Nobody has been named to the killing."
)

GO = "--go" in sys.argv


def one(sql):
    """Run a query and return its first row, or None."""
    r = q(sql)
    return r[0] if r else None


def main():
    """Name Beezy, describe the alliance, and seed the double killing."""
    api = Api() if GO else None

    def call(method, path, payload):
        if not GO:
            print(f"  {method} {path}  {json.dumps(payload)[:120]}")
            return {"id": str(uuid.uuid4())}
        r = api.call(method, path, payload)
        if isinstance(r, dict) and r.get("_error"):
            sys.exit(f"{method} {path} failed: {r['_error']} {r['_body']}")
        return r

    print("== source")
    row = one(f"SELECT id FROM source WHERE universe_id='{U}' AND url='{CHAMSPAGE_2010['url']}'")
    src = row["id"] if row else call("POST", "sources/", CHAMSPAGE_2010)["id"]
    print("  exists" if row else "  created")

    print("== Beezy -> Rodney Autrey")
    cur = one(f"SELECT legal_name FROM member WHERE id='{BEEZY}'")
    if cur and cur.get("legal_name"):
        print(f"  already named: {cur['legal_name']}")
    else:
        call("PATCH", f"members/{BEEZY}?universe_id={U}", {"legal_name": "Rodney Autrey"})
        print("  named")

    print("== Keylen Philyaw")
    row = one(f"SELECT id FROM member WHERE universe_id='{U}' AND legal_name='Keylen Philyaw'")
    if row:
        keylen = row["id"]
        print("  exists")
    else:
        keylen = call(
            "POST",
            "members/",
            {
                "universe_id": U,
                "legal_name": "Keylen Philyaw",
                "nickname_unknown": True,
                "status": "DEAD",
                "date_of_death": DATE,
                "source_ids": [src],
                "affiliations": [{"set_id": UNKNOWN_SET, "is_primary": True}],
            },
        )["id"]

    print("== alliance description")
    a = one(f"SELECT description FROM alliance WHERE id='{ALLIANCE}'")
    if a and a.get("description"):
        print("  already set")
    else:
        call(
            "PATCH",
            f"alliances/{ALLIANCE}?universe_id={U}",
            {"description": ALLIANCE_DESCRIPTION},
        )
        print("  set")

    print("== incident")
    row = one(
        f"SELECT id FROM incident WHERE universe_id='{U}' "
        "AND date->>'year'='2010' AND date->>'month'='10' AND date->>'day'='26' "
        "AND location_text LIKE '21435 W 8 Mile%'"
    )
    if row:
        print("  exists")
    else:
        call(
            "POST",
            "incidents/",
            {
                "universe_id": U,
                "type": "MURDER",
                "date": DATE,
                "municipality_id": DETROIT_MUNI,
                "location_text": LOCATION,
                "lat": LAT,
                "lng": LNG,
                "narrative": NARRATIVE,
                "verified": True,
                "source_ids": [src],
                "participants": [
                    {"member_id": BEEZY, "role": "VICTIM", "outcome": "KILLED"},
                    {"member_id": keylen, "role": "VICTIM", "outcome": "KILLED"},
                ],
            },
        )
        print("  created")

    print("\nDRY RUN - re-run with --go" if not GO else "\ndone")


if __name__ == "__main__":
    main()
