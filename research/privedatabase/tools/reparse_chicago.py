"""Re-parse the Chicago pages, separating set pages from person pages.

Writes chi_sets.json and chi_people.json to the scratchpad. Both feed the
markdown assembly and the seeding scripts.

Why the split matters: a person page opens with a sentence about a person and
then carries the same CORPS / FUSILLADES / ASSISTANCES sections a set page uses
for its members. Treating line 0 as a set description leaves those sections
with no member to attach to, so the entry lines themselves became "members" -
85 of 726 names were really comma-runs like "Doc (Landlord COV)Dale (STL/EBT)".
"""

import collections
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from chiparse import HDR, SETHDR, entries, keyof, lines_of, parse_member, parse_page  # noqa: E402

SCRATCH = pathlib.Path(
    "/tmp/claude-1000/-home-lbzgiu-squiidwiki/e162f253-b7e6-408b-a995-a5bb3bb9c68d/scratchpad"
)
ROOT = pathlib.Path(__file__).resolve().parent.parent

SETDESC = re.compile(
    r"est une? sets?|est une? alliance|ennemis? (directs? )?avec"
    r"|fusionn[eé]s? avec|cliqued up avec|est un quartier",
    re.I,
)


def parse_person(page, lines):
    """Parse a person page: line 0 is the subject, later sections are their events."""
    who = parse_member(lines[0])
    sect = None
    for line in lines[1:]:
        header = HDR.match(line)
        if header:
            sect = keyof(header.group(1))
            continue
        if SETHDR.match(line):
            sect = None
            continue
        if sect:
            who.setdefault(sect, []).extend(entries(line))
    return who


def main():
    """Split every Chicago page into a set record or a person record."""
    pages = json.loads((ROOT / "raw/pages.json").read_text())
    owner = json.loads((SCRATCH / "wp_owner4.json").read_text())

    sets_out, people_out = {}, {}
    for page in pages:
        if owner.get(page["slug"]) != "chicago":
            continue
        lines = lines_of(page)
        if not lines:
            continue
        is_set = bool(SETDESC.search(lines[0])) or any(SETHDR.match(x) for x in lines)
        if is_set:
            parsed = parse_page(page)
            if not parsed:
                continue
            members = [m for m in parsed["members"] if not m["name"].endswith(":")]
            if members or parsed.get("members_listed") or parsed.get("set_bodies"):
                sets_out[str(page["ID"])] = {
                    "title": page["title"],
                    "url": page["URL"],
                    "author": page["author"],
                    "date": page["date"][:10],
                    "members": members,
                    "members_listed": parsed.get("members_listed", []),
                    "set_bodies": parsed.get("set_bodies", []),
                }
        else:
            who = parse_person(page, lines)
            if who["name"]:
                people_out[str(page["ID"])] = {
                    "title": page["title"],
                    "url": page["URL"],
                    "author": page["author"],
                    "date": page["date"][:10],
                    **who,
                }

    (SCRATCH / "chi_sets.json").write_text(json.dumps(sets_out, ensure_ascii=False))
    (SCRATCH / "chi_people.json").write_text(json.dumps(people_out, ensure_ascii=False))

    members = [m for v in sets_out.values() for m in v["members"]]
    suspect = [m["name"] for m in members if len(m["name"]) > 34 or re.search(r"\)\w", m["name"])]
    print(f"set pages          : {len(sets_out)}")
    print(f"  members in them  : {len(members)}")
    print(f"  suspect names    : {len(suspect)}")
    print(f"person pages       : {len(people_out)}")
    events = collections.Counter()
    for v in sets_out.values():
        for m in v["members"]:
            for key in ("bodies", "shootings", "assists"):
                events[key] += len(m.get(key, []))
    person_events = collections.Counter()
    for v in people_out.values():
        for key in ("bodies", "shootings", "assists"):
            person_events[key] += len(v.get(key, []))
    print(f"  events on set members : {dict(events)}")
    print(f"  events on person pages: {dict(person_events)}")


if __name__ == "__main__":
    main()
