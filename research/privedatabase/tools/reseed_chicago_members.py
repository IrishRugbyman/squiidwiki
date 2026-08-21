"""Wipe and re-seed every Chicago member from the full extraction."""

import collections
import json
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

sys.path.insert(0, "/home/lbzgiu/squiidwiki/research/privedatabase/tools")
from db_sync import candidates, norm

API = "http://localhost:8001/api/v1"
U = "59d23911-6fee-4156-8839-ac3c248a3b46"
MUNI = "0d73ae53-037c-450f-8aca-6fee9d08492e"
S = pathlib.Path(
    "/tmp/claude-1000/-home-lbzgiu-squiidwiki/e162f253-b7e6-408b-a995-a5bb3bb9c68d/scratchpad"
)
R = pathlib.Path("/home/lbzgiu/squiidwiki/research/privedatabase")
H = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {(S / 'tok').read_text().strip()}",
}
NATMAP = {
    "Gangster Disciple": "Gangster Disciples",
    "Black Disciple": "Black Disciples",
    "Black P.Stone": "Black P. Stones",
    "Mickey Cobra": "Mickey Cobras",
    "Vice Lord": "Vice Lords",
    "Four Corner Hustler": "4 Corner Hustlers",
    "Latin King": "Latin Kings",
    "Mickey Cobras": "Mickey Cobras",
    "Black Disciples": "Black Disciples",
    "Latin Kings": "Latin Kings",
}


def q(sql):
    """Run a query against squiidwiki_prod and return rows as JSON."""
    return json.loads(
        subprocess.run(
            [
                "psql",
                "-d",
                "squiidwiki_prod",
                "-t",
                "-A",
                "-c",
                f"SELECT coalesce(json_agg(t),'[]') FROM ({sql}) t;",
            ],
            capture_output=True,
            text=True,
        ).stdout
    )


def call(method, path, payload=None):
    """Call the API; return the JSON body, or {"_error": code} on an HTTP error."""
    r = urllib.request.Request(
        f"{API}/{path}",
        method=method,
        data=json.dumps(payload).encode() if payload else None,
        headers=H,
    )
    try:
        with urllib.request.urlopen(r, timeout=30) as x:
            raw = x.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read()[:140].decode(errors="replace")}


def clean_title(t):
    """Normalise unicode lookalikes the site mixes in (multiplication sign, curly quote)."""
    return (t or "").replace("\u00d7", "x").replace("\u2019", "'").strip()


people = json.loads((R / "tools/extract-chicago-people.json").read_text())
am = json.loads((R / "tools/alias-map.json").read_text())["alias"]
gangs = {g["name"]: g["id"] for g in q(f"SELECT id,name FROM gang WHERE universe_id='{U}'")}


def build_set_index():
    """Index every DB set by all its name candidates; also map set id -> gang id."""
    idx, gang_of = {}, {}
    for r in q(
        f"SELECT id,name,gang_id::text AS gid,coalesce(name_variants,'[]'::jsonb) nv "
        f"FROM sets WHERE universe_id='{U}'"
    ):
        gang_of[r["id"]] = r["gid"]
        for k in candidates(r["name"]):
            idx.setdefault(k, r["id"])
        for v in r["nv"] or []:
            for k in candidates(v.get("name", "")):
                idx.setdefault(k, r["id"])
    return idx, gang_of


setidx, set_gang = build_set_index()
alliances = {}
for a in q(f"SELECT id,name FROM alliance WHERE universe_id='{U}'"):
    for k in candidates(a["name"]):
        alliances.setdefault(k, a["id"])


def resolve_set(title):
    """Return ('set', id) / ('alliance', id) / None for a source set name."""
    title = clean_title(title)
    if not title:
        return None
    for k in candidates(title):
        if k in setidx:
            return ("set", setidx[k])
    for k in candidates(title):
        if k in alliances:
            return ("alliance", alliances[k])
    canon = next((am[k] for k in candidates(title) if k in am), None)
    if canon:
        for k in candidates(canon):
            if k in setidx:
                return ("set", setidx[k])
    # unique prefix onto an existing set (min 4 chars): Killaward -> Killaward 078
    n = norm(title)
    if len(n) >= 4:
        pre = {sid for k, sid in setidx.items() if k.startswith(n)}
        if len(pre) == 1:
            return ("set", pre.pop())
    return None


# ---- pass 1: which set names have people but no DB set?
missing = collections.Counter()
best_case = {}
for p in people:
    t = clean_title(p["set"])
    if t and not resolve_set(t):
        missing[norm(t)] += 1
        cur = best_case.get(norm(t), "")
        if (t != t.upper() and cur == cur.upper()) or len(t) > len(cur):
            best_case[norm(t)] = t
missing_named = [(best_case[k], c) for k, c in sorted(missing.items(), key=lambda kv: -kv[1])]
print(
    f"set names with people but no DB set: {len(missing_named)} "
    f"(covering {sum(missing.values())} people)"
)
for name, c in missing_named[:12]:
    print(f"   {c:4}  {name}")

DRY = "--go" not in sys.argv
if DRY:
    # preview final numbers without writing
    merged = {}
    for p in people:
        r = resolve_set(p["set"])
        merged.setdefault((norm(p["name"]), r[1] if r else norm(clean_title(p["set"]))), []).append(
            p
        )
    print(f"\nfinal member records after set-resolution dedupe: {len(merged)}")
    print("DRY RUN - re-run with --go")
    sys.exit()

# ---- create the missing sets (they hold people now, so they earn a record)
made_sets = 0
for name, _c in missing_named:
    body = {
        "universe_id": U,
        "name": name,
        "municipality_id": MUNI,
        "status": "ACTIVE",
        "name_variants": [{"name": name, "is_primary": True}],
    }
    r = call("POST", "sets/", body)
    if r and not r.get("_error"):
        made_sets += 1
    else:
        print("  set create failed:", name, (r or {}).get("_body", "")[:80])
print(f"created {made_sets} sets for previously page-less names")
setidx, set_gang = build_set_index()

# ---- wipe the old members (all of them came from the broken parse)
old = q(f"SELECT id FROM member WHERE universe_id='{U}'")
wiped = 0
for r in old:
    x = call("DELETE", f"members/{r['id']}?universe_id={U}")
    if not (x or {}).get("_error"):
        wiped += 1
print(f"deleted {wiped}/{len(old)} old members")

# ---- merge on (name, resolved set) and seed
merged = {}
for p in people:
    res = resolve_set(p["set"])
    sid = res[1] if res and res[0] == "set" else None
    aid = res[1] if res and res[0] == "alliance" else None
    key = (norm(p["name"]), sid or aid or "")
    r = merged.setdefault(
        key,
        {
            "name": p["name"],
            "set_id": sid,
            "alliance_id": aid,
            "nation": None,
            "dead": False,
            "locked": False,
            "aliases": [],
        },
    )
    if len(p["name"]) > len(r["name"]):
        r["name"] = p["name"]
    r["nation"] = r["nation"] or p["nation"]
    r["dead"] = r["dead"] or p["dead"]
    r["locked"] = r["locked"] or p["locked"]
    for a in p["aliases"]:
        if norm(a) not in {norm(x) for x in r["aliases"]} | {norm(r["name"])}:
            r["aliases"].append(a)

made = err = 0
for r in merged.values():
    gid = gangs.get(NATMAP.get(r["nation"], r["nation"] or "")) or (
        set_gang.get(r["set_id"]) if r["set_id"] else None
    )
    body = {
        "universe_id": U,
        "nickname": r["name"],
        "nickname_unknown": False,
        "status": "DEAD" if r["dead"] else "LOCKED" if r["locked"] else "UNKNOWN",
        "biography": "",
    }
    if gid:
        body["gang_id"] = gid
    if r["aliases"]:
        body["aliases"] = r["aliases"]
    if r["set_id"]:
        body["affiliations"] = [{"set_id": r["set_id"], "is_primary": True}]
    if r.get("alliance_id"):
        body["alliance_id"] = r["alliance_id"]
    x = call("POST", "members/", body)
    if x and x.get("_error"):
        err += 1
        if err <= 3:
            print("  fail:", x["_error"], x["_body"][:100])
    else:
        made += 1
print(f"created {made} members, {err} failed")
