"""Check the agents' incarceration extraction against the source sentence.

Same contract as verify_pilot.py: every field carries a `<field>_quote` copied
verbatim from the sentence, so three mechanical checks stand in for trusting the
model - the quote is really in the sentence, the value is really in the quote,
and nothing was emitted without one.

Two extra checks this one needs:
  * `charge_fr` is its own evidence, so it must itself be an exact substring;
  * a release date must not be the arithmetic of from_year + sentence_years,
    which is the inference the free model already tried once.
"""

import json
import pathlib
import re
import unicodedata

SP = pathlib.Path(
    "/tmp/claude-1000/-home-lbzgiu-squiidwiki/e321bca8-b6be-470e-95db-fdd005e71a4f/scratchpad"
)
MONTHS = {
    1: "janvier",
    2: "fevrier",
    3: "mars",
    4: "avril",
    5: "mai",
    6: "juin",
    7: "juillet",
    8: "aout",
    9: "septembre",
    10: "octobre",
    11: "novembre",
    12: "decembre",
}
NUMERIC = ("from_year", "sentence_years")
DATES = ("earliest_release", "max_release")


def fold(s):
    """Lowercase and strip accents so 'Aout' matches 'Août'."""
    s = unicodedata.normalize("NFD", str(s))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def nums(text):
    """Every integer appearing in a piece of text."""
    return set(re.findall(r"\d+", text))


def check(entry, sentence):
    """Problems with one extracted entry, as a list of strings."""
    bad = []
    fsent = fold(sentence)
    for key, val in entry.items():
        if key in ("ref", "charge_en") or key.endswith("_quote"):
            continue
        quote = entry["charge_fr"] if key == "charge_fr" else entry.get(f"{key}_quote")
        if not quote:
            bad.append(f"{key}: aucune citation")
            continue
        fq = fold(quote)
        if fq not in fsent:
            bad.append(f"{key}: citation absente de la phrase -> {quote!r}")
            continue
        if key in NUMERIC:
            if str(val) not in nums(fq):
                bad.append(f"{key}={val} absent de la citation {quote!r}")
        elif key == "life_sentence":
            if val and not re.search(r"perpetuit|a vie", fq):
                bad.append("life_sentence sans 'perpetuite'/'a vie' dans la citation")
        elif key in DATES and isinstance(val, dict):
            if val.get("year") and str(val["year"]) not in nums(fq):
                bad.append(f"{key}: annee {val['year']} absente de la citation")
            if val.get("day") and str(val["day"]) not in nums(fq):
                bad.append(f"{key}: jour {val['day']} absent de la citation")
            if val.get("month") and MONTHS.get(val["month"], "@") not in fq:
                bad.append(f"{key}: mois {val['month']} absent de la citation")
    # The arithmetic the free model already attempted once.
    fy, yrs = entry.get("from_year"), entry.get("sentence_years")
    if isinstance(fy, int) and isinstance(yrs, int):
        for key in DATES:
            got = entry.get(key)
            if (
                isinstance(got, dict)
                and got.get("year") == fy + yrs
                and str(fy + yrs) not in nums(fold(entry.get(f"{key}_quote", "")))
            ):
                bad.append(f"{key}: annee calculee ({fy}+{yrs}), pas citee")
    return bad


corpus = {}
with open(SP / "spell_corpus.json") as fh:
    for c in json.load(fh):
        corpus[c["ref"]] = c

total = withfield = clean = 0
problems = []
missing = []
for n in range(1, 9):
    path = SP / f"spell_out_{n}.json"
    if not path.exists():
        missing.append(n)
        continue
    with open(path) as fh:
        for e in json.load(fh):
            src = corpus.get(e.get("ref"))
            if not src:
                problems.append((e.get("ref"), ["ref inconnue"], ""))
                continue
            total += 1
            fields = [k for k in e if k not in ("ref", "charge_en") and not k.endswith("_quote")]
            if fields:
                withfield += 1
            bad = check(e, src["sentence"])
            if bad:
                problems.append((e["ref"], bad, src["sentence"]))
            else:
                clean += 1

print(f"lots manquants: {missing or 'aucun'}")
print(f"{total} entrees verifiees | {withfield} avec au moins un champ | {clean} sans anomalie")
for ref, bad, sent in problems:
    print(f"\n  {ref}: " + "; ".join(bad))
    if sent:
        print(f"     phrase: {sent[:170]}")
