"""Date Nick's death from the candlelight post, and fold Rico into Domo.

Two findings, one write:

1. A third-party Facebook post dated 2010-10-14, "About to go Tto Nick candle
   light", puts the vigil in mid-October 2010. The death was previously only
   bounded by Carlos's 2011-01-13 RIP post. Recorded as October 2010, approx -
   a vigil is held the night of a death or within days, so the month holds and
   the day does not.

2. Dominiqque Brown is Domo, not Rico: the TTO roster carries Domo and no Rico,
   and the 2010-07-16 post signed "TTO RICO" is him addressing Rico, not
   signing as him. The rico-2 row was created from that misread. Domo takes the
   legal name, the ripdominic Facebook and Rico as an alias; rico-2 is deleted
   (it holds nothing else - no incidents, sources, aliases or spells).
"""

import sys

sys.path.insert(0, "/home/lbzgiu/squiidwiki/research/privedatabase/tools")
from wikiapi import Api  # noqa: E402

DETROIT = "4f57cae1-ebfe-408c-b435-052e2bd0ca45"
NICK = "a6f11dea-aa1a-44e4-ae6c-4bebddcf8b6a"
CARLOS = "aa627528-2790-429b-887c-03f4a3dc22af"
DOMO = "6122980a-9b50-4892-8fde-dfecc73918b4"
RICO = "083d2b06-b477-4df4-8f56-485905dfd74e"

GO = "--go" in sys.argv
api = Api()


def patch(mid, payload, what):
    """PATCH one member, or print what it would send when not --go."""
    if not GO:
        print(f"DRY  {what}: {payload}")
        return
    r = api.call("PATCH", f"members/{mid}?universe_id={DETROIT}", payload)
    if isinstance(r, dict) and r.get("_error"):
        sys.exit(f"FAILED {what}: {r}")
    print(f"OK   {what}")


patch(
    NICK,
    {
        "date_of_death": {
            "year": 2010,
            "month": 10,
            "day": None,
            "precision": "YM",
            "approx": True,
        },
        "family": {"brother": [CARLOS, DOMO]},
    },
    "Nick: death October 2010 (approx), brothers Carlos + Domo",
)

patch(
    DOMO,
    {
        "legal_name": "Dominiqque Brown",
        "aliases": ["Rico"],
        "social_media": {"facebook": "https://www.facebook.com/ripdominic"},
        "family": {"brother": [NICK, CARLOS]},
    },
    "Domo: legal name, alias Rico, Facebook, brothers Nick + Carlos",
)

patch(CARLOS, {"family": {"brother": [NICK, DOMO]}}, "Carlos: brothers Nick + Domo")

if GO:
    r = api.call("DELETE", f"members/{RICO}?universe_id={DETROIT}")
    if isinstance(r, dict) and r.get("_error"):
        sys.exit(f"FAILED delete rico-2: {r}")
    print("OK   deleted rico-2")
else:
    print("DRY  delete rico-2")
