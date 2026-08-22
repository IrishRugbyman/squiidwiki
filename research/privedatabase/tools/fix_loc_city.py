"""Un-swap the two LOC City sets and drop the parentheses from their names.

The site has two sets it explicitly tells you not to confuse:

  p7954 "LOC CITY"        - "un set de Gangster et de Black Disciples a Rogers
                             Park", also known as 1212, MMG, Jeffery Boyz, Get
                             Rich, Blake Block, Montana Gang, Keno World, Munchie
                             Gang, Lawless. 312 lines, the big one.
  p450 / p7991 "LOC CITY (BotY)" - Back of the Yards, "a ne pas confondre avec le
                             LOC City dans le Nord de Chicago". 28 lines.

Both titles reduce to the same comparison key `loccity`, so `resolve_set` sent
every unqualified sighting to whichever set registered that key first. The result
is inverted: the row NAMED "LOC City (Back of the Yards)" holds the 105 members
and 15 relationships that come from the Rogers Park page, while the row named
"LOC City (Rogers Park)" holds two Rogers Park men and nothing else - but carries
the Rogers Park name variants.

This relabels each row to match the content it actually holds, drops the
parenthetical from both names, and moves the members that sit on the wrong one.

Dry-run by default; --go applies.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from wikiapi import CHICAGO, Api, q  # noqa: E402

BIG = "2360bdc3-8b8b-4518-8c59-b58fff3e45d8"  # named "(Back of the Yards)", holds Rogers Park
SMALL = "0e09aeea-f1aa-4af5-8692-4d55cd36cf44"  # named "(Rogers Park)", holds almost nothing

ROGERS_PARK_VARIANTS = [
    "LOC City",
    "LOC CITY",
    "1212",
    "MMG",
    "Jeffery Boyz",
    "Get Rich",
    "Blake Block",
    "Montana Gang",
    "Keno World",
    "Munchie Gang",
    "Lawless",
]
# Deliberately NOT "LOC CITY (BotY)": candidates() derives a title-minus-parenthetical
# key from every variant, so that string would register the bare `loccity` key on this
# row and re-create the exact collision this script exists to undo.
BOTY_VARIANTS = ["LOC City BotY", "BotY", "Back of the Yards"]

# Named only on a "LOC City BotY" list in the source, so they belong to the small
# set once it is relabelled. ChiefLocMoney, Heado, Mon and Rico appear on BOTH
# source lists and are deliberately left on the big set - splitting them would
# need evidence that they are two different men, which the source does not give.
BOTY_MEMBERS = ["Buck", "GlockBoy BoBo", "GlockBoy KO", "GPap", "Lil Steve", "Roc", "Tra'Don"]
# Rogers Park men currently stranded on the small set.
RP_MEMBERS = ["Chubbz", "Joe Crack"]

# The bios were swapped along with the labels.
RP_BIO = (
    "A set of Gangster Disciples and Black Disciples in Rogers Park. LOC stands for "
    "Loyalty Over Cash. Also known as 1212, MMG, Jeffery Boyz, Get Rich, Blake Block, "
    "Montana Gang, Keno World, Munchie Gang and Lawless."
)
BOTY_BIO = (
    "A set of Gangster Disciples in Back of the Yards. Not to be confused with the LOC "
    "City in North Chicago, which is unrelated. Merged with DamenVille and W.B 057."
)

# Relationships the BotY page states (p7991, p450) but which sit on the big row.
# PottBlock, SedVille, 5th Ward Life and Jaro City come from neither LOC City page
# and are left where they are.
BOTY_RELATIONS = [
    ("DamenVille", "FRIEND"),
    ("W.B", "FRIEND"),
    ("JackBoys", "ENEMY"),
    ("LordsVille", "ENEMY"),
    ("MurdaField", "ENEMY"),
]


def variants(names):
    """Name-variant rows, first one primary."""
    return [
        {"name": n, "is_primary": i == 0, "lead": None, "number": None, "initials": None}
        for i, n in enumerate(names)
    ]


sets = {r["id"]: r for r in q(f"SELECT id, name FROM sets WHERE universe_id='{CHICAGO}'")}
if BIG not in sets or SMALL not in sets:
    sys.exit("les deux sets LOC City ne sont plus la - rien fait")

moves = []
for nick, src, dst, label in (
    *[(n, BIG, SMALL, "-> LOC City BotY") for n in BOTY_MEMBERS],
    *[(n, SMALL, BIG, "-> LOC City") for n in RP_MEMBERS],
):
    rows = q(
        f"""SELECT m.id, m.nickname FROM member m JOIN member_set ms ON ms.member_id=m.id
            WHERE m.universe_id='{CHICAGO}' AND ms.set_id='{src}'
              AND m.nickname='{nick.replace("'", "''")}'"""
    )
    if len(rows) != 1:
        print(f"  ! {nick!r}: {len(rows)} lignes sur le set source, ignore")
        continue
    moves.append((rows[0]["id"], rows[0]["nickname"], src, dst, label))

print(
    f"{sets[BIG]['name']!r}  ({q(f'SELECT count(*) n FROM member_set WHERE set_id={chr(39)}{BIG}{chr(39)}')[0]['n']} membres)  ->  'LOC City'"
)
print(
    f"{sets[SMALL]['name']!r}  ({q(f'SELECT count(*) n FROM member_set WHERE set_id={chr(39)}{SMALL}{chr(39)}')[0]['n']} membres)  ->  'LOC City BotY'"
)
print(f"\ndeplacements ({len(moves)}):")
for _mid, nick, _src, _dst, label in moves:
    print(f"   {nick!r:16} {label}")

if "--go" not in sys.argv:
    print("\nDRY RUN - relancez avec --go")
    sys.exit()

api = Api()
for sid, name, vs, bio in (
    (BIG, "LOC City", ROGERS_PARK_VARIANTS, RP_BIO),
    (SMALL, "LOC City BotY", BOTY_VARIANTS, BOTY_BIO),
):
    r = api.call(
        "PATCH",
        f"sets/{sid}?universe_id={CHICAGO}",
        {"name": name, "name_variants": variants(vs), "bio": bio},
    )
    print(f"renomme {name!r}: {'ok' if not (r or {}).get('_error') else r}")

# The BotY page states its own allies and enemies; they sit on the big row.
for target_name, kind in BOTY_RELATIONS:
    rows = q(f"SELECT id FROM sets WHERE universe_id='{CHICAGO}' AND name='{target_name}'")
    if len(rows) != 1:
        print(f"  ! relation {target_name!r}: {len(rows)} sets de ce nom, ignore")
        continue
    tid = rows[0]["id"]
    api.call("DELETE", f"sets/{BIG}/relationships/{tid}?universe_id={CHICAGO}")
    a = api.call(
        "POST",
        f"sets/{SMALL}/relationships?universe_id={CHICAGO}",
        {"target_id": tid, "type": kind},
    )
    print(f"  relation {target_name} ({kind}): {'deplacee' if not (a or {}).get('_error') else a}")

for mid, nick, src, dst, _label in moves:
    cur = api.call("GET", f"members/{mid}?universe_id={CHICAGO}")
    aff = [
        {
            "set_id": a["set_id"],
            "rank": a.get("rank"),
            "is_primary": a.get("is_primary", False),
            "from_date": a.get("from_date"),
        }
        for a in (cur or {}).get("affiliations", [])
        if a["set_id"] != src
    ]
    aff.append({"set_id": dst, "is_primary": not any(a["is_primary"] for a in aff)})
    r = api.call("PATCH", f"members/{mid}?universe_id={CHICAGO}", {"affiliations": aff})
    print(f"  {nick!r}: {'deplace' if not (r or {}).get('_error') else r}")
