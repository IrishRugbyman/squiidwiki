"""Nick's exact span: 1996-03-21 to 2010-10-08.

The birth date already matched. The death moves from October 2010 (approx) to
2010-10-08 exactly, which puts the candlelight vigil six days after - within the
window a vigil implies, so the estimate held and now gives way to the record.
Age at death 14, unchanged.
"""

import sys

sys.path.insert(0, "/home/lbzgiu/squiidape/squiidwiki/research/privedatabase/tools")
from wikiapi import Api  # noqa: E402

DETROIT = "4f57cae1-ebfe-408c-b435-052e2bd0ca45"
NICK = "a6f11dea-aa1a-44e4-ae6c-4bebddcf8b6a"
GO = "--go" in sys.argv

payload = {
    "dob": {"year": 1996, "month": 3, "day": 21, "precision": "YMD", "approx": False},
    "date_of_death": {"year": 2010, "month": 10, "day": 8, "precision": "YMD", "approx": False},
}

if not GO:
    print("DRY  Nick:", payload)
else:
    api = Api()
    r = api.call("PATCH", f"members/{NICK}?universe_id={DETROIT}", payload)
    if isinstance(r, dict) and r.get("_error"):
        sys.exit(f"FAILED: {r}")
    print("OK   Nick: 1996-03-21 to 2010-10-08")
