"""Seed the killing of To-To (Otis Waller Jr), 7 April 2008, into Metro Detroit.

To-To is already a member: BCB, DEAD, born 16 October 1989, died 7 April 2008.
What he did not have was an incident row, so his death sat in a column with
nothing behind it and no `death_incident_id`.

The killing matters beyond itself. *People v Morton* records that BCB gathered
at Henry Ford High School six months later to take on FOE Life "in memory of or
in retribution for a deceased friend, To-To", and that Morton walked up to
Christopher Walker saying "To-To says what's up". So this incident is the
stated cause of the one seeded by `seed_hfhs_2008.py`.

**And the date of that retaliation is his birthday.** He was born 16 October
1989; Walker was killed 16 October 2008, the day To-To would have turned 19.
The date of birth is the user's own research, the date of death and the address
come from the homicide list, and the motive comes from the appellate opinion -
three independent inputs, which is what makes the coincidence worth stating.

Location: 18551 Pierson St, Sunbeam Heights, Detroit 48219, geocoded to
42.4251298, -83.2472397. That sits inside the cluster of streets BCB is named
for - Burgess, Chapel and Blackstone are all 48219, within about a kilometre -
so he was killed on his own set's ground.

**No shooter and no set are attributed.** Nobody was ever named to this killing
in anything on file. That BCB blamed FOE Life is evidenced by the retaliation,
but BCB's belief is not a finding, so no `incident_set_participant` row is
written either. The incident carries a victim and nothing more.

Idempotent. Dry-run by default; --go writes through the local API on :8001.
"""

import json
import sys
import uuid

sys.path.insert(0, "/home/lbzgiu/squiidape/squiidwiki/research/privedatabase/tools")
from wikiapi import Api, q  # noqa: E402

U = "4f57cae1-ebfe-408c-b435-052e2bd0ca45"  # Metro Detroit
DETROIT_MUNI = "55d40a23-fdbe-4e83-b5b0-5670a04df4c9"
TOTO = "8f4645b0-8a8c-4d89-957a-1260a8b4ed92"

CHAMSPAGE_2008 = {
    "universe_id": U,
    "url": "http://chamspage.blogspot.com/2011/11/2008-detroit-homicidesmurder-list.html",
    "title": "2008 Detroit Homicide/Murder Victim List",
    "publication": "chamspage.blogspot.com",
    "accessed_at": "2026-08-21",
    "reliability": "MEDIUM",
    "notes": (
        "Personal blog compiling Detroit homicide victims by year, with date, name, age "
        "and block. Entry 74: 04/07/08, OTIS WALLER JR., 18, 18551 PIERSON. Rated MEDIUM "
        "to match the 2012 list already on file; the compilation is careful and its dates "
        "and addresses have checked out against court records, but it is not official."
    ),
}

LOCATION = "18551 Pierson St, Sunbeam Heights, Detroit"
GO = "--go" in sys.argv


def one(sql):
    """Run a query and return its first row, or None."""
    r = q(sql)
    return r[0] if r else None


def main():
    """Create the source and the incident, and let the death sync link them."""
    api = Api() if GO else None

    def post(path, payload):
        if not GO:
            print(f"  POST {path}  {json.dumps(payload)[:160]}")
            return {"id": str(uuid.uuid4())}
        r = api.call("POST", path, payload)
        if isinstance(r, dict) and r.get("_error"):
            sys.exit(f"POST {path} failed: {r['_error']} {r['_body']}")
        return r

    print("== source")
    url = CHAMSPAGE_2008["url"]
    row = one(f"SELECT id FROM source WHERE universe_id='{U}' AND url='{url}'")
    if row:
        print("  exists")
        src = row["id"]
    else:
        src = post("sources/", CHAMSPAGE_2008)["id"]

    print("== incident")
    row = one(
        f"SELECT id FROM incident WHERE universe_id='{U}' "
        "AND date->>'year'='2008' AND date->>'month'='4' AND date->>'day'='7' "
        "AND location_text LIKE '18551 Pierson%'"
    )
    if row:
        print("  exists")
        return

    post(
        "incidents/",
        {
            "universe_id": U,
            "type": "MURDER",
            "date": {"year": 2008, "month": 4, "day": 7, "precision": "YMD", "approx": False},
            "municipality_id": DETROIT_MUNI,
            "location_text": LOCATION,
            "lat": 42.4251298,
            "lng": -83.2472397,
            "narrative": (
                "Otis Waller Jr, 18, was killed on Pierson, inside the run of streets his "
                "set is named for. Nobody was named to the killing. Six months later, on "
                "what would have been his nineteenth birthday, BCB gathered at Henry Ford "
                "High School to take on FOE Life in retribution for his death, and "
                "Christopher Walker was killed there."
            ),
            "verified": True,
            "source_ids": [src],
            "participants": [{"member_id": TOTO, "role": "VICTIM", "outcome": "KILLED"}],
        },
    )
    print("  created")


if __name__ == "__main__":
    main()
