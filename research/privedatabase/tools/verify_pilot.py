"""Check an agent's fact extraction against the source sentence, mechanically.

Every field an agent emits must come with a `<field>_quote` copied verbatim from
the sentence. That turns "do I trust the model" into three checks a machine can
run: the quote really is in the sentence, the value really is in the quote, and
nothing was emitted without one. An agent that paraphrases its quote, or invents
a year, fails here rather than silently entering the database.
"""

import json
import re
import sys
import unicodedata

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


def fold(s):
    """Lowercase and strip accents, so 'Aout' matches 'Août'."""
    s = unicodedata.normalize("NFD", str(s))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def check(entry, sentence):
    """Return the list of problems with one extracted entry."""
    bad = []
    fsent = fold(sentence)
    for key, val in entry.items():
        if key in ("id",) or key.endswith("_quote"):
            continue
        quote = entry.get(f"{key}_quote")
        if not quote:
            bad.append(f"{key}: aucune citation")
            continue
        if fold(quote) not in fsent:
            bad.append(f"{key}: citation absente de la phrase -> {quote!r}")
            continue
        fq = fold(quote)
        if key in ("sentence_years", "release_year", "max_release_year", "age_at_death"):
            if val == "life":
                if not re.search(r"perpetuit", fq):
                    bad.append(f"{key}: 'life' sans 'perpetuite' dans la citation")
            elif str(val) not in re.sub(r"\D", " ", fq).split():
                bad.append(f"{key}: valeur {val} absente de la citation {quote!r}")
        elif key in ("death_date", "birth_date") and isinstance(val, dict):
            if val.get("year") and str(val["year"]) not in fq:
                bad.append(f"{key}: annee {val['year']} absente de la citation")
            if val.get("day") and str(val["day"]) not in re.sub(r"\D", " ", fq).split():
                bad.append(f"{key}: jour {val['day']} absent de la citation")
            if val.get("month") and MONTHS.get(val["month"], "@") not in fq:
                bad.append(f"{key}: mois {val['month']} absent de la citation")
    return bad


SP = "/tmp/claude-1000/-home-lbzgiu-squiidwiki/e321bca8-b6be-470e-95db-fdd005e71a4f/scratchpad"
n = sys.argv[1]
with open(f"{SP}/pilot_batch_{n}.json") as fh:
    corpus = {c["id"]: c for c in json.load(fh)}
try:
    with open(f"{SP}/pilot_out_{n}.json") as fh:
        out = json.load(fh)
except FileNotFoundError:
    sys.exit(f"lot {n}: pas de sortie")

ok = withfact = 0
problems = []
for e in out:
    src = corpus.get(e.get("id"))
    if not src:
        problems.append((e.get("id"), ["id inconnu"]))
        continue
    fields = [k for k in e if k != "id" and not k.endswith("_quote")]
    if fields:
        withfact += 1
    bad = check(e, src["sentence"])
    if bad:
        problems.append((e["id"], bad))
    else:
        ok += 1

print(f"lot {n}: {len(out)}/{len(corpus)} entrees, {withfact} avec un fait, {ok} sans anomalie")
for eid, bad in problems:
    print(f"   {eid}: " + "; ".join(bad))
    src = corpus.get(eid)
    if src:
        print(f"        phrase: {src['sentence'][:150]}")
