"""Seed the Henry Ford High School shooting of 16 October 2008 into Metro Detroit.

Christopher Walker, 16, of FOE Life, shot dead outside Henry Ford High School;
Kejuana McCants, Maleek Slater and Leon Merriweather wounded. William Morton
(BCB), 15, convicted of first-degree murder and sentenced to life.

Two primary sources, both HIGH:

  People v Morton, No. 294823, and People v Bell, No. 295573 (Mich Ct App,
  24 May 2012, unpublished), on appeal from Wayne Circuit LC No. 08-018563-FC.
  Recites the trial evidence. Its footnote 3 is the reason this seed exists:
  it expands BCB as "Burgess, Chapel, Blackstone Across Lahser" and names
  FOE-Life ("Family Over Everything") as the victim's set, which settles that
  FOE Life is distinct from PBF.

  MDOC/OTIS offender 744816, William Morton. Gives the date of birth that puts
  him at 15 on the day, the life sentence, and a chest tattoo reading "7 mile
  with two people both holding guns dressed in red with the initials BCB".

Morton is already on file as the member "J-Nutty"; this fills in his legal
name, MDOC number and date of birth, and attaches his OTIS photo.

**No aliases are written.** OTIS lists "William Boden Morton", "William James
Boden Morton" and "William James Morton", and the court caption gives Bell as
"a/k/a Devon Cheo Bell", but those are spelling variants of a legal name the
page already renders. `aliases` is for names the street actually uses, and
filling it with record variants prints a meaningless a/k/a line. The variants
live in the OTIS source notes instead.

Nothing is written to a biography. Set, status, dates, legal name and the
death incident are all columns, and nothing survives the strip.

Idempotent: every create checks for an existing row first. Dry-run by default;
--go writes through the local API on :8001 against the prod DB.
"""

import json
import mimetypes
import pathlib
import sys
import urllib.error
import urllib.request
import uuid

sys.path.insert(0, "/home/lbzgiu/squiidape/squiidwiki/research/privedatabase/tools")
from wikiapi import API, Api, q  # noqa: E402

U = "4f57cae1-ebfe-408c-b435-052e2bd0ca45"  # Metro Detroit
BCB = "60fe33e2-d257-4821-a09c-5e6b23ce617f"
UNKNOWN_SET = "f4bfd8ab-c0ce-458f-93eb-8d741109b077"
DETROIT_MUNI = "55d40a23-fdbe-4e83-b5b0-5670a04df4c9"
MORTON = "19f97690-f2eb-427a-9024-38e05ef72236"  # existing member "J-Nutty"

PHOTO = pathlib.Path(
    "/tmp/claude-1000/-home-lbzgiu-squiidwiki/"
    "4e0c90be-ff2d-453e-aa9b-764467c440bb/scratchpad/mdoc-744816.jpg"
)
PHOTO_CAPTION = "MDOC OTIS offender photo, 2 August 2024"

DATE = {"year": 2008, "month": 10, "day": 16, "precision": "YMD", "approx": False}

OPINION = {
    "universe_id": U,
    "url": (
        "https://www.courts.michigan.gov/4a349e/siteassets/case-documents/"
        "uploads/opinions/final/coa/20120524_c294823_41_294823.opn.pdf"
    ),
    "title": "People v Morton, No. 294823; People v Bell, No. 295573 (Mich Ct App, 24 May 2012)",
    "publication": "Michigan Court of Appeals",
    "published_at": {"year": 2012, "month": 5, "day": 24, "precision": "YMD", "approx": False},
    "accessed_at": "2026-08-25",
    "reliability": "HIGH",
    "notes": (
        "Unpublished per curiam opinion consolidating the appeals of William Morton and "
        "Devon Bell from Wayne Circuit LC No. 08-018563-FC, affirming both. Recites the "
        "trial evidence for the 16 October 2008 shooting outside Henry Ford High School. "
        "Footnote 3 expands BCB-AL as 'Burgess, Chapel, Blackstone Across Lahser' and "
        "identifies the victim as a member of FOE-Life ('Family Over Everything'). "
        "Codefendant Derryck Brantley was acquitted of all charges. The caption gives "
        "Bell as 'a/k/a Devon Cheo Bell'."
    ),
}

OTIS = {
    "universe_id": U,
    "url": "https://mdocweb.state.mi.us/OTIS2",
    "title": "MDOC OTIS offender 744816, William Morton",
    "publication": "Michigan Department of Corrections",
    "accessed_at": "2026-08-25",
    "reliability": "HIGH",
    "notes": (
        "Offender profile. Date of birth 8 January 1993, which puts him at 15 on the day "
        "of the offence. Five active prison sentences on court file 08018563-03-FC, all "
        "dated 15 October 2009: first-degree premeditated murder (MCL 750.316A) LIFE to "
        "LIFE, three counts of assault with intent to commit murder (MCL 750.83) 15 to 25 "
        "years each, and felony firearm (MCL 750.227BA) 2 years. Held at Saginaw "
        "Correctional Facility, security level II. SID 3534045J. Marks include a chest "
        "tattoo of '7 mile with two people both holding guns dressed in red with the "
        "initials BCB'. Recorded name variants: William Boden Morton, William James Boden "
        "Morton, William James Morton."
    ),
}

FOE_BIO = (
    "Family Over Everything. A northwest Detroit set opposed to BCB, and one of the four "
    "component sets of the Band Crew association alongside CMH, YNC and PBF. Distinct from "
    "PBF, with which it is sometimes conflated."
)

NARRATIVE = (
    "Christopher Walker and William Morton, of rival sets, fought with fists at Henry Ford "
    "High School earlier in the day; no weapons were seen. Between the fight and the "
    "shooting Morton was on his phone and students at the school were saying it was time "
    "for gun play. Morton was seen with weapons outside the school shortly before, and was "
    "seen firing toward a group of students; one account had him firing from outside a "
    "black Mazda into the crowd. At least two weapons were used, an assault rifle and a "
    "handgun. Walker was killed. Kejuana McCants, Maleek Slater and Leon Merriweather were "
    "wounded. Gunshot primer residue taken from Morton that evening tested positive. Text "
    "messages set out a plan to gather BCB members at the school against FOE Life in "
    "retribution for a dead friend, To-To."
)

# nickname, legal_name, set (None -> FOE Life), status
PEOPLE = [
    ("Chris", "Christopher Walker", None, "DEAD"),
    ("To-To", None, BCB, "DEAD"),
    (None, "Kejuana McCants", UNKNOWN_SET, "UNKNOWN"),
    (None, "Maleek Slater", UNKNOWN_SET, "UNKNOWN"),
    (None, "Leon Merriweather", UNKNOWN_SET, "UNKNOWN"),
    ("D", "Devon Bell", UNKNOWN_SET, "LOCKED"),
    (None, "Derryck Brantley", UNKNOWN_SET, "FREE"),
]

GO = "--go" in sys.argv


def one(sql):
    """Run a query and return its first row, or None."""
    r = q(sql)
    return r[0] if r else None


def upload(token, member_id):
    """POST the OTIS mugshot as multipart/form-data to /media/."""
    boundary = "----squiidwiki" + uuid.uuid4().hex
    ctype = mimetypes.guess_type(PHOTO.name)[0] or "image/jpeg"
    fields = {"universe_id": U, "member_id": member_id, "caption": PHOTO_CAPTION}
    body = b""
    for k, v in fields.items():
        body += (
            f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'
        ).encode()
    body += (
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
        f'filename="{PHOTO.name}"\r\nContent-Type: {ctype}\r\n\r\n'
    ).encode()
    body += PHOTO.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{API}/media/",
        method="POST",
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {token}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as x:
            print("  uploaded:", json.loads(x.read())["id"])
    except urllib.error.HTTPError as e:
        sys.exit(f"  upload failed: {e.code} {e.read()[:300].decode(errors='replace')}")


def participants(ids):
    """Build the seven participant rows for the incident."""
    return [
        {
            "member_id": MORTON,
            "role": "SHOOTER",
            "outcome": "UNHARMED",
            "notes": (
                "Convicted of first-degree premeditated murder, three counts of assault "
                "with intent to commit murder and felony firearm; sentenced to life."
            ),
        },
        {"member_id": ids["Christopher Walker"], "role": "VICTIM", "outcome": "KILLED"},
        {"member_id": ids["Kejuana McCants"], "role": "VICTIM", "outcome": "INJURED"},
        {"member_id": ids["Maleek Slater"], "role": "VICTIM", "outcome": "INJURED"},
        {"member_id": ids["Leon Merriweather"], "role": "VICTIM", "outcome": "INJURED"},
        {
            "member_id": ids["Devon Bell"],
            "role": "ASSISTED",
            "outcome": "UNHARMED",
            "notes": "Convicted of second-degree murder and felony firearm; affirmed.",
        },
        {
            "member_id": ids["Derryck Brantley"],
            "role": "ASSISTED",
            "outcome": "UNHARMED",
            "acquitted": True,
            "notes": "Acquitted of all charges at the joint trial.",
        },
    ]


def main():
    """Seed sources, the FOE Life set, the people, the incident and Morton's photo."""
    api = Api() if GO else None

    def post(path, payload):
        if not GO:
            print(f"  POST {path}  {json.dumps(payload)[:130]}")
            return {"id": str(uuid.uuid4())}
        r = api.call("POST", path, payload)
        if isinstance(r, dict) and r.get("_error"):
            sys.exit(f"POST {path} failed: {r['_error']} {r['_body']}")
        return r

    def patch(path, payload):
        if not GO:
            print(f"  PATCH {path}  {json.dumps(payload)[:130]}")
            return None
        r = api.call("PATCH", path, payload)
        if isinstance(r, dict) and r.get("_error"):
            sys.exit(f"PATCH {path} failed: {r['_error']} {r['_body']}")
        return r

    print("== sources")
    src_ids = []
    for s in (OPINION, OTIS):
        url = s["url"].replace("'", "''")
        row = one(f"SELECT id FROM source WHERE universe_id='{U}' AND url='{url}'")
        if row:
            print(f"  exists: {s['title'][:58]}")
            src_ids.append(row["id"])
        else:
            src_ids.append(post("sources/", s)["id"])
    opinion_id, otis_id = src_ids

    print("== FOE Life set")
    row = one(f"SELECT id FROM sets WHERE universe_id='{U}' AND name='FOE Life'")
    if row:
        foe = row["id"]
        print("  exists")
    else:
        foe = post(
            "sets/",
            {
                "universe_id": U,
                "name": "FOE Life",
                "name_variants": [{"name": "Family Over Everything"}, {"name": "FOE-Life"}],
                "bio": FOE_BIO,
                "status": "ACTIVE",
                "municipality_id": DETROIT_MUNI,
                "enemy_ids": [BCB],
            },
        )["id"]

    print("== members")
    ids = {}
    for nick, legal, set_id, status in PEOPLE:
        key = legal or nick
        where = f"legal_name='{legal}'" if legal else f"nickname='{nick}'"
        row = one(f"SELECT id FROM member WHERE universe_id='{U}' AND {where}")
        if row:
            print(f"  exists: {key}")
            ids[key] = row["id"]
            continue
        ids[key] = post(
            "members/",
            {
                "universe_id": U,
                "nickname": nick,
                "legal_name": legal,
                "nickname_unknown": nick is None,
                "status": status,
                "source_ids": [opinion_id],
                "affiliations": [{"set_id": set_id or foe, "is_primary": True}],
            },
        )["id"]

    print("== Morton (existing member J-Nutty)")
    patch(
        f"members/{MORTON}?universe_id={U}",
        {
            "legal_name": "William Morton",
            "mdoc_number": "744816",
            "dob": {"year": 1993, "month": 1, "day": 8, "precision": "YMD", "approx": False},
            "status": "LOCKED",
            "aliases": [],
            "source_ids": [opinion_id, otis_id],
        },
    )

    print("== incident")
    row = one(
        f"SELECT id FROM incident WHERE universe_id='{U}' "
        "AND date->>'year'='2008' AND date->>'month'='10' AND date->>'day'='16' "
        "AND location_text LIKE 'Evergreen%'"
    )
    if row:
        print("  exists")
    else:
        post(
            "incidents/",
            {
                "universe_id": U,
                "type": "MURDER",
                "date": DATE,
                "municipality_id": DETROIT_MUNI,
                "location_text": (
                    "Evergreen Rd & Pembroke St, outside Henry Ford High School, Detroit"
                ),
                "lat": 42.436772,
                "lng": -83.239136,
                "narrative": NARRATIVE,
                "verified": True,
                "source_ids": [opinion_id],
                "participants": participants(ids),
            },
        )

    print("== Morton OTIS photo")
    if not PHOTO.exists():
        print(f"  SKIP: {PHOTO} missing")
    elif not GO:
        print(f"  upload {PHOTO.name} ({PHOTO.stat().st_size} bytes) -> member {MORTON}")
    elif q(f"SELECT id FROM media WHERE member_id='{MORTON}' AND caption='{PHOTO_CAPTION}'"):
        print("  OTIS photo already attached")
    else:
        upload(api.token, MORTON)

    print("\nDRY RUN - re-run with --go" if not GO else "\ndone")


if __name__ == "__main__":
    main()
