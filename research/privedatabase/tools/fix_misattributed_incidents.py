"""Repair incidents credited to the wrong member by the block-leak parse bug.

On a set page the extractor attributes each CORPS / ASSISTANCE / FUSILLADES
block to the member sentence above it. When `parse_member` could not produce a
usable name it left `current` pointing at the PREVIOUS member, who then absorbed
the next man's whole kill list. On page 7488 alone, Gullie Gibson - who has two
bodies on his own fiche - absorbed 75 event lines belonging to Lil $hawn, Lil
Dutty, Kemo and Mosey, whose sentences all read
"<Name> aussi connu sous le nom de «X» est un ..." with no comma before "aussi".

chiparse now parses those sentences. This re-derives the perpetrators for every
affected victim from the corrected extraction and PATCHes only the incidents
whose participant list actually changes. It never creates or deletes an
incident, so hand-made records (the T-Slick murder) and the set-level claims are
untouched.

Dry-run by default; --go applies. --who NAME limits the report to one member.
"""

import collections
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import extract_members_full as E  # noqa: E402
from db_sync import candidates, norm  # noqa: E402
from wikiapi import CHICAGO, Api, q  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
KIND_TYPE = {"bodies": "MURDER", "shootings": "SHOOTING"}

# Men the old parse lost entirely: their own sentence failed, so no member row was
# ever created and their kill list went to whoever preceded them on the page.
# They have to exist before their events can be handed back.
MISSING_MEMBERS = [
    {
        "nickname": "Kemo",
        "set": "PBG/TFG",
        "aliases": ["NotThaBopper"],
        "status": "UNKNOWN",
        "src": "p7488: 'Kemo aussi connu sous le nom de «NotThaBopper» est un Insane Gangster "
        "Disciple de la PBG. Il etait proche de King Shoota de la TFG.'",
    },
    {
        "nickname": "DB",
        "set": "LOC City (Back of the Yards)",
        "aliases": ["Derry"],
        "status": "LOCKED",
        "src": "p7954: 'DB aussi connu sous le nom de «Derry» est un Gangster Disciple. Il est "
        "actuellement incarcere.' Placed on the set his page-mates already sit on.",
    },
    {
        "nickname": "The God Father",
        # No Luv City is an ALLIANCE of Gangster Disciple sets, not a set (p7888).
        "alliance": "No Luv City",
        "aliases": ["LB"],
        "status": "LOCKED",
        "src": "p4183: 'The God Father aussi connu sous le nom de “LB” est un Gangster Disciple. "
        "Il est considere comme un des boss du No Luv City. Il est actuellement incarcere.'",
    },
    {
        "nickname": "No Good Loso",
        "set": "Out7aw City",
        "aliases": [],
        "status": "UNKNOWN",
        "src": "p7949: 'Le rappeur No Good Loso est membre de ce set.' The Losos on GGE, "
        "Lowelife and NLMB are other men.",
    },
]

# Perpetrators whose name is shared and whose event carries no set hint; pinned by
# the page the block sits on.
PERP_OVERRIDES = {
    # p4046 'Zo aussi connu sous le nom de “Zo Pound” ... condamne a 52 ans' = Landlord COV
    ("Zo", "4046"): "978d35fd-9134-49f1-8eca-f3d656f40046",
    # p1772 'Tytus “Tyto” Harris etait un Conservative Vice Lord' - that page's subject
    ("Tyto", "1772"): "4e157d81-f36b-4c45-815a-d5c712cb27bf",
}

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
setidx = {}
for r in q(
    f"SELECT id, name, coalesce(name_variants,'[]'::jsonb) nv FROM sets WHERE universe_id='{CHICAGO}'"
):
    for k in candidates(r["name"]):
        setidx.setdefault(k, r["id"])
    for v in r["nv"] or []:
        # A variant carries three slots: the acronym lives in `initials` and the
        # set number in `number`, so indexing only `name` loses "SKD" and "078".
        for slot in ("name", "initials", "number"):
            for k in candidates(v.get(slot) or ""):
                setidx.setdefault(k, r["id"])
alias_map = json.loads((ROOT / "tools/alias-map.json").read_text())["alias"]


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


def resolve(name, set_hint=None, page=None):
    """Name (+ set hint, + page) -> member id, or None when it stays ambiguous."""
    if not name:
        return None
    pinned = PERP_OVERRIDES.get((name, page))
    if pinned:
        return pinned
    cands = set(name_idx.get(norm(name), ()))
    if len(cands) == 1:
        return next(iter(cands))
    if not cands:
        return None
    sid = resolve_set(set_hint)
    if sid:
        narrowed = {c for c in cands if sid in by_id[c]["set_ids"]}
        if len(narrowed) == 1:
            return narrowed.pop()
    exact = {c for c in cands if norm(by_id[c]["nickname"]) == norm(name)}
    return exact.pop() if len(exact) == 1 else None


def ensure_missing_members(api):
    """Create the lost members and register them in the local index."""
    made = 0
    alliances = {
        norm(a["name"]): a["id"]
        for a in q(f"SELECT id, name FROM alliance WHERE universe_id='{CHICAGO}'")
    }
    for spec in MISSING_MEMBERS:
        sid = resolve_set(spec["set"]) if spec.get("set") else None
        aid = alliances.get(norm(spec.get("alliance", ""))) if spec.get("alliance") else None
        if not sid and not aid:
            print(f"  rattachement introuvable pour {spec['nickname']!r}: {spec}")
            continue
        existing = name_idx.get(norm(spec["nickname"]), ())
        if sid and any(sid in by_id[m]["set_ids"] for m in existing):
            continue
        if aid and existing:
            continue
        body = {
            "universe_id": CHICAGO,
            "nickname": spec["nickname"],
            "nickname_unknown": False,
            "status": spec["status"],
            "biography": "",
        }
        if sid:
            body["affiliations"] = [{"set_id": sid, "is_primary": True}]
        if aid:
            body["alliance_id"] = aid
        if spec["aliases"]:
            body["aliases"] = spec["aliases"]
        r = api.call("POST", f"members/?universe_id={CHICAGO}", body)
        if r and r.get("_error"):
            print(f"  creation echouee {spec['nickname']!r}: {r}")
            continue
        by_id[r["id"]] = {
            "id": r["id"],
            "nickname": spec["nickname"],
            "aliases": spec["aliases"],
            "set_ids": [sid],
        }
        for n in [spec["nickname"], *spec["aliases"]]:
            name_idx[norm(n)].add(r["id"])
        made += 1
        print(f"  cree {spec['nickname']!r} sur {spec.get('set') or spec.get('alliance')!r}")
    return made


# ---------------------------------------------------------------------------
old_events = json.loads((ROOT / "tools/extract-chicago-events.json").read_text())
_, new_events = E.extract()

# The lost members must exist before any resolution runs, or their events resolve
# to nobody and the attribution is dropped instead of handed back.
api = Api() if "--go" in sys.argv else None
if api:
    ensure_missing_members(api)


def slot(e):
    """The event-slot key the two extractions share."""
    return (e["page"], e["kind"], e["victim"], e["victim_set"])


old_by_slot = collections.defaultdict(list)
for e in old_events:
    old_by_slot[slot(e)].append(str(e["perp"]))
changed_slots = {
    slot(e)
    for e in new_events
    if sorted(old_by_slot.get(slot(e), []))
    != sorted(str(x["perp"]) for x in new_events if slot(x) == slot(e))
}

# A member the old parse never created lost ALL of his attributions, not only the
# ones a changed slot covers: the seed could not resolve his name to a row, so
# every event naming him was dropped. Pull his slots in too.
_lost_names = {m["nickname"] for m in MISSING_MEMBERS}
changed_slots |= {slot(e) for e in new_events if e["perp"] in _lost_names}

# Victims touched by a changed slot; their incidents get recomputed in full.
affected = {}
for e in new_events:
    if slot(e) not in changed_slots or e["kind"] not in ("bodies", "shootings", "assists"):
        continue
    vid = resolve(e["victim"], e["victim_set"])
    if vid:
        affected[vid] = affected.get(vid, set()) | {
            "MURDER" if e["kind"] == "bodies" else "SHOOTING"
        }

# Full corrected picture per victim, from ALL new events (not just changed ones).
want = collections.defaultdict(lambda: {"MURDER": {}, "SHOOTING": {}})
for e in new_events:
    if e["kind"] not in ("bodies", "shootings", "assists"):
        continue
    vid = resolve(e["victim"], e["victim_set"])
    if vid not in affected:
        continue
    pid = resolve(e["perp"], e["perp_set"], e["page"])
    if not pid or pid == vid:
        continue
    if e["kind"] == "assists":
        for t in ("MURDER", "SHOOTING"):
            if t in affected[vid]:
                want[vid][t].setdefault(pid, "ASSISTED")
    else:
        t = KIND_TYPE[e["kind"]]
        want[vid][t][pid] = "SHOOTER"

print(f"changed event slots: {len(changed_slots)} | victims affected: {len(affected)}")

plans, unresolved_removals = [], 0
for vid, types in sorted(affected.items(), key=lambda kv: by_id[kv[0]]["nickname"] or ""):
    for typ in sorted(types):
        rows = q(
            f"""SELECT i.id, json_agg(json_build_object('member_id', ip.member_id::text,
                       'role', ip.role, 'outcome', ip.outcome, 'acquitted', ip.acquitted,
                       'notes', ip.notes)) parts
                FROM incident i JOIN incident_participant ip ON ip.incident_id=i.id
                WHERE i.universe_id='{CHICAGO}' AND i.type='{typ}'
                  AND EXISTS (SELECT 1 FROM incident_participant v
                              WHERE v.incident_id=i.id AND v.member_id='{vid}' AND v.role='VICTIM')
                GROUP BY i.id"""
        )
        if len(rows) != 1:
            continue
        inc = rows[0]
        current = {p["member_id"]: p for p in inc["parts"]}
        target = want[vid][typ]
        keep = [p for mid, p in current.items() if p["role"] == "VICTIM"]
        new_parts = list(keep)
        for mid, role in target.items():
            prev = current.get(mid)
            new_parts.append(
                {
                    "member_id": mid,
                    "role": role,
                    "outcome": (prev or {}).get("outcome", "UNKNOWN"),
                    "acquitted": (prev or {}).get("acquitted", False),
                    "notes": (prev or {}).get("notes"),
                }
            )
        before = {(p["member_id"], p["role"]) for p in inc["parts"]}
        after = {(p["member_id"], p["role"]) for p in new_parts}
        if before == after:
            continue
        plans.append(
            {
                "incident": inc["id"],
                "type": typ,
                "victim": by_id[vid]["nickname"],
                "removed": [by_id[m]["nickname"] for m, r in before - after if m in by_id],
                "added": [by_id[m]["nickname"] for m, r in after - before if m in by_id],
                "participants": new_parts,
            }
        )

moved = collections.Counter()
for p in plans:
    for n in p["removed"]:
        moved[n] -= 1
    for n in p["added"]:
        moved[n] += 1
print(f"incidents to patch: {len(plans)}\n")
print("net change per member (negative = wrongly credited, now removed):")
for name, n in sorted(moved.items(), key=lambda kv: kv[1]):
    if n:
        print(f"   {n:+4}  {name}")

who = sys.argv[sys.argv.index("--who") + 1] if "--who" in sys.argv else None
if who:
    print(f"\nincidents touching {who!r}:")
    for p in plans:
        if who in p["removed"] or who in p["added"]:
            print(f"   {p['type']:8} victim={p['victim']!r:16} -{p['removed']} +{p['added']}")

if "--go" not in sys.argv:
    print("\nDRY RUN - re-run with --go to apply")
    sys.exit()

done = 0
for p in plans:
    r = api.call(
        "PATCH",
        f"incidents/{p['incident']}?universe_id={CHICAGO}",
        {"participants": p["participants"]},
    )
    if r and r.get("_error"):
        print(f"  failed on {p['victim']}: {r}")
    else:
        done += 1
print(f"\npatched {done}/{len(plans)} incidents")
