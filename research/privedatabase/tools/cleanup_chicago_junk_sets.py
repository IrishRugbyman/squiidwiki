"""Remove the Chicago "sets" that are really kinship parentheticals.

Roster entries like "Lil Ant (frère de 5ive et de 051 Young Money Zeko)" were
read by the member seed as "Lil Ant, of the set 'frère de 5ive et de 051 Young
Money Zeko'", so sixteen one-member sets exist whose name is a sentence. The
relation itself is now written to member.family by extract_chicago_family.py.
This puts each stranded member back on the set whose roster named them (the
page the parenthetical came from) and deletes the junk set. Also catches the
'ZoLand. C'était un 4 Corne' truncation.

Dry-run by default; --go applies through the API.
"""

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from chiparse import HDR, SETHDR, lines_of  # noqa: E402
from db_sync import candidates, norm  # noqa: E402
from wikiapi import CHICAGO, Api, q  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Kinship parentheticals ("frere de X"), a truncated sentence ("ZoLand. C'etait"),
# and the rest of what a roster puts in brackets that is not a set at all: a
# status, a charge, an age, a slur, a role. All of them reached the sets table
# because the seed read "Name (anything)" as "Name, of the set 'anything'".
#
# The lowercase-start test is deliberately NOT case-insensitive: with re.I the
# class matches capitals too and the pattern swallows every set in the universe.
JUNK_KIN = re.compile(
    r"^(fr[èe]re|soeur|sœur|cousine?|fils|p[èe]re|oncle|neveu|femme|mari|demi-fr[èe]re|"
    r"petit fr[èe]re|grand fr[èe]re) d|\. [A-Z]",
    re.I,
)
JUNK_LOWER = re.compile(r"^[a-zà-ÿ]")
JUNK_WORD = re.compile(
    r"^(affili[ée]|condamn[ée]|arr[êe]t[ée]|enfant|tireur|assistance|rappeu)", re.I
)
# "PMBMB affiliee" is a qualifier trailing a real set name, not a set of its own:
# the source calls Ayanna an affiliate of PMBMB, and PMBMB itself exists.
JUNK_SUFFIX = re.compile(r"\saffili[ée]e?$", re.I)


def is_junk(name):
    """True when this set name is really a roster parenthetical, not a set."""
    return bool(
        JUNK_KIN.search(name)
        or JUNK_LOWER.match(name)
        or JUNK_WORD.match(name)
        or JUNK_SUFFIX.search(name)
    )


sets = q(f"SELECT id, name FROM sets WHERE universe_id='{CHICAGO}'")
junk = [s for s in sets if is_junk(s["name"])]
setidx = {}
for s in sets:
    if s in junk:
        continue
    for k in candidates(s["name"]):
        setidx.setdefault(k, s["id"])
owner = json.loads((ROOT / "tools/wp-owner.json").read_text())
pages = [
    p
    for p in json.loads((ROOT / "raw/pages.json").read_text())
    if owner.get(p["slug"]) == "chicago"
]


def home_set(junk_name):
    """Where the parenthetical came from: (set id, page title, section).

    Only a MEMBRES roster makes the entry a member of the page's set. Under a
    CORPS list the entry is a victim of that set, whose own set is unknown, so
    the caller must leave them set-less.
    """
    needle = norm(junk_name)
    for p in pages:
        section = "desc"
        for line in lines_of(p):
            sh = SETHDR.match(line)
            if sh:
                head = sh.group(1).upper()
                section = (
                    "roster"
                    if head.startswith(("MEMBRES", "LISTE DES MEMBRES"))
                    else "bodies"
                    if "CORPS" in head
                    else "other"
                )
                continue
            if HDR.match(line):
                section = "bodies"
                continue
            if needle and needle in norm(line) and "(" in line:
                for k in candidates(p["title"]):
                    if k in setidx:
                        return setidx[k], p["title"], section
    return None, None, None


plan = []
for s in junk:
    members = q(
        f"""SELECT m.id, m.nickname,
                   coalesce((SELECT json_agg(ms.set_id::text) FROM member_set ms WHERE ms.member_id=m.id),'[]') AS set_ids
            FROM member m JOIN member_set ms ON ms.member_id=m.id WHERE ms.set_id='{s["id"]}'"""
    )
    sid, title, section = home_set(s["name"])
    if section != "roster":
        sid = None
    plan.append((s, members, sid, title))
    print(f"\n{s['name']!r}  (found on {title!r}, section {section})")
    for m in members:
        other = [x for x in m["set_ids"] if x != s["id"]]
        action = (
            "already elsewhere"
            if other
            else (
                f"-> attach to {title!r}"
                if sid
                else "-> left set-less (victim entry or no roster found)"
            )
        )
        print(f"   {m['nickname']!r}: {action}")

if "--go" not in sys.argv:
    print(f"\n{len(plan)} junk sets. DRY RUN - re-run with --go")
    sys.exit()

api = Api()
for s, members, sid, _title in plan:
    for m in members:
        if sid and sid not in m["set_ids"]:
            cur = api.call("GET", f"members/{m['id']}?universe_id={CHICAGO}")
            aff = [
                {
                    "set_id": a["set_id"],
                    "rank": a.get("rank"),
                    "is_primary": a.get("is_primary", False),
                    "from_date": a.get("from_date"),
                }
                for a in (cur or {}).get("affiliations", [])
                if a["set_id"] != s["id"]
            ]
            aff.append({"set_id": sid, "is_primary": not any(a["is_primary"] for a in aff)})
            r = api.call("PATCH", f"members/{m['id']}?universe_id={CHICAGO}", {"affiliations": aff})
            if r and r.get("_error"):
                print("  attach failed:", m["nickname"], r)
    r = api.call("DELETE", f"sets/{s['id']}?universe_id={CHICAGO}")
    print(
        f"deleted {s['name']!r}"
        if not (r or {}).get("_error")
        else f"delete failed {s['name']!r}: {r}"
    )
