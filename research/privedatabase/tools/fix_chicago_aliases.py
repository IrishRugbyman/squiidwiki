"""Repair Chicago member aliases that the old quote regex glued together.

Before the chiparse fix, ALIAS opened on « " “ but only closed on » " ”, so a
naming clause written with mixed marks ("“Wop“, «Dooski»") came through as one
alias ('Wop“, «Dooski'), and a quote in later prose could swallow a paragraph.
This re-derives aliases and legal name for every Chicago member whose stored
aliases still carry a quote mark or run past 40 characters, from the same
source sentences, with the fixed parser.

Dry-run by default; --go PATCHes the rows through the API.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from chiparse import ALIAS, EMBEDDED_NICK, lines_of, parse_member  # noqa: E402
from db_sync import norm  # noqa: E402
from wikiapi import CHICAGO, Api, q  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
# One member on the site can share a nickname with another; when the automatic
# line match is ambiguous the page id pins which sentence describes this row.
PAGE_OVERRIDE: dict[str, set[str]] = {
    # Zo of ZoLand is Lorenzo McKeithen (page 1226), not the GD "Zo Pound" (page 4046).
    "b8834e98-34fc-495f-b037-b5322347380b": {"1226"},
}

broken = q(
    f"""SELECT m.id, m.nickname, m.legal_name, m.aliases,
               (SELECT json_agg(s.name) FROM member_set ms JOIN sets s ON s.id=ms.set_id
                 WHERE ms.member_id=m.id) AS sets
        FROM member m WHERE m.universe_id='{CHICAGO}' AND jsonb_typeof(m.aliases)='array'
          AND EXISTS (SELECT 1 FROM jsonb_array_elements_text(m.aliases) a
                      WHERE a ~ '[«»“”„"]' OR length(a) > 40)"""
)
# Nicknames stored as the whole 'Firstname “Nick” Lastname' string.
quoted = q(
    f"""SELECT m.id, m.nickname, m.legal_name FROM member m
        WHERE m.universe_id='{CHICAGO}' AND m.nickname ~ '[«»“”„"]'"""
)
owner = json.loads((ROOT / "tools/wp-owner.json").read_text())
pages = [
    p
    for p in json.loads((ROOT / "raw/pages.json").read_text())
    if owner.get(p["slug"]) == "chicago"
]

# Every parsed member sentence on the Chicago pages, keyed by the names it names.
sentences = []
for p in pages:
    for line in lines_of(p):
        m = parse_member(line)
        if m["name"] and (m["aliases"] or m["legal"]):
            sentences.append((str(p["ID"]), p["title"], m))

plan = []
for row in broken:
    keys = {norm(row["nickname"])}
    hits = [
        (pid, title, m)
        for pid, title, m in sentences
        if keys & ({norm(m["name"])} | {norm(a) for a in m["aliases"]})
    ]
    if row["id"] in PAGE_OVERRIDE:
        hits = [h for h in hits if h[0] in PAGE_OVERRIDE[row["id"]]]
    aliases, legal, seen = [], row["legal_name"], {norm(row["nickname"])}
    for _pid, _title, m in hits:
        for a in [m["name"], *m["aliases"]]:
            if norm(a) not in seen:
                aliases.append(a)
                seen.add(norm(a))
        legal = legal or m["legal"]
    plan.append((row, aliases, legal, hits))

for row, aliases, legal, hits in plan:
    print(f"\n{row['nickname']}  sets={row['sets']}  id={row['id']}")
    for pid, title, m in hits:
        print(
            f"   src p{pid} [{title}]: name={m['name']!r} legal={m['legal']!r} aliases={m['aliases']}"
        )
    print(f"   aliases: {row['aliases']}  ->  {aliases}")
    print(f"   legal  : {row['legal_name']!r}  ->  {legal!r}")

renames = []
for row in quoted:
    emb = EMBEDDED_NICK.match(row["nickname"].strip())
    if not emb:
        print(f"\n{row['nickname']!r}: quoted nickname I cannot split, left alone")
        continue
    nicks = ALIAS.findall(emb.group("nicks"))
    legal = " ".join(x for x in (emb.group("first"), emb.group("last")) if x)
    renames.append((row, nicks[0], legal, nicks[1:]))
    print(f"\n{row['nickname']!r}  ->  nickname={nicks[0]!r} legal={legal!r} aliases={nicks[1:]}")

if "--go" not in sys.argv:
    print(f"\n{len(plan)} alias rows, {len(renames)} renames. DRY RUN - re-run with --go to apply")
    sys.exit()

api = Api()
done = 0
for row, aliases, legal, _ in plan:
    body = {"aliases": aliases}
    if legal and legal != row["legal_name"]:
        body["legal_name"] = legal
    r = api.call("PATCH", f"members/{row['id']}?universe_id={CHICAGO}", body)
    if r and r.get("_error"):
        print("  PATCH failed:", row["nickname"], r)
    else:
        done += 1
for row, nick, legal, aliases in renames:
    body = {"nickname": nick, "legal_name": legal or row["legal_name"]}
    if aliases:
        body["aliases"] = aliases
    r = api.call("PATCH", f"members/{row['id']}?universe_id={CHICAGO}", body)
    if r and r.get("_error"):
        print("  rename failed:", row["nickname"], r)
    else:
        done += 1
print(f"patched {done}/{len(plan) + len(renames)}")
