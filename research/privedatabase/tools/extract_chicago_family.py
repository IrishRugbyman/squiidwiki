"""Extract family ties from the Chicago source and write them to member.family.

The site states kinship in prose ("Il est le petit frère de GBE Capo et l'oncle
de T-Slick", "Darius Jones (frère d'Eastside Ivo)"). The member seed never read
those sentences, so Chicago had 0 family links on 4,577 members. This walks the
same pages/sentences as extract_members_full.py, pulls every "<rel> de <name>
[du même set | de la <set> | (<set>)]" clause, resolves subject and object to DB
members (nickname/legal/alias, disambiguated by set), and maps the relation onto
the wiki's vocabulary (father/son, uncle/nephew, brother, cousin, spouse).

Sister/mother/daughter/niece/in-law have no key in the wiki's family model and
are reported, not written. Dry-run by default; --go PATCHes through the API,
whose update path writes the inverse link on the relative for free.

Outputs (scratch, next to nothing committed): family-links.json with every
resolved link and its source, plus the unresolved and unsupported lists.
"""

import collections
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from chiparse import HDR, QUOTE, SETHDR, VERB, lines_of, parse_member  # noqa: E402
from db_sync import candidates, norm  # noqa: E402
from extract_members_full import ADMIN_TITLES, SETDESC, good_name  # noqa: E402
from wikiapi import CHICAGO, Api, q  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(__file__).resolve().parent / "chicago-family-links.json"

# relation word -> (key written on the SUBJECT, key written on the OBJECT)
# "X est le père de Y": X.son += Y, Y.father = X.
REL = {
    "frere": ("brother", "brother"),
    "demifrere": ("brother", "brother"),
    "cousin": ("cousin", "cousin"),
    "cousine": ("cousin", "cousin"),
    "pere": ("son", "father"),
    "fils": ("father", "son"),
    "oncle": ("nephew", "uncle"),
    "neveu": ("uncle", "nephew"),
    "mari": ("spouse", "spouse"),
    "femme": ("spouse", "spouse"),
    "epoux": ("spouse", "spouse"),
    "epouse": ("spouse", "spouse"),
}
# Adjudicated by hand where the automatic match is ambiguous or the site wrote
# a name the DB does not carry verbatim. Keyed by (page id, subject as parsed,
# object as parsed) -> member id; SUBJECT_OVERRIDES by (page id, subject).
_DAYDAY_STL = "39e28373-16c3-4e7a-a6af-2438b7a1b726"  # FBG Day Day, STL/EBT
_SLUTTY = "8db58ea2-8953-4247-a7ad-407eb598745b"  # Slutty of the Slutty Boyz (O'Block)
_LIL_ANT_PT = "32c2d180-8ea5-40ca-a259-800ee26da039"  # Lil Ant on the PocketTown roster
_TAY_SAVAGE = "f0dcccba-175a-4024-813b-a20835fbff0e"  # Tay Savage on the Nicko Gang roster
SUBJECT_OVERRIDES = {
    ("4755", "D.Rose"): "3c104f29-920d-4b09-b46a-33983e85d340",  # the 600 D.Rose
    ("4749", "Lil Dee"): "f9c38939-309b-453f-b0b5-44f1d3c002a7",  # Booka's half-brother, 600
    ("1813", "By"): "3bdd5ff7-390c-45c6-8b8a-9fe426b732c2",  # Byron Berry's own page
    ("7930", "Lil Ant"): _LIL_ANT_PT,
    ("7925", "Tay Savage"): _TAY_SAVAGE,
    ("7907", "OTF NuNu ou Nuski"): "fd79b70b-c628-4c75-a8e6-ce1d2bf78daa",  # OTF Nuski
}
OBJECT_OVERRIDES = {
    ("7971", "Curt Mac", "Woo"): "c3a1ee7e-0950-4f73-97bc-33f3b442875f",  # Melly/Woo/KD, 051 YM
    ("7930", "5ive", "Lil Ant"): _LIL_ANT_PT,
    ("7930", "5ive", "051 Young Money Zeko"): "e6980bf9-b744-4211-b3c7-2ba0f3e3d380",
    ("7925", "Trey Savage", "Tay Savage"): _TAY_SAVAGE,
    ("7494", "Melly", "Cortize"): "b0b844c6-ea09-4d7e-9c49-f20bfd7e4c27",  # TYMB Cortize
    ("7494", "Fathead", "051 Montana"): "7a8d4b53-96c6-4191-b85b-b27f9837d0da",
    ("7493", "Mooda", "Lil Durk"): "d4459f34-93e9-412e-ab5a-4e23ad737d96",  # Lamron Lil Durk
    ("7493", "Raheem", "FBG Day Day"): _DAYDAY_STL,
    ("7485", "Coby", "FBG Day Day"): _DAYDAY_STL,
    ("6277", "D.Rose", "Day Day"): _DAYDAY_STL,  # cousin of FBG Duck/Brick too
    ("7487", "Kyro", "Raheem"): "4e1ec7ab-3410-4e57-b4e5-7a2ea6a94a86",  # THF 46 Raheem
    ("7486", "Skinny", "Lil Steve"): "fabe351f-866e-48c9-92f7-89743f329aa3",  # Memo's brother
    ("7485", "L.C", "007"): "197ab322-c899-4698-aa0d-7acd2ee483b2",  # 007 of Jaro City
    ("6277", "RondoNumba9", "OTF Toon"): "94939265-c831-4edb-9380-2c79ad3e110a",  # Toon, G-Ville
    ("6273", "HK", "Slutty"): _SLUTTY,
    ("6273", "T-Roy", "Slutty"): _SLUTTY,
    ("6273", "Lil Drilla", "Slutty"): _SLUTTY,
    ("7489", "Lil Durk", "Lil Mister"): "4f7e2e2b-04ca-4433-8ce3-7a0e710945c9",
}
UNSUPPORTED = {
    "soeur",
    "mere",
    "fille",
    "niece",
    "beaufrere",
    "bellesoeur",
    "grandpere",
    "grandmere",
}
RELWORD = (
    r"(?:(?:petit|grand|demi|petite|grande)[- ]?)?"
    r"(fr[èe]re|s[oœ]ur|cousine?|fils|fille|p[èe]re|m[èe]re|oncle|neveu|ni[èe]ce|mari|femme|"
    r"[ée]poux|[ée]pouse|beau-fr[èe]re|belle-s[oœ]ur|grand-p[èe]re|grand-m[èe]re)"
    r"(?:\s+jumeaux?|\s+jumelle)?"
)
# "le frère de", "l'oncle de", "Père à Tooka", "(frère d'Eastside Ivo)"
CLAUSE = re.compile(
    rf"(?:\b(?:le|la|l'|un|une|son|sa|leur)\s*|(?<=\()|^)\s*{RELWORD}\s+(?:de|d'|à)\s*", re.I
)
SENT_END = re.compile(r"\.\s+(?=[A-Z])|\.$|;|\s+\((?!frère|cousin)")
SPLIT_OBJ = re.compile(r"\s+et\s+|,\s+|\s+ainsi que\s+|\s+ou\s+|\s*&\s*")
TRAIL = re.compile(r"\s+(?:et|ainsi que|ou|&|,)\s*$")
SETQUAL = re.compile(
    r"^(?P<name>.+?)(?:\s+(?:du même set|de la même|du (?P<s1>.+)|de la (?P<s2>.+)|de l'(?P<s3>.+)|"
    r"d'(?P<s4>.+)|de (?P<s5>.+))|\s*\((?P<s6>[^)]+)\))?\s*$"
)
NOT_A_NAME = re.compile(
    r"\b(sa|son|ses|leur|petite amie|copine|famille|star|rappeur|gars|membre|victime|tueur|"
    r"enfant|qui|dont|un|une|la|le|les)\b|^\W*$",
    re.I,
)


def relkey(word):
    """Normalise a matched relation word to a REL/UNSUPPORTED key (accents folded first)."""
    w = word.lower().replace("-", "")
    for a, b in (("è", "e"), ("é", "e"), ("ê", "e"), ("œ", "oe")):
        w = w.replace(a, b)
    return norm(w)


def clauses(sentence):
    """Yield (relation word, object text) for every kinship clause in a sentence."""
    ms = list(CLAUSE.finditer(sentence))
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(sentence)
        seg = sentence[m.end() : end]
        seg = SENT_END.split(seg, 1)[0]
        yield m.group(1), seg.strip(" ,.")


def parse_objects(seg):
    """Split an object segment into (name, set_hint) pairs; set_hint 'SAME' = du même set."""
    out = []
    seg = TRAIL.sub("", seg)
    for chunk in SPLIT_OBJ.split(seg):
        chunk = re.sub(r"^(?:de\s+|d')", "", chunk.strip())
        chunk = re.sub(QUOTE, "", chunk).strip(" ,.:")
        if not chunk or len(chunk) > 40:
            continue
        m = SETQUAL.match(chunk)
        name = m.group("name").strip()
        hint = next((m.group(k) for k in ("s1", "s2", "s3", "s4", "s5", "s6") if m.group(k)), None)
        if "même set" in chunk or "de la même" in chunk:
            hint = "SAME"
        if hint:
            hint = TRAIL.sub("", hint).strip(" .,")
        if NOT_A_NAME.search(name) or not good_name(name):
            continue
        out.append((name, hint))
    return out


# ---------------------------------------------------------------------------
# DB index
members = q(
    f"""SELECT m.id, m.nickname, m.legal_name, m.aliases, m.family, m.alliance_id::text AS alliance_id,
               coalesce((SELECT json_agg(ms.set_id::text) FROM member_set ms WHERE ms.member_id=m.id),'[]') AS set_ids
        FROM member m WHERE m.universe_id='{CHICAGO}'"""
)
by_id = {m["id"]: m for m in members}
name_idx = collections.defaultdict(set)
for m in members:
    for n in [m["nickname"], m["legal_name"], *(m["aliases"] or [])]:
        if n and norm(n):
            name_idx[norm(n)].add(m["id"])
setidx = {}
set_name = {}
for r in q(
    f"SELECT id, name, coalesce(name_variants,'[]'::jsonb) nv FROM sets WHERE universe_id='{CHICAGO}'"
):
    set_name[r["id"]] = r["name"]
    for k in candidates(r["name"]):
        setidx.setdefault(k, r["id"])
    for v in r["nv"] or []:
        for k in candidates(v.get("name", "")):
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
    n = norm(t)
    if len(n) >= 4:
        pre = {sid for k, sid in setidx.items() if k.startswith(n)}
        if len(pre) == 1:
            return pre.pop()
    return None


PREFIX = re.compile(r"^(OTF|FBG|THF|GBE|MOB|TTB|KTS|STL|NLMB|MuBu|TYMB|BD|GD|PBG|CMB)\s+(.+)$")


def tag_sets(tag):
    """Sets of the members who carry this tag in their nickname ("FBG Duck" -> STL/EBT)."""
    out = collections.Counter()
    for m in members:
        if (m["nickname"] or "").upper().startswith(tag.upper() + " "):
            for sid in m["set_ids"]:
                out[sid] += 1
    return {sid for sid, c in out.items() if c >= 2}


def resolve_member(name, set_hint=None, context_sets=()):
    """Name (+ set hint, + sets of the related subject) -> (member id | None, why)."""
    cands = set(name_idx.get(norm(name), ()))
    if not cands:
        pm = PREFIX.match(name)
        if pm and name_idx.get(norm(pm.group(2))):
            tag, base = pm.group(1), pm.group(2)
            sid = resolve_set(tag)
            hsid = resolve_set(set_hint) if set_hint and set_hint != "SAME" else None
            tsets = {sid} if sid else tag_sets(tag)
            if hsid:
                tsets = {hsid}
            narrowed = {c for c in name_idx[norm(base)] if set(by_id[c]["set_ids"]) & tsets}
            if len(narrowed) == 1:
                return narrowed.pop(), f"tag {tag}"
            return None, f"tag {tag}: {len(narrowed) or len(name_idx[norm(base)])} candidates"
        # "Duck" for "FBG Duck": a one-token tag dropped, recoverable when the
        # set hint or the subject's own set leaves exactly one such member.
        # Only an all-caps set tag (FBG, MOB, OTF): "Lil"/"Big" make a different person.
        tagged = {
            m["id"]
            for m in members
            if re.match(rf"^[A-Z0-9]{{2,5}}\s+{re.escape(name)}$", m["nickname"] or "")
        }
        if tagged:
            hsid = resolve_set(set_hint) if set_hint and set_hint != "SAME" else None
            ctx = {hsid} if hsid else set(context_sets)
            narrowed = {c for c in tagged if set(by_id[c]["set_ids"]) & ctx}
            if len(narrowed) == 1:
                return narrowed.pop(), "tag dropped"
        return None, "no such name"
    if len(cands) == 1:
        return cands.pop(), "unique"
    sid = resolve_set(set_hint) if set_hint and set_hint != "SAME" else None
    if set_hint == "SAME":
        sid = None
        narrowed = {c for c in cands if set(by_id[c]["set_ids"]) & set(context_sets)}
    elif sid:
        narrowed = {c for c in cands if sid in by_id[c]["set_ids"]}
    else:
        narrowed = {c for c in cands if set(by_id[c]["set_ids"]) & set(context_sets)}
    if len(narrowed) == 1:
        return narrowed.pop(), "set-narrowed"
    # Several rows survive: prefer the one whose nickname IS the name over
    # alias-only matches ("007" over "FYB DJ" a/k/a 007).
    pool = narrowed or cands
    exact = {c for c in pool if norm(by_id[c]["nickname"]) == norm(name)}
    if len(exact) == 1 and (narrowed or len(pool) == len(exact) + 0):
        return exact.pop(), "exact nickname"
    if set_hint and set_hint != "SAME" and sid is None:
        return None, f"set hint {set_hint!r} unknown, {len(cands)} candidates"
    return None, f"ambiguous ({len(cands)} candidates)"


# ---------------------------------------------------------------------------
# Walk the source
owner = json.loads((ROOT / "tools/wp-owner.json").read_text())
alliance_pages = set(json.loads((ROOT / "tools/chi-alliance-pages.json").read_text()))
pages = [
    p
    for p in json.loads((ROOT / "raw/pages.json").read_text())
    if owner.get(p["slug"]) == "chicago"
]

people = json.loads((ROOT / "tools/extract-chicago-people.json").read_text())
page_subject_set = {}  # person page id -> set title recorded for its subject
for rec in people:
    if "person-page" in rec["origins"] and rec["set"]:
        for pid in rec["pages"]:
            page_subject_set.setdefault(pid, rec["set"])

links = []  # dicts: a, b, a_key, b_key, rel, subject, object, page
unresolved = []
unsupported = collections.Counter()
seen_pairs = set()


def subject_sets(mid):
    """Set ids of a resolved member (for 'du même set' and same-set tie-breaks)."""
    return by_id[mid]["set_ids"]


def emit(subj_id, word, obj_name, obj_hint, src):
    """Resolve the object and record one link, or why it failed."""
    key = relkey(word)
    if key in UNSUPPORTED:
        unsupported[key] += 1
        return
    if key not in REL:
        return
    ctx = subject_sets(subj_id)
    obj_id, why = OBJECT_OVERRIDES.get((src["page"], src["subject"], obj_name)), "override"
    if not obj_id:
        obj_id, why = resolve_member(obj_name, obj_hint, ctx)
    if not obj_id:
        unresolved.append({**src, "object": obj_name, "hint": obj_hint, "why": why})
        return
    if obj_id == subj_id:
        return
    s_key, o_key = REL[key]
    pair = tuple(sorted([(subj_id, s_key), (obj_id, o_key)]))
    if pair in seen_pairs:
        return
    seen_pairs.add(pair)
    links.append(
        {
            "a": subj_id,
            "b": obj_id,
            "a_key": s_key,
            "b_key": o_key,
            **src,
            "object": obj_name,
            "hint": obj_hint,
            "why": why,
        }
    )


def handle_sentence(subj_name, subj_set_title, sentence, page):
    """Resolve the subject and emit every kinship clause in the sentence."""
    cls = list(clauses(sentence))
    if not cls:
        return
    sid = resolve_set(subj_set_title) if subj_set_title else None
    subj_id, why = SUBJECT_OVERRIDES.get((str(page["ID"]), subj_name)), "override"
    if not subj_id:
        subj_id, why = resolve_member(subj_name, subj_set_title, [sid] if sid else ())
    src = {
        "page": str(page["ID"]),
        "title": page["title"],
        "subject": subj_name,
        "sentence": sentence[:200],
    }
    if not subj_id:
        unresolved.append({**src, "object": None, "hint": None, "why": f"subject: {why}"})
        return
    for word, seg in cls:
        for obj_name, hint in parse_objects(seg):
            emit(subj_id, word, obj_name, hint, {**src, "rel": word})


for p in pages:
    if p["title"].strip().upper() in ADMIN_TITLES:
        continue
    L = lines_of(p)
    if not L:
        continue
    title = re.sub(r"\s+", " ", p["title"]).strip()
    is_set_page = bool(SETDESC.search(L[0])) or any(SETHDR.match(x) for x in L)
    is_alliance_page = str(p["ID"]) in alliance_pages
    page_set = title if (is_set_page and not is_alliance_page) else None
    start = 1
    if not is_set_page and not is_alliance_page:
        if not VERB.search(L[0]):
            continue
        subject = parse_member(L[0])
        if not good_name(subject["name"]):
            continue
        m = re.search(
            r"membre (?:officiel )?(?:du|de la|de l'|des)\s+([A-Z][\w$./'\- ]{1,25})", L[0]
        )
        subj_set = m.group(1).strip().rstrip(".") if m else page_subject_set.get(str(p["ID"]))
        handle_sentence(subject["name"], subj_set, L[0], p)
        # the rest of a person page keeps talking about the subject
        for line in L[1:]:
            if SETHDR.match(line) or HDR.match(line):
                break
            if VERB.search(line) and re.match(r"^(Il|Elle|C')\b", line):
                handle_sentence(subject["name"], subj_set, line, p)
        continue
    for line in L[start:]:
        if SETHDR.match(line) or HDR.match(line):
            continue
        if VERB.search(line) and (len(line) > 24 or re.search(r"\b(est|était)\s+une?\b", line)):
            m = parse_member(line)
            if good_name(m["name"]):
                handle_sentence(m["name"], page_set, line, p)
            continue
        # roster / bodies entries: "Darius Jones (frère d'Eastside Ivo)"
        pm = re.match(r"^([^()]{2,34}?)\s*\(([^()]*)\)", line)
        if pm and CLAUSE.search(pm.group(2)):
            handle_sentence(pm.group(1).strip(), page_set, pm.group(2), p)


# ---------------------------------------------------------------------------
# Report
def label(mid):
    """'Nickname [Set/Set]' for the report."""
    m = by_id[mid]
    sets = "/".join(set_name.get(s, "?") for s in m["set_ids"]) or "-"
    return f"{m['nickname'] or m['legal_name']} [{sets}]"


print(f"{len(links)} links, {len(unresolved)} unresolved, unsupported={dict(unsupported)}\n")
for lk in links:
    print(
        f"  {label(lk['a']):40} {lk['a_key']:>7} -> {lk['b_key']:<7} {label(lk['b']):40} p{lk['page']} ({lk['rel']} de {lk['object']}{' / ' + lk['hint'] if lk['hint'] else ''}) [{lk['why']}]"
    )
print("\nUNRESOLVED")
for u in unresolved:
    print(
        f"  p{u['page']} {u['title'][:24]:24} subj={u['subject']!r:22} obj={u['object']!r:22} hint={u['hint']!r:14} {u['why']}"
    )
    if "ambiguous" in u["why"] or "candidates" in u["why"]:
        nm = u["object"] if u["object"] else u["subject"]
        pm = PREFIX.match(nm)
        key = norm(pm.group(2)) if pm and not name_idx.get(norm(nm)) else norm(nm)
        for c in sorted(name_idx.get(key, ()), key=label):
            print(f"        - {c} {label(c)} {by_id[c].get('status', '')}")
        print(f"        sentence: {u['sentence'][:160]}")
OUT.write_text(
    json.dumps(
        {"links": links, "unresolved": unresolved, "unsupported": unsupported},
        ensure_ascii=False,
        indent=1,
    )
)

if "--go" not in sys.argv:
    print("\nDRY RUN - re-run with --go to write through the API")
    sys.exit()

# ---------------------------------------------------------------------------
# Apply. One PATCH per subject with the merged dict; the API writes the inverse
# on the relative, so later PATCHes must re-read before merging.
api = Api()
wanted = collections.defaultdict(lambda: collections.defaultdict(set))  # mid -> key -> ids
for lk in links:
    wanted[lk["a"]][lk["a_key"]].add(lk["b"])
    wanted[lk["b"]][lk["b_key"]].add(lk["a"])
patched = conflicts = 0
for mid, keys in wanted.items():
    cur = api.call("GET", f"members/{mid}?universe_id={CHICAGO}")
    fam = dict((cur or {}).get("family") or {})
    changed = False
    for key, ids in keys.items():
        if key == "father":
            have = fam.get("father")
            if have and have not in ids or len(ids) > 1:
                conflicts += 1
                print(f"  father conflict on {label(mid)}: has {have}, wants {ids}")
                continue
            if not have:
                fam["father"] = next(iter(ids))
                changed = True
        else:
            have = fam.get(key)
            have = set(have) if isinstance(have, list) else {have} if have else set()
            new = have | ids
            if new != have:
                fam[key] = sorted(new)
                changed = True
    if not changed:
        continue
    r = api.call("PATCH", f"members/{mid}?universe_id={CHICAGO}", {"family": fam})
    if r and r.get("_error"):
        print("  PATCH failed:", label(mid), r)
    else:
        patched += 1
print(f"\npatched {patched} members, {conflicts} father conflicts skipped")
