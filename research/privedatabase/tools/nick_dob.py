"""Give Nick his date of birth, and trim the bio the columns now cover.

A memorial post on one of his photos, "you turned 21 today", timestamped 2:14 PM
on 21 mars 2017. The screenshot renders in CET (UTC+1, EU summer time not until
26 March); Detroit was on EDT (UTC-4) from 12 March, so it is 09:14 Detroit on
the same day. Birthday 21 March, born 1996-03-21, dead at 14 in October 2010.

That makes "he was quite young" a restatement of two columns, so it comes out of
the biography and only the go-kart accident stays - the one thing no column holds.

Dry-run by default; --go writes.
"""

import sys

sys.path.insert(0, "/home/lbzgiu/squiidwiki/research/privedatabase/tools")
from wikiapi import Api  # noqa: E402

DETROIT = "4f57cae1-ebfe-408c-b435-052e2bd0ca45"
NICK = "a6f11dea-aa1a-44e4-ae6c-4bebddcf8b6a"
GO = "--go" in sys.argv

payload = {
    "dob": {"year": 1996, "month": 3, "day": 21, "precision": "YMD", "approx": False},
    "biography": "Died in a go-kart accident.",
}

if not GO:
    print("DRY  Nick:", payload)
else:
    api = Api()
    r = api.call("PATCH", f"members/{NICK}?universe_id={DETROIT}", payload)
    if isinstance(r, dict) and r.get("_error"):
        sys.exit(f"FAILED: {r}")
    print("OK   Nick: dob 1996-03-21, bio trimmed")
