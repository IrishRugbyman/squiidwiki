"""Undo the Rico-into-Domo merge: Domo's Facebook is Linwood Tto Domo.

The merge rested on the TTO roster carrying Domo and no Rico. Domo's profile
settles it the other way: @linwood.t.domo, display name "Linwood Tto Domo", a
Linwood man, not Dominiqque Brown. Pritch's handle carries the same street
(@linwood.mcgiver), which is what Linwood in a Detroit handle means - a street,
never a surname. Dominiqque Brown / @ripdominic is a different man, and the
rico-2 row was right.

The deleted row is restored from its own audit-log DELETE snapshot, with its
original id, so every family link and every reference in the commit history
still resolves. Domo keeps nothing from the merge but gains his real profile.

Dry-run by default; --go writes.
"""

import json
import subprocess
import sys

sys.path.insert(0, "/home/lbzgiu/squiidwiki/research/privedatabase/tools")
from wikiapi import Api  # noqa: E402

DETROIT = "4f57cae1-ebfe-408c-b435-052e2bd0ca45"
TTO = "65567fc2-f41b-419d-b569-3eccabdf2161"
NICK = "a6f11dea-aa1a-44e4-ae6c-4bebddcf8b6a"
CARLOS = "aa627528-2790-429b-887c-03f4a3dc22af"
DOMO = "6122980a-9b50-4892-8fde-dfecc73918b4"
RICO = "083d2b06-b477-4df4-8f56-485905dfd74e"
ADMIN = "e44913fe-9a60-4ff6-9728-82abf2804c1a"

GO = "--go" in sys.argv


def sql(statement):
    """Run one statement against prod, or print it when not --go."""
    if not GO:
        print("DRY  " + " ".join(statement.split())[:160])
        return
    r = subprocess.run(
        ["psql", "-d", "squiidwiki_prod", "-v", "ON_ERROR_STOP=1", "-c", statement],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        sys.exit(f"psql failed: {r.stderr.strip()}")
    print("OK   " + r.stdout.strip())


family = json.dumps({"brother": [NICK, CARLOS]})
social = json.dumps({"facebook": "https://www.facebook.com/ripdominic"})

# 1. The row itself, straight off the DELETE snapshot, id included.
sql(
    f"""INSERT INTO member (id, universe_id, nickname, legal_name, nickname_unknown,
        aliases, biography, status, family, social_media, created_at, updated_at,
        created_by_id, slug, is_rapper)
    VALUES ('{RICO}', '{DETROIT}', 'Rico', 'Dominiqque Brown', false,
        NULL, '', 'UNKNOWN', '{family}'::jsonb, '{social}'::jsonb, now(), now(),
        '{ADMIN}', 'rico-2', false);"""
)

# 2. His one TTO membership, dropped by the delete cascade.
sql(
    f"""INSERT INTO member_set (id, member_id, set_id, is_primary)
    VALUES (gen_random_uuid(), '{RICO}', '{TTO}', false);"""
)

# 3. An audit row, so the restore is not a silent write.
note = json.dumps(
    {
        "id": RICO,
        "slug": "rico-2",
        "nickname": "Rico",
        "legal_name": "Dominiqque Brown",
        "restored_from": "audit_log DELETE d8cbfe89-377c-43c8-b124-77f96fc5c380",
        "why": "Domo is @linwood.t.domo (Linwood Tto Domo), so the merge into Domo was wrong.",
    }
)
sql(
    f"""INSERT INTO audit_log (id, user_id, entity_type, entity_id, action, diff_json, created_at)
    VALUES (gen_random_uuid(), '{ADMIN}', 'member', '{RICO}', 'CREATE',
        '{note}'::jsonb, now());"""
)

# 4. Family links back onto Rico, and Domo stripped of everything the merge gave him.
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


patch(NICK, {"family": {"brother": [CARLOS, RICO]}}, "Nick: brothers Carlos + Rico")
patch(CARLOS, {"family": {"brother": [NICK, RICO]}}, "Carlos: brothers Nick + Rico")
patch(
    DOMO,
    {
        "legal_name": None,
        "aliases": [],
        "family": {},
        "social_media": {"facebook": "https://www.facebook.com/linwood.t.domo"},
    },
    "Domo: merge undone, real profile linwood.t.domo",
)
