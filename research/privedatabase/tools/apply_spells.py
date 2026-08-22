"""Write the agent-extracted incarceration spells into member_incarceration.

The table was empty across the whole universe while 200 members sat at LOCKED,
so their sentence, charge and release dates lived only in the French source. Eight
Haiku agents extracted them under the quote rule (every field carries the exact
substring that states it) and `verify_spells.py` checked all 200 mechanically.

Only members with something substantive get a spell: a bare "actuellement
incarcere" adds nothing that `status = LOCKED` does not already say.

Two things the schema cannot hold go into `notes`:
  * the length of the term - the table has dates and life_sentence, no year count;
  * the source's exculpatory wording ("un meurtre qu'il n'a pas commis"), which a
    bare charge would silently drop.

Dry-run by default; --go writes.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from wikiapi import CHICAGO, Api, q  # noqa: E402

SP = pathlib.Path(
    "/tmp/claude-1000/-home-lbzgiu-squiidwiki/e321bca8-b6be-470e-95db-fdd005e71a4f/scratchpad"
)
# The source says outright that these three did not do it; the charge alone would
# read as a conviction the site does not claim.
# The source has a typo here - "pour le mettre de Duski" for "le meurtre de Duski".
# The agent correctly refused to guess and rendered it literally, which leaves an
# unusable note; the French is kept so a reader can see why.
NOTE_OVERRIDE = {
    "s144": "Murder of Duski (Hoola Gang) - source reads \u00ab pour le mettre \u00bb, a typo",
}
EXCULPATED = {
    "s57": "source states he did not commit it",
    "s119": "source states he did not commit it",
    "s180": "source states he did not commit it, but was present",
}


def fuzzy(d):
    """A {year,month,day} dict as the API's FuzzyDate."""
    if not d or not d.get("year"):
        return None
    out = {"year": d["year"], "month": d.get("month"), "day": d.get("day"), "approx": False}
    out["precision"] = "YMD" if out["day"] else "YM" if out["month"] else "Y"
    return out


def notes_for(e, ref):
    """Everything true that the structured columns cannot carry."""
    bits = []
    if ref in NOTE_OVERRIDE:
        bits.append(NOTE_OVERRIDE[ref])
    elif e.get("charge_en"):
        bits.append(e["charge_en"][0].upper() + e["charge_en"][1:])
    if e.get("sentence_years"):
        bits.append(f"{e['sentence_years']}-year sentence")
    # Only add the exculpation when the charge does not already carry it, or Beans
    # ends up saying it twice.
    if ref in EXCULPATED and not any(
        w in (e.get("charge_en") or "").lower() for w in ("not ", "present")
    ):
        bits.append(EXCULPATED[ref])
    return "; ".join(bits) or None


with open(SP / "spell_corpus.json") as fh:
    corpus = {c["ref"]: c for c in json.load(fh)}

extracted = {}
for n in range(1, 9):
    path = SP / f"spell_out_{n}.json"
    if not path.exists():
        sys.exit(f"lot {n} manquant - lancez la verification d'abord")
    with open(path) as fh:
        for e in json.load(fh):
            extracted[e["ref"]] = e

already = {
    r["member_id"]
    for r in q(
        f"""SELECT DISTINCT x.member_id FROM member_incarceration x
            JOIN member m ON m.id=x.member_id WHERE m.universe_id='{CHICAGO}'"""
    )
}

plans = []
for ref, e in sorted(extracted.items(), key=lambda kv: int(kv[0][1:])):
    src = corpus.get(ref)
    if not src or src["id"] in already:
        continue
    body = {
        "from_date": fuzzy({"year": e["from_year"]}) if e.get("from_year") else None,
        "earliest_release_date": fuzzy(e.get("earliest_release")),
        "max_discharge_date": fuzzy(e.get("max_release")),
        "life_sentence": bool(e.get("life_sentence")),
        "notes": notes_for(e, ref),
    }
    if not any(
        [
            body["from_date"],
            body["earliest_release_date"],
            body["max_discharge_date"],
            body["life_sentence"],
            body["notes"],
        ]
    ):
        continue
    plans.append((ref, src, body))

print(f"spells a creer: {len(plans)} (sur {len(corpus)} membres LOCKED sans spell)")
for _ref, src, body in plans:
    parts = []
    if body["from_date"]:
        parts.append(f"depuis {body['from_date']['year']}")
    for label, key in (("liberable", "earliest_release_date"), ("max", "max_discharge_date")):
        if body[key]:
            d = body[key]
            parts.append(
                f"{label} {d.get('day') or ''}/{d.get('month') or ''}/{d['year']}".replace(
                    "//", "/"
                )
            )
    if body["life_sentence"]:
        parts.append("perpetuite")
    print(f"   {src['subject']!r:22} {' | '.join(parts) or '-':32} {body['notes'] or ''}")

stale = [
    (src["subject"], body["earliest_release_date"]["year"])
    for _ref, src, body in plans
    if body["earliest_release_date"] and body["earliest_release_date"]["year"] <= 2025
]
if stale:
    print(f"\n{len(stale)} liberations que la source situait dans le futur sont deja passees;")
    print("leur statut LOCKED est probablement perime (rien n'est change ici):")
    for name, yr in stale:
        print(f"   {name!r:22} liberable {yr}")

if "--go" not in sys.argv:
    print("\nDRY RUN - relancez avec --go")
    sys.exit()

api = Api()
made = err = 0
for _ref, src, body in plans:
    r = api.call("POST", f"members/{src['id']}/incarcerations?universe_id={CHICAGO}", body)
    if r and r.get("_error"):
        err += 1
        print(f"  echec {src['subject']!r}: {r['_error']} {r.get('_body', '')[:110]}")
    else:
        made += 1
print(f"\ncrees {made}, echecs {err}")
