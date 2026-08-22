"""Create the Chicago members the database is missing, without wiping anything.

`reseed_chicago_members.py` deletes every member and rebuilds from the
extraction. That was fine on a virgin universe and is now destructive: it would
throw away the merges, the family links, the hand-written biographies and the
incident participations that hang off the surviving rows.

This is the idempotent replacement. It resolves every person in the corrected
extraction against the database by nickname *or alias*, narrowed by set, and
POSTs only the ones that are genuinely absent. It never deletes and never
rewrites an existing row, so it is safe to re-run after any parser fix.

Resolving on aliases is what keeps it from re-creating the duplicates that were
merged by hand: "Brick" now lives as an alias of FBG Brick, so the extraction's
bare "Brick" record matches the merged row instead of spawning a new one.

Dry-run by default; --go creates.
"""

import collections
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import extract_members_full as E  # noqa: E402
from db_sync import candidates, norm  # noqa: E402
from wikiapi import CHICAGO, Api, q  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
NATMAP = {
    "Gangster Disciple": "Gangster Disciples",
    "Black Disciple": "Black Disciples",
    "Black P.Stone": "Black P. Stones",
    "Mickey Cobra": "Mickey Cobras",
    "Vice Lord": "Vice Lords",
    "Four Corner Hustler": "4 Corner Hustlers",
    "Latin King": "Latin Kings",
}
# Roster lines that name a crew, not a person.
NOT_A_PERSON = re.compile(r"^(les|le|la)\s+\w|gang$|boyz$|squad$", re.I)


def clean_name(raw):
    """Split a roster-style name into (display name, aliases).

    The site writes 'Jarvis « Jaro »' and 'Scarface ou Trigga' in roster lines,
    which never pass through parse_member, so the quoting survives into the
    record. Neither form should become a member nickname verbatim.
    """
    raw = re.split(r"\s*(?:->|→|,)\s*", raw, maxsplit=1)[0]
    aliases = [a.strip() for a in re.findall(r"[«»\"“”]\s*([^«»\"“”]+?)\s*[«»\"“”]", raw)]
    name = re.sub(r"[«»\"“”][^«»\"“”]*[«»\"“”]", "", raw).strip(" ,.-")
    parts = re.split(r"\s+ou\s+", name, maxsplit=1)
    if len(parts) == 2 and all(p.strip() for p in parts):
        name, extra = parts[0].strip(), parts[1].strip()
        if extra and norm(extra) not in {norm(a) for a in aliases}:
            aliases.append(extra)
    return name, [a for a in aliases if a and norm(a) != norm(name)]


members = q(
    f"""SELECT m.id, m.nickname, coalesce(m.aliases,'[]'::jsonb) aliases,
               coalesce((SELECT json_agg(ms.set_id::text) FROM member_set ms
                         WHERE ms.member_id=m.id),'[]') set_ids
        FROM member m WHERE m.universe_id='{CHICAGO}'"""
)
by_id = {m["id"]: m for m in members}
name_idx = collections.defaultdict(set)
for m in members:
    for n in [m["nickname"], *(m["aliases"] or [])]:
        if n and norm(n):
            name_idx[norm(n)].add(m["id"])

setidx, set_gang = {}, {}
for r in q(
    f"""SELECT id, name, gang_id::text gid, coalesce(name_variants,'[]'::jsonb) nv
        FROM sets WHERE universe_id='{CHICAGO}'"""
):
    set_gang[r["id"]] = r["gid"]
    for k in candidates(r["name"]):
        setidx.setdefault(k, r["id"])
    for v in r["nv"] or []:
        # A variant carries three slots: the acronym lives in `initials` and the
        # set number in `number`, so indexing only `name` loses "SKD" and "078".
        for slot in ("name", "initials", "number"):
            for k in candidates(v.get(slot) or ""):
                setidx.setdefault(k, r["id"])
alias_map = json.loads((ROOT / "tools/alias-map.json").read_text())["alias"]
gangs = {g["name"]: g["id"] for g in q(f"SELECT id, name FROM gang WHERE universe_id='{CHICAGO}'")}


def resolve_set(title):
    """Source set name -> DB set id, or None."""
    if not title:
        return None
    t = title.replace("×", "x").replace("’", "'").strip()
    # Longest key first: candidates() is an unordered set, and a parenthetical title
    # yields BOTH "loccityboty" and the bare "loccity". Taking whichever came out of
    # the set first sends "LOC CITY (BotY)" to either row at random.
    for k in sorted(candidates(t), key=len, reverse=True):
        if k in setidx:
            return setidx[k]
    canon = next(
        (alias_map[k] for k in sorted(candidates(t), key=len, reverse=True) if k in alias_map), None
    )
    if canon:
        for k in sorted(candidates(canon), key=len, reverse=True):
            if k in setidx:
                return setidx[k]
    return None


people, _events = E.extract()
people = E.dedupe(people)

create, review, skipped = [], [], collections.Counter()
for p in people:
    name, extra_aliases = clean_name(p["name"])
    if not E.good_name(name) or NOT_A_PERSON.match(name):
        skipped["nom inutilisable"] += 1
        continue
    sid = resolve_set(p["set"]) if p["set"] else None
    keys = {norm(name), *(norm(a) for a in [*extra_aliases, *p["aliases"]] if a)}
    cands = {c for k in keys if k for c in name_idx.get(k, ())}
    if not sid:
        if cands:
            skipped["deja present (sans set a verifier)"] += 1
        else:
            skipped["set non resolu et nom inconnu"] += 1
        continue
    if any(sid in by_id[c]["set_ids"] for c in cands):
        skipped["deja present"] += 1
        continue
    row = (p, name, sorted({*extra_aliases, *p["aliases"]}), sid)
    # Conservative: create only when the universe holds no row of that name at all.
    # A name that already exists on another set is exactly the shape that produced
    # the tag-prefix duplicates, so it is reported for adjudication, never created.
    (create if not cands else review).append(row)

print(f"personnes extraites : {len(people)}")
print(f"deja en base        : {sum(skipped.values())}  {dict(skipped)}")
print(f"a creer             : {len(create)}\n")
sets_by_id = {
    r["id"]: r["name"] for r in q(f"SELECT id, name FROM sets WHERE universe_id='{CHICAGO}'")
}
for p, name, aliases, sid in create:
    print(
        f"   {name!r:24} set={sets_by_id.get(sid)!r:22} aliases={aliases} "
        f"dead={p['dead']} locked={p['locked']} pages={p['pages'][:2]}"
    )

print(f"\na verifier a la main ({len(review)}) - nom deja porte par une fiche sur un autre set,")
print("donc potentiellement le meme homme; rien n'est cree pour eux:")
for p, name, _aliases, sid in review:
    other = sorted(
        f"{by_id[c]['nickname']}@{'/'.join(sets_by_id.get(x, '?') for x in by_id[c]['set_ids']) or '-'}"
        for k in {norm(name)}
        for c in name_idx.get(k, ())
    )
    print(f"   {name!r:22} -> {sets_by_id.get(sid)!r:18} deja: {other[:4]}  pages={p['pages'][:2]}")

if "--go" not in sys.argv:
    print("\nDRY RUN - relancez avec --go")
    sys.exit()

api = Api()
made = err = 0
for p, name, aliases, sid in create:
    body = {
        "universe_id": CHICAGO,
        "nickname": name,
        "nickname_unknown": False,
        "status": "DEAD" if p["dead"] else "LOCKED" if p["locked"] else "UNKNOWN",
        "biography": "",
        "affiliations": [{"set_id": sid, "is_primary": True}],
    }
    if aliases:
        body["aliases"] = aliases
    gid = gangs.get(NATMAP.get(p["nation"], p["nation"] or "")) or set_gang.get(sid)
    if gid:
        body["gang_id"] = gid
    r = api.call("POST", f"members/?universe_id={CHICAGO}", body)
    if r and r.get("_error"):
        err += 1
        print(f"  echec {name!r}: {r['_error']} {r.get('_body', '')[:90]}")
    else:
        made += 1
print(f"\ncrees {made}, echecs {err}")
