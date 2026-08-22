"""Reconcile Chicago incidents against the extraction instead of wiping them.

`seed_chicago_incidents.py` deletes every incident and rebuilds. That is why the
parser fixes looked unappliable: a rebuild would also destroy the hand-made
records (the T-Slick murder), the folded duplicate murders and every manual edit.

This drives the SAME grouping and the SAME resolver as the seed - it imports the
module, whose top half is pure computation, and catches the dry-run `sys.exit` -
then writes only the difference:

  * a group whose incident exists     -> PATCH when the participant set differs
  * a group with no incident          -> POST it
  * an incident the extraction does not know about -> LEFT ALONE, and reported

Using the seed's `resolve_person` matters: it scopes names by page, alliance and
person-page subject set, and resolves cases the simpler local resolvers in
`fix_misattributed_incidents.py` cannot.

Dry-run by default; --go writes. --limit N caps how many creations are made.
"""

import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def load_seed():
    """Import the seed module for its indexes, resolver and grouping."""
    argv = sys.argv
    sys.argv = ["seed_chicago_incidents.py"]  # force its dry-run path
    spec = importlib.util.spec_from_file_location("seedmod", HERE / "seed_chicago_incidents.py")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass  # the dry run exits after printing its report
    finally:
        sys.argv = argv
    return mod


print("--- rapport du seed (calcul seulement, rien n'est ecrit) ---")
S = load_seed()
print("--- fin du rapport ---\n")

from wikiapi import CHICAGO, Api, q  # noqa: E402

# Every incident already in the universe, keyed by (victim member id, type).
existing = {}
for r in q(
    f"""SELECT i.id, i.type, ip.member_id AS vid,
               (SELECT json_agg(json_build_object('member_id', p.member_id::text, 'role', p.role,
                        'outcome', p.outcome, 'acquitted', p.acquitted, 'notes', p.notes))
                FROM incident_participant p WHERE p.incident_id=i.id) parts
        FROM incident i JOIN incident_participant ip
          ON ip.incident_id=i.id AND ip.role='VICTIM'
        WHERE i.universe_id='{CHICAGO}'"""
):
    existing.setdefault((r["vid"], r["type"]), []).append(r)

patch, create, ambiguous = [], [], []
for murder, group in ((True, S.murders), (False, S.shootings)):
    typ = "MURDER" if murder else "SHOOTING"
    for vid, g in group.items():
        body = S.payload(vid, g, murder)
        want = {p["member_id"]: p["role"] for p in body["participants"]}
        rows = existing.get((vid, typ), [])
        if not rows:
            create.append((vid, typ, body))
            continue
        if len(rows) > 1:
            ambiguous.append((vid, typ, len(rows)))
            continue
        inc = rows[0]
        have = {p["member_id"]: p["role"] for p in inc["parts"]}
        if have == want:
            continue
        # Keep whatever a person added by hand: only the roles the extraction
        # knows about are rewritten, the victim row is preserved as stored.
        merged = {p["member_id"]: p for p in inc["parts"] if p["role"] == "VICTIM"}
        for p in body["participants"]:
            if p["member_id"] in merged:
                continue
            prev = next((x for x in inc["parts"] if x["member_id"] == p["member_id"]), None)
            merged[p["member_id"]] = {
                "member_id": p["member_id"],
                "role": p["role"],
                "outcome": p.get("outcome", "UNKNOWN"),
                "acquitted": (prev or {}).get("acquitted", False),
                "notes": (prev or {}).get("notes"),
            }
        if {(m, v["role"]) for m, v in merged.items()} == {
            (p["member_id"], p["role"]) for p in inc["parts"]
        }:
            continue
        patch.append((vid, typ, inc, list(merged.values())))

known_ids = {r["id"] for rows in existing.values() for r in rows}
covered = {rows[0]["id"] for (vid, typ), rows in existing.items() if len(rows) == 1}
seed_ids = set()
for murder, group in ((True, S.murders), (False, S.shootings)):
    typ = "MURDER" if murder else "SHOOTING"
    for vid in group:
        for r in existing.get((vid, typ), []):
            seed_ids.add(r["id"])
orphans = known_ids - seed_ids

print(f"groupes calcules : {len(S.murders)} meurtres + {len(S.shootings)} fusillades")
print(f"a creer          : {len(create)}")
print(f"a corriger       : {len(patch)}")
print(f"ambigus (plusieurs incidents pour une victime) : {len(ambiguous)}")
print(f"incidents en base que l'extraction ignore (intouches) : {len(orphans)}")

print("\nechantillon de creations:")
for vid, typ, body in create[:12]:
    who = ", ".join(
        f"{S.display.get(p['member_id'], '?')}:{p['role']}" for p in body["participants"]
    )
    print(f"   {typ:8} victime={S.display.get(vid, '?')!r:18} {who[:96]}")
print("\nechantillon de corrections:")
for vid, typ, inc, parts in patch[:12]:
    before = {S.display.get(p["member_id"], "?") for p in inc["parts"] if p["role"] != "VICTIM"}
    after = {S.display.get(p["member_id"], "?") for p in parts if p["role"] != "VICTIM"}
    print(
        f"   {typ:8} victime={S.display.get(vid, '?')!r:18} {sorted(before - after)} -> {sorted(after - before)}"
    )

if "--go" not in sys.argv:
    print("\nDRY RUN - relancez avec --go")
    sys.exit()

limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else len(create)
api = Api()
src = q(f"SELECT id FROM source WHERE universe_id='{CHICAGO}' AND url='{S.SITE}'")
source_ids = [src[0]["id"]] if src else []

done = err = 0
for vid, _typ, inc, parts in patch:
    r = api.call("PATCH", f"incidents/{inc['id']}?universe_id={CHICAGO}", {"participants": parts})
    if r and r.get("_error"):
        err += 1
        print(f"  echec patch {S.display.get(vid)!r}: {r['_error']} {r.get('_body', '')[:90]}")
    else:
        done += 1
print(f"corriges {done}, echecs {err}")

made = err2 = 0
for vid, _typ, body in create[:limit]:
    if source_ids:
        body = body | {"source_ids": source_ids}
    r = api.call("POST", f"incidents/?universe_id={CHICAGO}", body)
    if r and r.get("_error"):
        err2 += 1
        if err2 <= 5:
            print(f"  echec create {S.display.get(vid)!r}: {r['_error']} {r.get('_body', '')[:90]}")
    else:
        made += 1
print(f"crees {made}, echecs {err2}")
