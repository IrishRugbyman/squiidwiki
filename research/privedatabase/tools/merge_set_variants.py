"""Merge a set's acronym and its expansion into one name variant.

A name variant has three slots - `name`, `initials`, `number` - so that one row
can hold "Never Leave My Brothers", "NLMB" and a number together, and the display
picks which one leads. `backfill_set_name_variants.py` filled the slots correctly
but never merged rows: it split each stored variant string on its own, so NLMB
ended up with an initials-only row beside a name-only row saying the same thing.

This joins them where the acronym is demonstrably built from the name, and leaves
the number alone. A numeric alias like "1212" or "8X13" is a name in its own
right, not a qualifier of another name, so merging it into a neighbouring row
would invent a set number the source never gives.

Dry-run by default; --go applies.
"""

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from wikiapi import CHICAGO, Api, q  # noqa: E402


def initials_of(full):
    """First letter of every word, camelCase included: GuttaVille Gangstas -> GVG."""
    words = re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z]*|[0-9]+|[a-z]+", full or "")
    return "".join(w[0] for w in words).upper()


def letters(s):
    """An acronym reduced to its alphanumerics: D.O.D -> DOD."""
    return re.sub(r"[^A-Za-z0-9]", "", s or "").upper()


def is_abbreviation(name, acro):
    """True when `acro` is `name` shortened, by initials or by contraction.

    STL is not the initials of "Saint Lawrence" - it is the word contracted, the
    way EBT contracts "Eberhart". Requiring initials alone left STL/EBT with five
    variant rows for three things. A contraction must keep the letters in order
    and start on the same letter, which is tight enough to reject unrelated pairs.
    """
    a = letters(acro)
    n = letters(name)
    if len(a) < 2 or not n or a[0] != n[0]:
        return False
    if a == initials_of(name):
        return True
    i = 0
    for ch in n:
        if i < len(a) and ch == a[i]:
            i += 1
    return i == len(a)


sets = q(
    f"""SELECT id, name, coalesce(name_variants,'[]'::jsonb) nv
        FROM sets WHERE universe_id='{CHICAGO}' AND NOT is_reserved ORDER BY name"""
)

plans = []
for s in sets:
    variants = list(s["nv"] or [])
    merged, consumed = [], set()
    for i, acro in enumerate(variants):
        if i in consumed or not acro.get("initials") or acro.get("name"):
            continue
        for j, named in enumerate(variants):
            if j == i or j in consumed or not named.get("name") or named.get("initials"):
                continue
            if not is_abbreviation(named["name"], acro["initials"]):
                continue
            consumed |= {i, j}
            merged.append(
                {
                    "name": named["name"],
                    "initials": acro["initials"],
                    "number": acro.get("number") or named.get("number"),
                    "is_primary": acro.get("is_primary") or named.get("is_primary", False),
                    # The set is filed under its acronym, so the acronym keeps leading
                    # the display even though the row now carries the full name too.
                    "lead": "initials" if acro.get("is_primary") else None,
                }
            )
            break
    if not consumed:
        continue
    out = [v for k, v in enumerate(variants) if k not in consumed] + merged
    if not any(v.get("is_primary") for v in out):
        out[0]["is_primary"] = True
    plans.append((s, out))


def render(v):
    """How the frontend shows one entry."""
    lead = v.get("lead") or (
        "name" if v.get("name") else "initials" if v.get("initials") else "number"
    )
    extras = [v[k] for k in ("name", "initials", "number") if k != lead and v.get(k)]
    return f"{v.get(lead)} ({' · '.join(extras)})" if extras else str(v.get(lead))


print(f"sets a corriger: {len(plans)}\n")
for s, out in plans:
    before = " | ".join(render(v) for v in (s["nv"] or []))
    print(f"   {s['name']!r}")
    print(f"      avant : {before}")
    print(f"      apres : {' | '.join(render(v) for v in out)}")

if "--go" not in sys.argv:
    print("\nDRY RUN - relancez avec --go")
    sys.exit()

api = Api()
done = err = 0
for s, out in plans:
    r = api.call("PATCH", f"sets/{s['id']}?universe_id={CHICAGO}", {"name_variants": out})
    if r and r.get("_error"):
        err += 1
        print(f"  echec {s['name']!r}: {r['_error']} {r.get('_body', '')[:90]}")
    else:
        done += 1
print(f"\nmis a jour {done}, echecs {err}")
