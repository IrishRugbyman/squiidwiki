import html
import re


def lines_of(p):
    """Strip HTML tags/links from a page's content and return its non-empty, stripped lines."""
    c = p["content"]
    c = re.sub(r"<br\s*/?>", "\n", c)
    # </li> matters as much as </p>: the site puts every roster and kill-list
    # entry in its own <li>, so dropping it glues names into one string and no
    # amount of regex afterwards can tell "Joc Da Block" from "Wayne" again.
    c = re.sub(r"</p>|</div>|</h\d>|</li>|</ol>|</ul>|</tr>|</td>", "\n", c)
    t = html.unescape(re.sub("<[^>]+>", "", c))
    t = re.sub(r"https?://\S+", "", t)
    t = t.replace("\xa0", " ").replace("’", "'")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    return [line.strip() for line in t.strip().splitlines() if line.strip()]


HDR = re.compile(
    r"^(ASSISTANCE\(S\)|ASSISTANCES?|FUSIL?LADES?(?:\(S\))?(?: IMPORTANTES?(?:\(S\))?)?|CORPS|BLESS[EÉ]E?S?)\s*:\s*$",
    re.I,
)
SETHDR = re.compile(
    r"^(ALLI[EÉ]S|ENNEMIS|MEMBRES(?: IMPORTANTS?)?|LISTE DES MEMBRES|LISTE DES CORPS DU SET|LISTE DES CORPS DE L\'ALLIANCE|CORPS IMPORTANTS?(?:\(S\))?)\s*:\s*(.*)$",
    re.I,
)
SKIP = re.compile(r"^\(?\s*(PAS DE PHOTO|AUCUNE PHOTO|PHOTO)\s*\)?\.?$", re.I)
SETKEY = {
    "alliés": "allies",
    "allies": "allies",
    "ennemis": "enemies",
    "membres": "members_listed",
    "membres importants": "members_listed",
    "liste des membres": "members_listed",
    "liste des corps du set": "set_bodies",
    "liste des corps de l'alliance": "set_bodies",
    "corps importants": "set_bodies",
    "corps important(s)": "set_bodies",
    "corps important": "set_bodies",
}


def keyof(h):
    """Map a matched section header to its normalized section key."""
    h = h.lower().strip()
    if h.startswith("assistance"):
        return "assists"
    if h.startswith("fusillade"):
        return "shootings"
    if h.startswith("corps"):
        return "bodies"
    if h.startswith("bless"):
        return "wounded"
    return "other"


NATION = re.compile(
    r"(Gangster Disciples?|Black Disciples?|Black P\.?\s?Stones?|Four Corner Hustlers?|Vice Lords?|Latin Kings?|Mickey Cobras?)",
    re.I,
)
ALIAS = re.compile(r"[«\"“]\s*([^»\"”]+?)\s*[»\"”]")

MARK = [
    ("nations", r"est une? set de|est une? sets? de|sont des"),
    ("allies", r"fusionn[ée]s? avec|alli[ée]s? avec|cliqued up avec"),
    ("enemies_direct", r"ennemis directs? avec"),
    ("enemies", r"ennemis avec"),
    ("beef", r"en embrouille avec"),
]


def _clean(seg):
    parts = re.split(r",|\bet\b|\bainsi que\b|\bou\b", seg, flags=re.I)
    out = []
    for x in parts:
        x = re.sub(r"^\s*(?:de\s+)?(?:l'|d')\s*", "", x.strip(), flags=re.I)
        x = re.sub(r"^\s*(?:de\s+)?(?:quelques|le|la|les|du|des|un|une)\s+", "", x, flags=re.I)
        x = re.sub(r"^\s*(?:de|d')\s+", "", x, flags=re.I)
        x = re.sub(r"\s+", " ", x).strip(" ,.;:")
        if x and len(x) < 40:
            out.append(x)
    return out


def parse_desc(desc):
    """Extract nation/allies/enemies/beef mentions from a page's description line using MARK patterns."""
    out = {k: [] for k, _ in MARK}
    hits = []
    for key, pat in MARK:
        for m in re.finditer("(?:" + pat + ")", desc, re.I):
            hits.append((m.start(), m.end(), key))
    hits.sort()
    for i, (_s, e, key) in enumerate(hits):
        end = hits[i + 1][0] if i + 1 < len(hits) else len(desc)
        seg = desc[e:end]
        seg = re.split(r"\.\s|\.$", seg)[0]
        if not out[key]:
            out[key] = _clean(seg)
    return out


# An entry line is a run of "Name (Set)" pairs. A member line is a sentence and
# carries a verb. Entry blocks can span several lines, so consume while it still
# looks like entries instead of taking exactly one.
VERB = re.compile(r"\b(est|était|etait|sont|étaient)\b", re.I)


def looks_like_entries(line):
    """Return whether a line looks like a run of "Name (Set)" entries rather than a member sentence."""
    return bool(re.search(r"\([^)]*\)", line)) and not VERB.search(line)


def entries(line):
    """Split a line into individual "Name (Set)" entries, falling back to a comma/semicolon split."""
    got = re.findall(r"[^()]+\([^()]*\)", line)
    if got:
        return [re.sub(r"\s+", " ", g).strip(" ,;") for g in got if g.strip()]
    return [re.sub(r"\s+", " ", x).strip() for x in re.split(r",|;", line) if x.strip()]


def parse_member(line):
    """Parse a member sentence into a dict with name, aliases, nation, and dead/locked flags."""
    m = {"raw": line}
    nm = re.split(
        r"\s+(?:est|était|etait)\s+(?:un|une)\b|,\s*aussi connue?\s|\s+ou\s+[«\"“]", line
    )[0]
    m["name"] = nm.strip(" ,.")[:60]
    m["aliases"] = [x for x in ALIAS.findall(line) if x.lower() != m["name"].lower()]
    n = NATION.search(line)
    m["nation"] = n.group(1) if n else ""
    m["dead"] = bool(re.search(r"décédée?|est morte?|a été tué", line, re.I))
    m["locked"] = bool(re.search(r"incarcéré|en prison", line, re.I))
    return m


def parse_page(p):
    """Parse a page's lines into a description, set/member relationships, and list of members."""
    L = lines_of(p)
    if not L:
        return None
    # Heterogeneous by design: "desc" is a str, everything else a list.
    out: dict[str, object] = {"desc": L[0]}
    out.update(parse_desc(L[0]))
    out["members"] = []
    out["members_listed"] = []
    out["set_bodies"] = []
    cur = None
    sect = None
    setsect = None
    taken = 0
    staken = 0
    for line in L[1:]:
        if SKIP.match(line):
            continue
        sh = SETHDR.match(line)
        if sh:
            setsect = SETKEY.get(sh.group(1).lower().strip())
            sect = None
            cur = None
            staken = 0
            rest = sh.group(2).strip()
            if rest and setsect:
                out.setdefault(setsect, []).extend(
                    entries(rest) if setsect != "allies" and setsect != "enemies" else _clean(rest)
                )
                setsect = None
            continue
        if setsect:
            if staken == 0 or looks_like_entries(line):
                if setsect in ("allies", "enemies"):
                    out[setsect] = (out.get(setsect) or []) + _clean(line)
                else:
                    out.setdefault(setsect, []).extend(entries(line))
                staken += 1
                continue
            setsect = None
            staken = 0
        h = HDR.match(line)
        if h:
            sect = keyof(h.group(1))
            taken = 0
            continue
        if sect is not None and cur is not None:
            # First line after a header is always entries. Later lines only if
            # they still look like entries - otherwise it is the next member.
            if taken == 0 or looks_like_entries(line):
                cur.setdefault(sect, []).extend(entries(line))
                taken += 1
                continue
            sect = None
            taken = 0
        sect = None
        taken = 0
        cur = parse_member(line)
        out["members"].append(cur)
    return out
