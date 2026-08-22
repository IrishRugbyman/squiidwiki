"""Merge hand-adjudicated duplicate members, carrying everything the row owns.

`apply_dedupe.py` (the 74-merge agent pass) merges names, aliases, sets and gang
onto the keeper and then DELETEs the absorbed row - but `delete_member` drops
that row's incident participations outright, and nothing repoints the family
links other members hold to the absorbed id. This script closes both gaps:
incidents move first, family references are rewritten on every member that
holds them, and only then is the row deleted.

Pairs are adjudicated BY HAND, with the source line that settles it recorded in
`why`. Nothing here is inferred at runtime: an automatic rule is what produced
these duplicates in the first place.

Dry-run by default; --go applies. `--pair KEY` restricts to one pair.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from db_sync import norm  # noqa: E402
from wikiapi import CHICAGO, Api, q  # noqa: E402

# Weakest to strongest: a merged row keeps the most specific status known.
STATUS_RANK = {"UNKNOWN": 0, "FREE": 1, "ESCAPEE": 2, "ABSCONDER": 3, "LOCKED": 4, "DEAD": 5}
# Same idea for a participant row that exists on both sides of a merge.
ROLE_RANK = {"BYSTANDER": 0, "VICTIM": 1, "ASSISTED": 2, "SHOOTER": 3}
OUTCOME_RANK = {"UNKNOWN": 0, "UNHARMED": 1, "INJURED": 2, "KILLED": 3}

PAIRS = [
    {
        "key": "kts-von",
        "keep": "fbb1a335-dd48-428f-92a3-a92a028fcb5f",  # KTS Von, KTS, DEAD
        "absorb": "14dbd168-d36d-4892-bb89-2b17a64726dc",  # Von, KTS, DEAD
        "add_aliases": ["Big Kutthroat Da Smoker"],
        # One man, one killing: the NLMB page credits MaddMaxx (+ EBK Juvie
        # assisting) under "KTS Von" and Choppa under "Von", so the seed built
        # two murders. Fold Choppa's claim into the murder the keeper carries.
        "fold_incidents": [
            ("d052d6a7-184b-4f56-a144-f61a4dc46397", "810c65ad-f1aa-4ebd-9d63-eb2bf38a282b")
        ],
        "why": (
            "Page 7491 (KTS): 'KTS Von aussi connu sous le nom de « Big Kutthroat Da Smoker » "
            "etait un Gangster Disciple. Il est decede. Il etait le frere de Dre et Vinnie et le "
            "cousin de Zeko' - and both Dre's and Vinnie's own sentences on the same page say "
            "'le frere de ... Von du meme set'. Same set, same brothers, same cousin, both DEAD. "
            "The dedupe agent never compared them: it groups candidates by normalised nickname, "
            "so 'ktsvon' and 'von' landed in different buckets."
        ),
    },
    {
        "key": "lil-durk",
        "keep": "d4459f34-93e9-412e-ab5a-4e23ad737d96",  # Lil Durk, Lamron, 3 incidents
        "absorb": "5e49ba8b-4539-44af-a6d3-9fb8b8b0a114",  # Lil Durk, OTF, empty row
        "primary_set": "Lamron",
        "why": (
            "Page 7489 (LAMRON): 'Lil Durk ou «Durkiooooooooo» est un Black Disciple. Il est le "
            "fils de Big Durk de Central City' - his set. Page 4333 (OTF) is a bare roster line "
            "'Lil Durk': OTF is his own label (Only The Family), not a rival set, and page 6537 "
            "has him and D-Thang out of the Doggpound with cousin 'OTF Nuski'. One man on two "
            "rosters. The dedupe agent read the empty OTF row's lack of events as evidence of a "
            "second person ('likely the real rapper's roster listing')."
        ),
    },
]


def member(mid):
    """Full row for one member, or None."""
    rows = q(
        f"""SELECT m.id, m.nickname, m.legal_name, m.status, m.biography,
                   coalesce(m.aliases,'[]'::jsonb) aliases, m.family, m.gang_id::text gid,
                   m.alliance_id::text aid, m.dob, m.date_of_death, m.social_media,
                   m.death_incident_id::text death_incident_id,
                   coalesce((SELECT json_agg(json_build_object('set_id', ms.set_id::text,
                             'name', s.name, 'is_primary', ms.is_primary, 'rank', ms.rank,
                             'from_date', ms.from_date, 'until_date', ms.until_date))
                     FROM member_set ms JOIN sets s ON s.id=ms.set_id
                     WHERE ms.member_id=m.id),'[]') affiliations
            FROM member m WHERE m.id='{mid}' AND m.universe_id='{CHICAGO}'"""
    )
    return rows[0] if rows else None


def incidents_of(mid):
    """Every incident this member participates in, with the full participant list."""
    return q(
        f"""SELECT i.id, i.type, ip.role, ip.outcome, ip.acquitted, ip.notes,
                   (SELECT json_agg(json_build_object('member_id', ip2.member_id::text,
                            'nickname', m2.nickname, 'role', ip2.role, 'outcome', ip2.outcome,
                            'acquitted', ip2.acquitted, 'notes', ip2.notes))
                    FROM incident_participant ip2 JOIN member m2 ON m2.id=ip2.member_id
                    WHERE ip2.incident_id=i.id) participants
            FROM incident_participant ip JOIN incident i ON i.id=ip.incident_id
            WHERE ip.member_id='{mid}'"""
    )


def holders_of(mid):
    """Members whose family JSONB references this id."""
    return q(
        f"""SELECT m.id, m.nickname, m.family FROM member m
            WHERE m.universe_id='{CHICAGO}' AND m.family::text LIKE '%{mid}%'"""
    )


def repoint(family, old, new):
    """Rewrite one id inside a family dict; drop it if `new` is None or self."""
    out = {}
    for key, val in (family or {}).items():
        ids = val if isinstance(val, list) else [val]
        fixed = []
        for i in ids:
            i = new if i == old else i
            if i and i != new or i == new:
                fixed.append(i)
        fixed = [i for i in dict.fromkeys(fixed) if i and i != old]
        if not fixed:
            continue
        out[key] = fixed[0] if key == "father" else sorted(set(fixed))
    return out


def merge_participants(rows, old, new):
    """Participant list with `old` rewritten to `new`, strongest row winning on collision."""
    best = {}
    for p in rows:
        mid = new if p["member_id"] == old else p["member_id"]
        prev = best.get(mid)
        if prev is None or (ROLE_RANK.get(p["role"], 0), OUTCOME_RANK.get(p["outcome"], 0)) > (
            ROLE_RANK.get(prev["role"], 0),
            OUTCOME_RANK.get(prev["outcome"], 0),
        ):
            best[mid] = {**p, "member_id": mid}
    return [
        {
            "member_id": p["member_id"],
            "role": p["role"],
            "outcome": p["outcome"],
            "acquitted": p.get("acquitted", False),
            "notes": p.get("notes"),
            "nickname": p.get("nickname"),  # display only; stripped before sending
        }
        for p in best.values()
    ]


def payload(participants):
    """Participant rows as the API takes them (nickname is a local display field)."""
    return [{k: v for k, v in p.items() if k != "nickname"} for p in participants]


def plan_one(pair):
    """Everything that has to change for one pair, resolved against the live DB."""
    keep, absorb = member(pair["keep"]), member(pair["absorb"])
    if not keep or not absorb:
        return None, f"missing row (keep={bool(keep)}, absorb={bool(absorb)})"

    folds = []
    folded_away = set()
    for src_id, dst_id in pair.get("fold_incidents", []):
        src = q(
            f"""SELECT json_agg(json_build_object('member_id', ip.member_id::text,
                       'nickname', m.nickname, 'role', ip.role, 'outcome', ip.outcome,
                       'acquitted', ip.acquitted, 'notes', ip.notes)) p
                FROM incident_participant ip JOIN member m ON m.id=ip.member_id
                WHERE ip.incident_id='{src_id}'"""
        )[0]["p"]
        dst = q(
            f"""SELECT json_agg(json_build_object('member_id', ip.member_id::text,
                       'nickname', m.nickname, 'role', ip.role, 'outcome', ip.outcome,
                       'acquitted', ip.acquitted, 'notes', ip.notes)) p
                FROM incident_participant ip JOIN member m ON m.id=ip.member_id
                WHERE ip.incident_id='{dst_id}'"""
        )[0]["p"]
        merged = merge_participants((src or []) + (dst or []), pair["absorb"], pair["keep"])
        folds.append({"src": src_id, "dst": dst_id, "participants": merged})
        folded_away.add(src_id)

    moves = []
    for inc in incidents_of(pair["absorb"]):
        if inc["id"] in folded_away:
            continue
        moves.append(
            {
                "incident": inc["id"],
                "type": inc["type"],
                "participants": merge_participants(
                    inc["participants"], pair["absorb"], pair["keep"]
                ),
            }
        )

    # Family: union both sides, then rewrite everyone else's reference.
    merged_family = repoint(keep["family"], pair["absorb"], pair["keep"])
    for key, val in (absorb["family"] or {}).items():
        ids = val if isinstance(val, list) else [val]
        cur = merged_family.get(key)
        cur = cur if isinstance(cur, list) else [cur] if cur else []
        allids = [i for i in dict.fromkeys([*cur, *ids]) if i not in (pair["absorb"], pair["keep"])]
        if allids:
            merged_family[key] = allids[0] if key == "father" else sorted(set(allids))
    rewrites = []
    for h in holders_of(pair["absorb"]):
        if h["id"] in (pair["keep"], pair["absorb"]):
            continue
        new = repoint(h["family"], pair["absorb"], pair["keep"])
        if new != h["family"]:
            rewrites.append({"id": h["id"], "nickname": h["nickname"], "family": new})

    # Scalars: keeper wins, absorbed fills blanks.
    aliases, seen = [], {norm(keep["nickname"] or "")}
    for a in [
        *(keep["aliases"] or []),
        absorb["nickname"],
        *(absorb["aliases"] or []),
        *pair.get("add_aliases", []),
    ]:
        if a and norm(a) not in seen and len(a) <= 40:
            aliases.append(a)
            seen.add(norm(a))
    by_set = {}
    for a in [*keep["affiliations"], *absorb["affiliations"]]:
        by_set.setdefault(a["set_id"], a)
    primary = pair.get("primary_set")
    primary_id = next(
        (sid for sid, a in by_set.items() if primary and norm(a["name"]) == norm(primary)),
        next(
            (a["set_id"] for a in keep["affiliations"] if a["is_primary"]),
            next(iter(by_set), None),
        ),
    )
    body = {
        "status": max([keep["status"], absorb["status"]], key=lambda s: STATUS_RANK.get(s, 0)),
        "aliases": aliases,
        "family": merged_family or None,
        "affiliations": [
            {
                "set_id": sid,
                "is_primary": sid == primary_id,
                "rank": a.get("rank"),
                "from_date": a.get("from_date"),
            }
            for sid, a in by_set.items()
        ],
    }
    for field, src in (("gang_id", "gid"), ("alliance_id", "aid")):
        val = keep[src] or absorb[src]
        if val:
            body[field] = val
    for field in ("legal_name", "dob", "date_of_death", "social_media"):
        val = keep[field] or absorb[field]
        if val:
            body[field] = val
    bio = keep["biography"] or absorb["biography"] or ""
    if bio and bio != keep["biography"]:
        body["biography"] = bio
    return {
        "pair": pair,
        "keep": keep,
        "absorb": absorb,
        "folds": folds,
        "moves": moves,
        "rewrites": rewrites,
        "body": body,
    }, None


def describe(plan):
    """Print one pair's plan in full."""
    p, keep, absorb = plan["pair"], plan["keep"], plan["absorb"]
    ksets = "/".join(a["name"] for a in keep["affiliations"]) or "-"
    asets = "/".join(a["name"] for a in absorb["affiliations"]) or "-"
    print(f"\n=== {p['key']}")
    print(f"  keep   {keep['nickname']!r} [{ksets}] {keep['status']} {keep['id']}")
    print(f"  absorb {absorb['nickname']!r} [{asets}] {absorb['status']} {absorb['id']}")
    print(f"  why    {p['why']}")
    for f in plan["folds"]:
        who = ", ".join(f"{x['nickname']}:{x['role']}" for x in f["participants"])
        print(f"  fold   incident {f['src'][:8]} -> {f['dst'][:8]}  ({who})")
    for m in plan["moves"]:
        who = ", ".join(f"{x['nickname']}:{x['role']}" for x in m["participants"])
        print(f"  move   {m['type']} {m['incident'][:8]} -> keeper  ({who})")
    for r in plan["rewrites"]:
        print(f"  family {r['nickname']}: repoint to keeper -> {json.dumps(r['family'])}")
    print(f"  keeper aliases   -> {plan['body']['aliases']}")
    print(
        f"  keeper sets      -> {[a['name'] for a in plan['keep']['affiliations']]}"
        f" + {[a['name'] for a in plan['absorb']['affiliations']]}"
    )
    print(f"  keeper family    -> {json.dumps(plan['body']['family'])}")
    print(f"  keeper status    -> {plan['body']['status']}")


def apply(plan, api):
    """Execute one plan: incidents, then family, then the keeper, then the delete."""
    p = plan["pair"]
    for f in plan["folds"]:
        r = api.call(
            "PATCH",
            f"incidents/{f['dst']}?universe_id={CHICAGO}",
            {"participants": payload(f["participants"])},
        )
        if r and r.get("_error"):
            return f"fold patch failed: {r}"
        r = api.call("DELETE", f"incidents/{f['src']}?universe_id={CHICAGO}")
        if r and r.get("_error"):
            return f"fold delete failed: {r}"
    for m in plan["moves"]:
        r = api.call(
            "PATCH",
            f"incidents/{m['incident']}?universe_id={CHICAGO}",
            {"participants": payload(m["participants"])},
        )
        if r and r.get("_error"):
            return f"incident move failed: {r}"
    for rw in plan["rewrites"]:
        r = api.call(
            "PATCH", f"members/{rw['id']}?universe_id={CHICAGO}", {"family": rw["family"] or None}
        )
        if r and r.get("_error"):
            return f"family rewrite failed on {rw['nickname']}: {r}"
    r = api.call("PATCH", f"members/{p['keep']}?universe_id={CHICAGO}", plan["body"])
    if r and r.get("_error"):
        return f"keeper patch failed: {r}"
    r = api.call("DELETE", f"members/{p['absorb']}?universe_id={CHICAGO}")
    if r and r.get("_error"):
        return f"delete failed: {r}"
    return None


only = None
if "--pair" in sys.argv:
    only = sys.argv[sys.argv.index("--pair") + 1]

plans = []
for pair in PAIRS:
    if only and pair["key"] != only:
        continue
    plan, err = plan_one(pair)
    if err:
        print(f"=== {pair['key']}: SKIP - {err}")
        continue
    describe(plan)
    plans.append(plan)

if "--go" not in sys.argv:
    print(f"\n{len(plans)} pairs planned. DRY RUN - re-run with --go to apply")
    sys.exit()

api = Api()
done = 0
for plan in plans:
    err = apply(plan, api)
    if err:
        print(f"\n{plan['pair']['key']}: {err}")
    else:
        done += 1
        print(f"\n{plan['pair']['key']}: merged")
print(f"\n{done}/{len(plans)} pairs merged")
