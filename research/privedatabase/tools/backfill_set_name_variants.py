"""Fill the structured slots of every set's name variants: name / initials / number.

`name_variants` on a set is not a list of strings - each entry has three slots,
`name`, `initials` and `number`, plus a `lead` saying which one heads the display
("Killaward" renders as `Killaward (078)`, `SKD` as `SKD (South King Drive)`).
Nothing had ever populated `initials` or `number`: all 303 Chicago sets carried
variants with only `name` set, so the whole structure rendered as flat strings.

This derives the slots from what the source already states:

  - the page titles that spell out `FULL NAME (ACRONYM)` - "SOUTH KING DRIVE
    (SKD)", "COREY MONEY BROTHERS (CMB)", "OAK BOYZ NATION (OBN)" - which give a
    full name and its acronym for the same set;
  - a standalone number inside a set name: "Killaward 078", "051 Young Money",
    "THF 46", "600". The number moves to its own slot and the rest stays as name.
  - a set name that is nothing but an acronym ("MOB", "NLMB", "D.O.D", "STL/EBT")
    goes to `initials` rather than `name`.

It rewrites only `name_variants`; the `name` column and the display order are left
alone, and an entry that already carries `initials` or `number` is never touched.

Dry-run by default; --go applies.
"""

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from db_sync import candidates, norm  # noqa: E402
from wikiapi import CHICAGO, Api, q  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent

# "600", "078", "11-5", "8X13", "400E", "9-0" - a token that is essentially a number.
NUMBER_TOKEN = re.compile(r"^\d+(?:[-xX]\d+)?[A-Za-z]?$")
# "MOB", "NLMB", "D.O.D", "STL/EBT", "W.B", "GME/EBE" - all caps, no lowercase word.
ACRONYM = re.compile(r"^[A-Z0-9]+(?:[./$][A-Z0-9]+)*$")
TITLE_ACRONYM = re.compile(r"^(.+?)\s*\(\s*([A-Z0-9./'’ -]{2,18})\s*\)\s*$")


def initials_of(full):
    """First letter of every word, splitting camelCase too: GuttaVille Gangstas -> GVG."""
    words = re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z]*|[0-9]+|[a-z]+", full)
    return "".join(w[0] for w in words).upper()


def is_real_acronym(full, acro):
    """True when `acro` is built from `full`, not a nation shorthand pasted on.

    The site titles "BLACKMOB (4CH)" and "P-BLOCK (4CH)", where 4CH is the gang
    nation (4 Corner Hustlers), not the set's own acronym.
    """
    letters = re.sub(r"[^A-Za-z0-9]", "", acro).upper()
    if not letters or " " in acro.strip():
        return False
    return letters == initials_of(full)


def split_slots(raw):
    """Split one variant string into (name, initials, number)."""
    s = re.sub(r"\s+", " ", (raw or "").strip())
    if not s:
        return None, None, None
    trailing = None
    m = TITLE_ACRONYM.match(s)
    if m and is_real_acronym(m.group(1).strip(), m.group(2)):
        s, trailing = m.group(1).strip(), m.group(2).strip()
    number = None
    tokens = s.split(" ")
    # A number token only counts at either end; "New Money 080" and "051 Young
    # Money" both yield 080/051, "Deathrow 085" likewise. A number in the middle
    # is part of the name.
    # Two digits minimum: "051", "078", "400E", "9-5" are set numbers, the "3" of
    # "3 Bs" is part of the name.
    for end in (-1, 0):
        tok = tokens[end]
        if len(tokens) > 1 and NUMBER_TOKEN.match(tok) and len(re.sub(r"\D", "", tok)) >= 2:
            number = tokens.pop(end)
            break
    rest = " ".join(tokens).strip()
    if not rest:
        return None, None, number or s
    if NUMBER_TOKEN.match(rest):
        return None, None, rest if number is None else f"{rest} {number}"
    if ACRONYM.match(rest) and len(rest) <= 8:
        return None, trailing or rest, number if not trailing else number
    return rest, trailing, number


def variant(name=None, initials=None, number=None, is_primary=False, lead=None):
    """One name-variant row."""
    return {
        "name": name,
        "initials": initials,
        "number": number,
        "is_primary": is_primary,
        "lead": lead,
    }


# --- full-name / acronym pairs the source states outright -------------------
owner = json.loads((ROOT / "tools/wp-owner.json").read_text())
pairs = {}  # comparison key -> (full name, acronym)
for p in json.loads((ROOT / "raw/pages.json").read_text()):
    if owner.get(p["slug"]) != "chicago":
        continue
    m = TITLE_ACRONYM.match(re.sub(r"\s+", " ", p["title"]).strip())
    if not m:
        continue
    full, acro = m.group(1).strip(), m.group(2).strip()
    if " " in acro.strip():
        continue  # "(4 CORNER GLO GANG)" is another name, not an acronym
    full = full.title() if full.isupper() else full
    for k in (norm(full), norm(acro)):
        if k:
            pairs.setdefault(k, (full, acro))

# Reserved sets (Civilian, Police) accept bio updates only, by design.
sets = q(
    f"""SELECT id, name, coalesce(name_variants,'[]'::jsonb) nv
        FROM sets WHERE universe_id='{CHICAGO}' AND NOT is_reserved ORDER BY name"""
)

plans = []
# Sentence fragments left on the sets table by the roster-parenthetical bug:
# "arrete en 2017", "condamne a 50 ans", "il est gay". They start lowercase (the
# class is deliberately NOT case-insensitive) or open with a known French verb.
JUNK_LOWER = re.compile(r"^[a-z\u00e0-\u00ff]")
JUNK_WORD = re.compile(r"^(affili|condamn|arr[eê]t|enfant|tireur|assistance|rappeu)", re.I)
junk = []
for s in sets:
    if " " in s["name"] and (JUNK_LOWER.match(s["name"]) or JUNK_WORD.match(s["name"])):
        junk.append(s["name"])
        continue
    existing = s["nv"] or []
    if any(v.get("initials") or v.get("number") for v in existing):
        continue  # already structured, leave it
    known = next((pairs[k] for k in candidates(s["name"]) if k in pairs), None)
    # Validate the acronym against the DATABASE name: an all-caps page title has
    # lost its camel hump, so "GUTTAVILLE GANGSTAS" reads as GG while the stored
    # "GuttaVille Gangstas" correctly yields GVG.
    if known and not (is_real_acronym(s["name"], known[1]) or is_real_acronym(known[0], known[1])):
        known = None
    out, seen = [], set()
    for i, v in enumerate(existing) or [(0, variant(name=s["name"], is_primary=True))]:
        raw = (v.get("name") or "").strip()
        if not raw:
            continue
        if known:
            # "GUTTAVILLE GANGSTAS (GVG)" as a stored variant would otherwise survive
            # beside the split one; the acronym is already known for this set.
            raw = re.sub(rf"\s*\(\s*{re.escape(known[1])}\s*\)\s*$", "", raw, flags=re.I).strip()
        name, initials, number = split_slots(raw)
        if known:
            full, acro = known
            if initials and norm(initials) == norm(acro):
                name = name or full
            elif name and norm(name) == norm(full):
                initials = initials or acro
        key = (norm(name or ""), norm(initials or ""), norm(number or ""))
        if key in seen or not any(key):
            continue
        seen.add(key)
        out.append(variant(name, initials, number, v.get("is_primary", i == 0), v.get("lead")))
    if not out:
        continue
    if not any(v["is_primary"] for v in out):
        out[0]["is_primary"] = True
    if out != existing:
        plans.append((s, out))


def render(v):
    """How the frontend will show this entry."""
    lead = v["lead"] or ("name" if v["name"] else "initials" if v["initials"] else "number")
    head = v.get(lead) or ""
    extras = [v[k] for k in ("name", "initials", "number") if k != lead and v[k]]
    return f"{head} ({' · '.join(extras)})" if extras else head


print(f"sets: {len(sets)} | a enrichir: {len(plans)} | noms parasites ignores: {len(junk)}")
if junk:
    print(
        f"  (a nettoyer separement: {', '.join(repr(j) for j in junk[:8])}{' ...' if len(junk) > 8 else ''})"
    )
print()
enriched = [p for p in plans if any(v["initials"] or v["number"] for v in p[1])]
print(f"dont {len(enriched)} gagnent un acronyme ou un numero:\n")
for s, out in enriched:
    print(f"   {s['name']!r:28} -> {' | '.join(render(v) for v in out)}")

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
