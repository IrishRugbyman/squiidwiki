"""Write the agent-drafted biographies to the members that have none.

454 members carried a source sentence and an empty biography. Ten Haiku agents
drafted one each under a single rule: say only what no other column holds, and
return an empty string when nothing is left. 272 came back with text, 182 empty -
the empties are correct answers, not failures.

`verify_bios.py` checks each draft mechanically (no invented proper name, no
restated set, gang, family or status). This applies what survives, with one more
trim the drafting instructions could not know about: the incarceration spells
written earlier today already carry the charge, so a bio that opens "Incarcerated
for the murder of X" is repeating a column again. That clause is cut and whatever
the sentence added beyond it is kept.

Dry-run by default; --go writes.
"""

import json
import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from wikiapi import CHICAGO, Api, q  # noqa: E402

SP = pathlib.Path(
    "/tmp/claude-1000/-home-lbzgiu-squiidwiki/e321bca8-b6be-470e-95db-fdd005e71a4f/scratchpad"
)
# "Incarcerated for the murder of X.", "Sentenced to 30 years for murder."
CHARGE_CLAUSE = re.compile(
    r"^(?:He (?:is|was) )?(?:currently )?"
    r"(?:incarcerated|imprisoned|sentenced|serving|convicted|jailed)\b[^.]*\.\s*",
    re.I,
)


def fold(s):
    """Lowercase, accent-stripped, for substring tests."""
    s = unicodedata.normalize("NFD", str(s))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


with open(SP / "bio_corpus.json") as fh:
    corpus = {c["ref"]: c for c in json.load(fh)}
drafts = {}
for n in range(1, 11):
    path = SP / f"bio_out_{n}.json"
    if not path.exists():
        sys.exit(f"lot {n} manquant - relancez la verification d'abord")
    with open(path) as fh:
        for e in json.load(fh):
            drafts[e["ref"]] = e

spells = {
    r["member_id"]: r["notes"]
    for r in q(
        f"""SELECT x.member_id, x.notes FROM member_incarceration x JOIN member m
            ON m.id=x.member_id WHERE m.universe_id='{CHICAGO}' AND x.notes IS NOT NULL"""
    )
}
current = {
    r["id"]: (r["biography"] or "").strip()
    for r in q(f"SELECT id, biography FROM member WHERE universe_id='{CHICAGO}'")
}

plans, trimmed, skipped = [], 0, 0
for ref, e in sorted(drafts.items(), key=lambda kv: int(kv[0][1:])):
    src = corpus.get(ref)
    bio = (e.get("bio") or "").strip()
    if not src or not bio:
        continue
    mid = src["member_id"]
    if current.get(mid):
        skipped += 1  # someone wrote one by hand since the corpus was built
        continue
    note = spells.get(mid)
    if note:
        # Cut the opening charge clause only when the spell already states it.
        key = re.sub(r"^(murder|shooting|killing) of ", "", fold(note).split(";")[0]).strip()
        head = CHARGE_CLAUSE.match(bio)
        if head and key and (key in fold(head.group(0)) or len(key) < 9):
            rest = bio[head.end() :].strip()
            if rest:
                bio, trimmed = rest, trimmed + 1
            else:
                continue  # the whole bio was the charge; the spell says it already
    plans.append((mid, src["name"], bio, ref))

print(
    f"brouillons: {len(drafts)} | avec texte: {sum(1 for e in drafts.values() if (e.get('bio') or '').strip())}"
)
print(f"a ecrire: {len(plans)} | clauses de peine coupees: {trimmed} | deja une bio: {skipped}")
for _mid, name, bio, ref in plans[:12]:
    print(f"   [{ref}] {name!r:20} {bio[:110]}")

if "--go" not in sys.argv:
    print("\nDRY RUN - relancez avec --go")
    sys.exit()

api = Api()
done = err = 0
for mid, name, bio, _ref in plans:
    r = api.call("PATCH", f"members/{mid}?universe_id={CHICAGO}", {"biography": bio})
    if r and r.get("_error"):
        err += 1
        if err <= 5:
            print(f"  echec {name!r}: {r['_error']} {r.get('_body', '')[:90]}")
    else:
        done += 1
print(f"\nbios ecrites {done}, echecs {err}")
