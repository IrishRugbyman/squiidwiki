"""Seed the killing of Walvon Holland, 13 June 2007, into Metro Detroit.

Walvon Holland, 16, BCB, was already on file as DEAD with no incident behind
it. This gives him one, and it is built from the court record rather than from
the street account that was in his biography.

Sources, in the order they were found:

  Herbert v Rivard, No. 2:11-cv-12967 (E.D. Mich., 27 Apr 2015), Hon. Bernard
  A. Friedman, denying habeas. Read from govinfo, because law.justia.com 403s
  this server. It quotes the Michigan Court of Appeals' recitation of the trial
  testimony in People v Herbert, No. 284313, 2009 WL 1682140 (Mich Ct App,
  16 June 2009), and gives the trial court file, People v Herbert,
  No. 07-11024-01 (Wayne County Circuit Court).

  MDOC/OTIS offender 615989, Rodgereck Herbert: date of birth, the life
  sentence, the same court file, and two street names.

  The 2007 chamspage homicide list, for the address.

**The court record contradicts the biography that was on the member, and the
court record is what is used here.** The biography said he was killed by BCB's
older generation, shot with a shotgun at his door after a brick came through
his window. The testimony is that he was shot three times in the head and once
in the chest inside the basement bedroom of his friend Kurtis Kelm, during a
robbery for the marijuana and money the two of them kept there, and that the
shooter was Rodgereck Herbert. No gang is mentioned anywhere in the opinion,
and neither a shotgun nor a brick appears in it. The biography is cleared here;
its account is kept in `../extraction/leads.md` as an unattached account,
because it may belong to a different member.

**The homicide list has him as "Wolvon Howell".** Same date, same age of 16.
The court record settles that the person is Walvon Holland, so the list entry
is a garbled spelling and its address is used.

Idempotent. Dry-run by default; --go writes through the local API on :8001.
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
UNKNOWN_SET = "f4bfd8ab-c0ce-458f-93eb-8d741109b077"
DETROIT_MUNI = "55d40a23-fdbe-4e83-b5b0-5670a04df4c9"
WALVON = "98b0d330-0e44-475f-92cd-b7770e7702e5"

SCRATCH = pathlib.Path(
    "/tmp/claude-1000/-home-lbzgiu-squiidwiki/4e0c90be-ff2d-453e-aa9b-764467c440bb/scratchpad"
)
HERBERT_PHOTO = SCRATCH / "mdoc-615989.jpg"
HERBERT_CAPTION = "MDOC OTIS offender photo, 3 November 2022"

HABEAS = {
    "universe_id": U,
    "url": (
        "https://www.govinfo.gov/content/pkg/USCOURTS-mied-2_11-cv-12967/"
        "pdf/USCOURTS-mied-2_11-cv-12967-0.pdf"
    ),
    "title": "Herbert v Rivard, No. 2:11-cv-12967 (E.D. Mich., 27 Apr 2015)",
    "publication": "U.S. District Court, Eastern District of Michigan",
    "published_at": {"year": 2015, "month": 4, "day": 27, "precision": "YMD", "approx": False},
    "accessed_at": "2026-08-25",
    "reliability": "HIGH",
    "notes": (
        "Opinion denying Rodgereck Herbert's habeas petition. Quotes the Michigan Court of "
        "Appeals' recitation of the trial testimony in People v Herbert, No. 284313, 2009 WL "
        "1682140 (Mich Ct App, 16 June 2009): Walvon Holland, 16, was shot three times in "
        "the head and once in the chest inside the basement bedroom of his friend Kurtis "
        "Kelm, where the two of them kept the marijuana they sold. Kelm woke to Herbert "
        "demanding drugs and money, saw him point a gun, and saw him shoot when Holland "
        "refused. A second person Kelm could not see entered and took the drugs and money. "
        "Bench trial, Wayne County Circuit Court, People v Herbert No. 07-11024-01; "
        "convicted of first-degree felony murder and felony firearm, sentenced 20 February "
        "2008 to life plus two years. No gang, shotgun or brick appears anywhere in the "
        "opinion. Read from govinfo; law.justia.com returns 403 to this server."
    ),
}

OTIS_HERBERT = {
    "universe_id": U,
    "url": "https://mdocweb.state.mi.us/OTIS2",
    "title": "MDOC OTIS offender 615989, Rodgereck Herbert",
    "publication": "Michigan Department of Corrections",
    "accessed_at": "2026-08-25",
    "reliability": "HIGH",
    "notes": (
        "Offender profile. Date of birth 1 October 1988, so 18 at the offence against "
        "Holland's 16. Felony murder (LIFE) and felony firearm (2 years) on court file "
        "07011024-01-FC, both sentenced 20 February 2008. Carson City Correctional "
        "Facility, security level II. SID 2739772L. Street names Bama and Bookie. Marks "
        "include a left forearm tattoo reading 'Money Over Everything'. Recorded name "
        "variants: Roderick Markieth Herbert, Rodgereck Markeith Herbert."
    ),
}

CHAMSPAGE_2007 = {
    "universe_id": U,
    "url": "http://chamspage.blogspot.com/2011/11/2007-detroit-homicidemurder-list.html",
    "title": "2007 Detroit Homicide/Murder Victim List",
    "publication": "chamspage.blogspot.com",
    "accessed_at": "2026-08-21",
    "reliability": "MEDIUM",
    "notes": (
        "Personal blog compiling Detroit homicide victims by year. The 13 June 2007 entry "
        "reads 'Wolvon Howell, 16, 18997 Lenore' - a garbled spelling of Walvon Holland, "
        "settled by the court record, which agrees on the date and the age. Used here for "
        "the address."
    ),
}

NARRATIVE = (
    "Walvon Holland was shot three times in the head and once in the chest in the basement "
    "bedroom of his friend Kurtis Kelm, where the two of them kept the marijuana they sold "
    "together. Kelm was asleep in the room and woke to Rodgereck Herbert demanding drugs and "
    "money. From where he lay hidden he saw Herbert point a gun at Holland, and saw him fire "
    "when Holland refused. A second man Kelm never saw came down into the basement, and the "
    "drugs and the money were gone once both had left. Kelm's testimony convicted Herbert at "
    "a bench trial of first-degree felony murder and felony firearm."
)

GO = "--go" in sys.argv


def one(sql):
    """Run a query and return its first row, or None."""
    r = q(sql)
    return r[0] if r else None


def upload(token, member_id, photo, caption):
    """POST a mugshot as multipart/form-data to /media/."""
    boundary = "----squiidwiki" + uuid.uuid4().hex
    ctype = mimetypes.guess_type(photo.name)[0] or "image/jpeg"
    fields = {"universe_id": U, "member_id": member_id, "caption": caption}
    body = b""
    for k, v in fields.items():
        body += (
            f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'
        ).encode()
    body += (
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
        f'filename="{photo.name}"\r\nContent-Type: {ctype}\r\n\r\n'
    ).encode()
    body += photo.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
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
            print("    uploaded:", json.loads(x.read())["id"])
    except urllib.error.HTTPError as e:
        sys.exit(f"    upload failed: {e.code} {e.read()[:300].decode(errors='replace')}")


def main():
    """Seed the sources, Herbert and Kelm, the incident, and clear Walvon's biography."""
    api = Api() if GO else None

    def post(path, payload):
        if not GO:
            print(f"  POST {path}  {json.dumps(payload)[:120]}")
            return {"id": str(uuid.uuid4())}
        r = api.call("POST", path, payload)
        if isinstance(r, dict) and r.get("_error"):
            sys.exit(f"POST {path} failed: {r['_error']} {r['_body']}")
        return r

    def patch(path, payload):
        if not GO:
            print(f"  PATCH {path}  {json.dumps(payload)[:120]}")
            return None
        r = api.call("PATCH", path, payload)
        if isinstance(r, dict) and r.get("_error"):
            sys.exit(f"PATCH {path} failed: {r['_error']} {r['_body']}")
        return r

    print("== sources")
    ids = []
    for s in (HABEAS, OTIS_HERBERT, CHAMSPAGE_2007):
        row = one(f"SELECT id FROM source WHERE universe_id='{U}' AND url='{s['url']}'")
        if row:
            print(f"  exists: {s['title'][:56]}")
            ids.append(row["id"])
        else:
            ids.append(post("sources/", s)["id"])
    habeas_id, otis_id, chams_id = ids

    print("== Rodgereck Herbert")
    row = one(f"SELECT id FROM member WHERE universe_id='{U}' AND legal_name='Rodgereck Herbert'")
    if row:
        herbert = row["id"]
        print("  exists")
    else:
        herbert = post(
            "members/",
            {
                "universe_id": U,
                "legal_name": "Rodgereck Herbert",
                "nickname_unknown": True,
                # Bama and Bookie are street names, unlike the OTIS spelling
                # variants of the legal name, so these do belong in aliases.
                "aliases": ["Bama", "Bookie"],
                "mdoc_number": "615989",
                "dob": {"year": 1988, "month": 10, "day": 1, "precision": "YMD", "approx": False},
                "status": "LOCKED",
                "source_ids": [habeas_id, otis_id],
                "affiliations": [{"set_id": UNKNOWN_SET, "is_primary": True}],
            },
        )["id"]

    spell = one(f"SELECT id FROM member_incarceration WHERE member_id='{herbert}'")
    if spell:
        print("  spell exists")
    else:
        post(
            f"members/{herbert}/incarcerations?universe_id={U}",
            {
                "from_date": {
                    "year": 2008,
                    "month": 2,
                    "day": 20,
                    "precision": "YMD",
                    "approx": False,
                },
                "life_sentence": True,
                "facility": "Carson City Correctional Facility",
                "case_id": "07011024-01-FC",
                "notes": (
                    "First-degree felony murder, LIFE, and felony firearm, 2 years. Bench "
                    "trial, Wayne County Circuit Court. Aged 18 at the offence."
                ),
            },
        )
        print("  spell created")

    if not HERBERT_PHOTO.exists():
        print(f"  photo SKIP: {HERBERT_PHOTO.name} missing")
    elif not GO:
        print(f"  photo upload {HERBERT_PHOTO.name} ({HERBERT_PHOTO.stat().st_size} bytes)")
    elif q(f"SELECT id FROM media WHERE member_id='{herbert}' AND caption='{HERBERT_CAPTION}'"):
        print("  photo already attached")
    else:
        upload(api.token, herbert, HERBERT_PHOTO, HERBERT_CAPTION)

    print("== Kurtis Kelm")
    row = one(f"SELECT id FROM member WHERE universe_id='{U}' AND legal_name='Kurtis Kelm'")
    if row:
        kelm = row["id"]
        print("  exists")
    else:
        kelm = post(
            "members/",
            {
                "universe_id": U,
                "legal_name": "Kurtis Kelm",
                "nickname_unknown": True,
                "status": "UNKNOWN",
                "source_ids": [habeas_id],
                "affiliations": [{"set_id": UNKNOWN_SET, "is_primary": True}],
            },
        )["id"]

    print("== incident")
    row = one(
        f"SELECT id FROM incident WHERE universe_id='{U}' "
        "AND date->>'year'='2007' AND date->>'month'='6' AND date->>'day'='13' "
        "AND location_text LIKE '18997 Lenore%'"
    )
    if row:
        print("  exists")
    else:
        post(
            "incidents/",
            {
                "universe_id": U,
                "type": "MURDER",
                "date": {"year": 2007, "month": 6, "day": 13, "precision": "YMD", "approx": False},
                "municipality_id": DETROIT_MUNI,
                "location_text": "18997 Lenore Ave, Five Points, Detroit",
                "lat": 42.427503,
                "lng": -83.281793,
                "narrative": NARRATIVE,
                "verified": True,
                "source_ids": [habeas_id, chams_id],
                "participants": [
                    {
                        "member_id": herbert,
                        "role": "SHOOTER",
                        "outcome": "UNHARMED",
                        "notes": (
                            "Convicted of first-degree felony murder and felony firearm at a "
                            "bench trial; sentenced to life plus two years."
                        ),
                    },
                    {"member_id": WALVON, "role": "VICTIM", "outcome": "KILLED"},
                    {
                        "member_id": kelm,
                        "role": "BYSTANDER",
                        "outcome": "UNHARMED",
                        "notes": (
                            "Asleep in the room and hidden through the shooting. His "
                            "testimony identified the shooter and convicted him."
                        ),
                    },
                ],
            },
        )
        print("  created")

    print("== Walvon's biography")
    cur = one(f"SELECT biography FROM member WHERE id='{WALVON}'")
    if cur and cur.get("biography"):
        patch(f"members/{WALVON}?universe_id={U}", {"biography": ""})
        print("  cleared (its account moved to extraction/leads.md)")
    else:
        print("  already empty")

    print("\nDRY RUN - re-run with --go" if not GO else "\ndone")


if __name__ == "__main__":
    main()
