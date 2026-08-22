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
    # --- the tag-prefix family -------------------------------------------------
    # A man written "FBG Brick" on one page and "Brick (STL/EBT)" on another became
    # two rows, and the dedupe agent never compared them: it buckets candidates by
    # normalised nickname, so the tagged and bare forms never met. Its stated test
    # ("no shared events") also cannot fire here - each event names him one way or
    # the other, never both. Every pair below was read back to the source.
    {
        "key": "fbg-brick",
        "keep": "680c7413-51f9-4b37-a45f-141fcde681e6",  # FBG Brick, STL/EBT, DEAD
        "absorb": "b8150455-2f4a-44b5-a976-c477b64e5ed2",  # Brick, STL/EBT, DEAD
        "why": (
            "p7484 (STL/EBT) carries his member sentence: 'FBG Brick, aussi connu sous le nom "
            "de «#30» etait un Black Disciple ... le grand frere de FBG Duck et de Day Day du "
            "meme set'. The bare row is event sightings only, every one tagged '(STL/EBT)', "
            "also DEAD. STL/EBT has one Brick."
        ),
    },
    {
        "key": "fbg-butta",
        "keep": "c2c7260f-2fd5-4dc2-b734-bb11087cb5a1",  # FBG Butta, STL/EBT
        "absorb": "0da04c49-5ebc-4a58-9574-4287ff7ac979",  # Butta, STL/EBT (26 incidents)
        "why": (
            "p7484 (STL/EBT): 'Butta, aussi connu sous le nom de «#26» et de «Tunechi» est un "
            "Gangster Disciple. Il etait tres proche de K.I. du meme set' - the set page's own "
            "sentence for its only Butta. Other pages write him 'FBG Butta (STL/EBT)'. The "
            "other Buttas in the DB are HadiWay and Gotti World, both dead, both untouched."
        ),
    },
    {
        "key": "fbg-cash",
        "keep": "198d4051-3de6-445a-862e-e9ec507ac58e",  # FBG Cash, STL/EBT
        "absorb": "0a7debe1-b6d7-41cd-a9f5-4c2c5ec97ab8",  # Cash, STL/EBT
        "why": (
            "p7484 (STL/EBT): 'FBG Cash est un Gangster Disciple. Il est le frere de FBG Young, "
            "Jiale et Fay Fay du meme set'. p4755 lists 'Cash (STL/EBT)' and 'FBG Cash "
            "(STL/EBT)' on the same page. One Cash on STL/EBT."
        ),
    },
    {
        "key": "fbg-young",
        "keep": "e2abdfd9-eea5-4124-b35e-8e5b9ab546b9",  # FBG Young, STL/EBT
        "absorb": "af45cd85-625f-4f4e-8085-31adfe60e36b",  # Young, STL/EBT
        "why": (
            "p7484 (STL/EBT): 'FBG Young, aussi connu sous le nom de «Mello» et «#1» ... l'un "
            "des deux createurs de la FBG'. The bare row is event sightings tagged '(STL/EBT)'. "
            "The other bare Youngs sit on Hitzsquad and O'Block and are left alone."
        ),
    },
    {
        "key": "fyb-dj",
        "keep": "0d625cdc-85df-42fc-9f11-d451be5575b8",  # FYB DJ, Jaro City
        "absorb": [
            "c350c187-2967-4d54-8c74-4b3bfbeb5987",  # DJ, Jaro City (p243 roster)
            "197ab322-c899-4698-aa0d-7acd2ee483b2",  # 007, Jaro City
        ],
        "why": (
            "Three rows, one man. p7486 (JARO CITY): 'FYB DJ ou «007» est un Gangster Disciple. "
            "Il est le grand frere de LC du Tyquan World', and p7485 has L.C as 'le petit frere "
            "de «007» de Jaro City' - so L.C currently shows two brothers who are the same "
            "person. The bare 'DJ' is the Jaro City roster line on p243. 007 of THF 46 is a "
            "different man and is not touched."
        ),
    },
    {
        "key": "fyb-duke",
        "keep": "3b375456-7e1d-4f25-a277-019f1d5ac354",  # FYB Duke, Jaro City
        "absorb": "77326d98-49c2-4524-9cc5-de08c1b85bb1",  # Duke, Jaro City (p243 roster)
        "why": (
            "The Jaro City roster (p243) lists 'Duke'; kill lists on p4751 and p6277 write the "
            "same man 'FYB Duke (Jaro City)'. The other Dukes (O'Block, No Luv City, MOE, SuWu "
            "Mobb, TYMB, 757, CashCrew) are separate rows and stay separate."
        ),
    },
    {
        "key": "fyb-j-mane",
        "keep": "1aeb8a32-f212-4ede-9147-2f7aa1b221b8",  # FYB J Mane, Jaro City
        "absorb": "ffb993df-2d12-4cb9-920a-c4e67b744041",  # J Mane, Jaro City (p243 roster)
        "why": (
            "p7486 (JARO CITY): 'FYB J Mane est un Insane Black Disciple. Son pere est un Black "
            "Disciple.' The bare row is that same set's roster line on p243, and 'J Mane' "
            "appears nowhere else in the source."
        ),
    },
    {
        "key": "fyb-mattana",
        "keep": "51fbdd9a-fd1f-4d84-8747-f5460970194d",  # FYB Mattana, Jaro City
        "absorb": "1e5b8117-4422-4314-8fbe-197cedead1d6",  # Mattana, Jaro City (p243 roster)
        "why": (
            "p7486 (JARO CITY): 'FYB Mattana est un Gangster Disciple.' The bare row is the "
            "p243 Jaro City roster line. 'Mattana' appears nowhere else."
        ),
    },
    {
        "key": "gbe-capo",
        "keep": "f86800e9-5953-4c89-87bd-3ae987ceaea7",  # GBE Capo, Front$treet, DEAD
        "absorb": "03676f9e-2026-411b-9117-51fa920ac6ff",  # Capo, Front$treet, DEAD
        "why": (
            "p6278 (DIPSET/FRONT$TREET) carries his sentence (alias 'Drama', deceased); p245 "
            "and p7485 write the same dead man 'Capo (Front$treet)'. Front$treet has one Capo. "
            "The Killaward 078 Capo and CapFck12 (whose alias is 'Capo') are different people "
            "and are not touched."
        ),
    },
    {
        "key": "otf-ikey",
        "keep": "0d859402-4960-4cee-ab7d-cf109711c951",  # OTF Ikey, O'Block
        "absorb": "ed98a4ad-0b9a-4c0c-a877-d93f48b67932",  # Ikey, O'Block
        "why": (
            "Both come from the SAME roster, p1151 (O'BLOCK), which is alphabetical: 'Ikey' "
            "sits in the I's and 'OTF Ikey' in the O's - one man entered twice under two "
            "spellings. p6273 gives him his brother: 'Boss Money ... est le grand frere d'Ikey "
            "du meme set'. The Lowelife Ikey is a different man and stays."
        ),
    },
    {
        "key": "otf-pat",
        "keep": "393bd196-51ec-43fc-bb78-954421bbbd18",  # OTF Pat, NLMB
        "absorb": "2d05dbde-1c6a-42e1-8939-a835f077052b",  # Pat, NLMB
        "why": (
            "The same shooting on both sides. p7487 (NLMB): 'OTF Pat, aussi connu sous le nom "
            "de « Project » ... En 2017, FBG Brick tire plus de 15 fois sur Pat'. p7484 "
            "(STL/EBT), under FBG Brick: 'Pat (NLMB, il lui a tire dessus 15 fois mais Pat a "
            "survecu)'. The dead Pats on CCG, Smashville, TaeTown and South End are other men."
        ),
    },
    {
        "key": "otf-tay",
        "keep": "aff26797-82a9-44af-9ac6-4927289ef83c",  # OTF Tay, Lowelife, DEAD
        "absorb": "3fd3432f-c960-4303-88d8-8e478136c9fa",  # Tay, Lowelife, DEAD
        "why": (
            "Both rows come off p6536 (CMB), whose kill list carries 'OTF Tay (Lowelife)' and "
            "'Tay (Lowelife)' two lines apart - the same signature as KTS Von/Von. Decisive: "
            "Lowelife's own body list (p7944) contains exactly one Tay, 'OTF Tay (decede)'."
        ),
    },
    {
        "key": "pbg-spazz",
        "keep": "b7820b49-fef1-4b2f-94b0-76956b720f6e",  # PBG Spazz, PBG/TFG
        "absorb": "89b14ff4-61cc-4c0e-9c9f-dfa0b9c74723",  # Spazz, PBG/TFG (14 incidents, LOCKED)
        "why": (
            "The bare row is the member sentence on p7488, the PBG/TFG set page; the tagged row "
            "is a p7954 kill-list sighting written 'PBG Spazz (PBG)', which resolves to the "
            "same set. There is only one Spazz in the source."
        ),
    },
    {
        "key": "tfg-bigz",
        "keep": "147942f8-85e3-41d3-ab7c-9fdc78be00a2",  # TFG Bigz, PBG/TFG
        "absorb": "15be567c-6e81-4885-b4f5-797de20efb1d",  # Bigz, PBG/TFG (LOCKED)
        "why": (
            "The two rows already carry the SAME brother in the database, which only happens "
            "when one man was split. The bare row is the p7488 PBG/TFG member sentence; the "
            "tagged row is the p7955/p7954 sightings written 'TFG Bigz (TFG)'."
        ),
    },
    {
        "key": "abm-tay",
        "keep": "20dd6b68-af73-4137-8865-093b7e22d6df",  # ABM Tay, Jaro City
        "absorb": "b3139233-3c59-47ff-97a2-7d8031ef153a",  # Tay, Jaro City, DEAD
        "why": (
            "Neither Jaro City page names a bare 'Tay' - the p243 roster has none - so the bare "
            "row's Jaro City affiliation is a set-resolution artifact of the p7908 kill-list "
            "entry 'Tay (ABM)'. The only Tay the source ties to either ABM or Jaro City is the "
            "man written 'ABM Tay (Jaro City)' on p1194 and p6273. Same man, and the source "
            "contradicts itself on his set (ABM vs Jaro City); Jaro City is kept as the two "
            "sightings that name a set agree on it."
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


def absorb_ids(pair):
    """The absorbed ids as a list; `absorb` takes a single id or several."""
    a = pair["absorb"]
    return [a] if isinstance(a, str) else list(a)


def plan_one(pair):
    """Everything that has to change for one pair, resolved against the live DB."""
    keep = member(pair["keep"])
    absorbed = [(aid, member(aid)) for aid in absorb_ids(pair)]
    missing = [aid for aid, row in absorbed if not row]
    if not keep or missing:
        return None, f"missing row (keep={bool(keep)}, absorbed missing={missing})"
    absorbs = [row for _, row in absorbed]

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
        merged = (src or []) + (dst or [])
        for aid in absorb_ids(pair):
            merged = merge_participants(merged, aid, pair["keep"])
        folds.append({"src": src_id, "dst": dst_id, "participants": merged})
        folded_away.add(src_id)

    moves, seen_inc = [], set()
    for aid in absorb_ids(pair):
        for inc in incidents_of(aid):
            if inc["id"] in folded_away or inc["id"] in seen_inc:
                continue
            seen_inc.add(inc["id"])
            rows = inc["participants"]
            for other in absorb_ids(pair):
                rows = merge_participants(rows, other, pair["keep"])
            moves.append({"incident": inc["id"], "type": inc["type"], "participants": rows})

    # Family: union both sides, then rewrite everyone else's reference.
    gone = set(absorb_ids(pair)) | {pair["keep"]}
    merged_family = keep["family"] or {}
    for aid in absorb_ids(pair):
        merged_family = repoint(merged_family, aid, pair["keep"])
    for row in absorbs:
        for key, val in (row["family"] or {}).items():
            ids = val if isinstance(val, list) else [val]
            cur = merged_family.get(key)
            cur = cur if isinstance(cur, list) else [cur] if cur else []
            allids = [i for i in dict.fromkeys([*cur, *ids]) if i not in gone]
            if allids:
                merged_family[key] = allids[0] if key == "father" else sorted(set(allids))
    rewrites = {}
    for aid in absorb_ids(pair):
        for h in holders_of(aid):
            if h["id"] in gone:
                continue
            base = rewrites.get(h["id"], {}).get("family", h["family"])
            new = repoint(base, aid, pair["keep"])
            if new != h["family"]:
                rewrites[h["id"]] = {"id": h["id"], "nickname": h["nickname"], "family": new}
    rewrites = list(rewrites.values())

    # Scalars: keeper wins, absorbed fills blanks.
    aliases, seen = [], {norm(keep["nickname"] or "")}
    candidates = list(keep["aliases"] or [])
    for row in absorbs:
        candidates += [row["nickname"], *(row["aliases"] or [])]
    for a in [*candidates, *pair.get("add_aliases", [])]:
        if a and norm(a) not in seen and len(a) <= 40:
            aliases.append(a)
            seen.add(norm(a))
    by_set = {}
    for a in [*keep["affiliations"], *(x for row in absorbs for x in row["affiliations"])]:
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
        "status": max(
            [keep["status"], *(r["status"] for r in absorbs)],
            key=lambda s: STATUS_RANK.get(s, 0),
        ),
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
        val = keep[src] or next((r[src] for r in absorbs if r[src]), None)
        if val:
            body[field] = val
    for field in ("legal_name", "dob", "date_of_death", "social_media"):
        val = keep[field] or next((r[field] for r in absorbs if r[field]), None)
        if val:
            body[field] = val
    bio = keep["biography"] or next((r["biography"] for r in absorbs if r["biography"]), "")
    if bio and bio != keep["biography"]:
        body["biography"] = bio
    return {
        "pair": pair,
        "keep": keep,
        "absorbs": absorbs,
        "folds": folds,
        "moves": moves,
        "rewrites": rewrites,
        "body": body,
    }, None


def body_sets(plan):
    """Distinct affiliations the keeper ends up with."""
    seen, out = set(), []
    for a in [
        *plan["keep"]["affiliations"],
        *(x for r in plan["absorbs"] for x in r["affiliations"]),
    ]:
        if a["set_id"] not in seen:
            seen.add(a["set_id"])
            out.append(a)
    return out


def describe(plan):
    """Print one pair's plan in full."""
    p, keep = plan["pair"], plan["keep"]
    ksets = "/".join(a["name"] for a in keep["affiliations"]) or "-"
    print(f"\n=== {p['key']}")
    print(f"  keep   {keep['nickname']!r} [{ksets}] {keep['status']} {keep['id']}")
    for row in plan["absorbs"]:
        rsets = "/".join(a["name"] for a in row["affiliations"]) or "-"
        print(f"  absorb {row['nickname']!r} [{rsets}] {row['status']} {row['id']}")
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
    print(f"  keeper sets      -> {[a['name'] for a in body_sets(plan)]}")
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
    for aid in absorb_ids(p):
        r = api.call("DELETE", f"members/{aid}?universe_id={CHICAGO}")
        if r and r.get("_error"):
            return f"delete failed on {aid}: {r}"
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
