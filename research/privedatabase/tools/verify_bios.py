"""Check the agent-written biographies against their source sentence, mechanically.

Prose cannot be checked the way a date can, but two things can:

  * **No invented names.** Every capitalised token in the bio must appear in the
    French sentence. A model that hallucinates an associate, a set or a song title
    fails here rather than in the database.
  * **No column duplicated.** The bio must not restate the set, the gang, the
    family or the bare status - those have their own fields, and repeating them
    is what makes a wiki rot. `already_in_fields` says what to look for per
    member.

What neither check can catch is a fluent, well-sourced sentence that misreads the
French. That is what the hand-read sample is for.
"""

import json
import pathlib
import re
import sys
import unicodedata

SP = pathlib.Path(
    "/tmp/claude-1000/-home-lbzgiu-squiidwiki/e321bca8-b6be-470e-95db-fdd005e71a4f/scratchpad"
)
# Words that legitimately start a sentence or name a month/nationality and are not
# claims about a person.
STOP = {
    "he",
    "his",
    "him",
    "the",
    "a",
    "an",
    "and",
    "was",
    "is",
    "in",
    "on",
    "of",
    "at",
    "one",
    "started",
    "known",
    "before",
    "after",
    "shot",
    "killed",
    "served",
    "had",
    "a.k.a",
    "og",
    "chicago",
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
}
STATUS_WORDS = {
    "DEAD": (r"\bis dead\b", r"\bis deceased\b", r"\bhe died\b"),
    "LOCKED": (r"\bis (?:currently )?(?:incarcerated|in prison|locked up)\b",),
    "FREE": (r"\bis free\b",),
}


def fold(s):
    """Lowercase, strip accents and punctuation runs, for substring tests."""
    s = unicodedata.normalize("NFD", str(s))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def caps(text):
    """Capitalised tokens, which in a bio are names unless they open a sentence."""
    out = []
    for m in re.finditer(r"(?<![.!?]\s)(?<!^)\b([A-Z][\w.'$-]*)", text):
        tok = re.sub(r"'s$", "", m.group(1)).strip(".'")
        if tok and fold(tok) not in STOP and len(tok) > 1:
            out.append(tok)
    return out


def check(entry, src):
    """Problems with one biography."""
    bio = (entry.get("bio") or "").strip()
    if not bio:
        return []
    bad = []
    fsent = fold(src["sentence"])
    fbio = fold(bio)
    for tok in caps(bio):
        if fold(tok) not in fsent:
            bad.append(f"nom absent de la phrase source: {tok!r}")
    fields = src.get("already_in_fields", {})
    # Only a MEMBERSHIP claim duplicates the column. A set named in a story - "fell
    # out with Hella Bandz", "Lakeside represents him under Posto Gang" - is a fact
    # the column does not hold and must survive.
    for setname in (fields.get("sets") or "").split("/"):
        if len(setname) > 2 and re.search(
            rf"\b(member of|of the|from the|part of|represents?)\s+(the\s+)?{re.escape(fold(setname))}\b",
            fbio,
        ):
            bad.append(f"revendique l'appartenance au set {setname!r}")
    if fields.get("gang") and re.search(
        rf"\b(is|was)\s+an?\s+{re.escape(fold(fields['gang']).rstrip('s'))}", fbio
    ):
        bad.append(f"repete la nation {fields['gang']!r}")
    for rel in fields.get("family") or []:
        if rel and re.search(
            rf"\b(brother|sister|cousin|father|son|uncle|nephew|spouse|half-brother)\s+(of|to)\s+{re.escape(fold(rel))}\b",
            fbio,
        ):
            bad.append(f"repete le lien de parente avec {rel!r}, deja dans le champ famille")
    for pat in STATUS_WORDS.get(fields.get("status"), ()):
        if re.search(pat, fbio):
            bad.append(f"repete le statut {fields['status']}")
    if len(bio) > 600:
        bad.append(f"trop long ({len(bio)} caracteres)")
    return bad


with open(SP / "bio_corpus.json") as fh:
    corpus = {c["ref"]: c for c in json.load(fh)}

total = written = clean = 0
problems = []
missing = []
for n in range(1, 11):
    path = SP / f"bio_out_{n}.json"
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
            if (e.get("bio") or "").strip():
                written += 1
            bad = check(e, src)
            if bad:
                problems.append((e["ref"], bad, e.get("bio", "")))
            else:
                clean += 1

print(f"lots manquants: {missing or 'aucun'}")
print(
    f"{total} entrees | {written} avec une bio | {clean} sans anomalie | {len(problems)} a revoir"
)
for ref, bad, bio in problems[: int(sys.argv[1]) if len(sys.argv) > 1 else 25]:
    print(f"\n  {ref}: " + "; ".join(bad))
    if bio:
        print(f"     bio: {bio[:150]}")
        src = corpus.get(ref)
        if src:
            print(f"     src: {src['sentence'][:150]}")
