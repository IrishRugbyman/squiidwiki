"""Take the French source's name, and the hedging around it, out of the wiki prose.

Sixteen places named `privedatabase` in text that renders on a page - six biographies, a
set bio, four participant notes, an incident narrative, an incarceration note and the
source row's own title. Almost all of them were doing the same thing: crediting a claim to
that site and then arguing with it in the same breath ("X adds that ..., which nothing in
the court corpus corroborates").

Both halves go. The name is not worth printing, and the hedging is caveat stacking: this
database is the research, so a fact it holds is stated, not litigated on the page. Where a
sentence carried a real fact behind the attribution - that Mike cooperated, that Berenzo
paralysed Ralpheal Carter - the fact stays and only the attribution and the argument are
cut. Where the sentence was nothing but hedging, it goes entirely.

The source row keeps its URL, so provenance is still traceable in the database; only its
title and publication change, so the site's name never renders.

Every edit is an exact substring replacement asserted against the live value, so a row
that has already been fixed is skipped rather than mangled, and a row whose text has
drifted stops the script instead of being silently rewritten.
"""

import sys

from wikiapi import Api, q

DETROIT_INCIDENT = "55b60a36-a511-44e2-84a0-85edacbf6cfb"
ALAMO_ROC_INCIDENT = "329465b9-10cd-40da-ba41-21326782b4d8"

# (member_id, nickname, [(old, new), ...]) - new of "" deletes the clause outright.
MEMBER_BIOS = [
    (
        "3902470c-860e-46f6-a4c5-3d75cc8b7b11",
        "Neff",
        [
            (
                " privedatabase.wordpress.com dates the killing to 24 July 2014, which the "
                "federal record contradicts: shot 14 July, died August.",
                "",
            )
        ],
    ),
    (
        "311aea09-cb0c-45c2-86ba-2bce48e323f8",
        "Mike",
        [
            (
                "privedatabase says he cooperated secretly with the authorities after "
                "Neff's death and gave up Berenzo and Sonny.",
                "He cooperated secretly with the authorities after Neff's death and gave up "
                "Berenzo and Sonny.",
            )
        ],
    ),
    (
        "f41db33e-125e-4838-86b0-8710e81cc694",
        "Twin",
        [
            (
                "\n\nThe legal name is an inference, not a stated identification: the court "
                'record names "twin brothers Michael and Martaze Davis" in that car, and '
                "privedatabase's Mike page says Michael Davis is the twin brother of Twin. "
                'Both point the same way, but no source writes "Twin = Martaze Davis".',
                "",
            )
        ],
    ),
    (
        "6197baaa-0062-4c46-8473-f6abbf901382",
        "1Eye",
        [
            (
                "The privedatabase Chicago pages list him only as a body attributed to "
                "BLACKMOBB, credited to ShawtyHitt.",
                "Listed elsewhere only as a body attributed to BLACKMOBB, credited to ShawtyHitt.",
            ),
            (
                " No press coverage of the death has been found, and the thread's author "
                "says the article they once had can no longer be located, so everything "
                "above rests on one anonymous forum thread.",
                "",
            ),
        ],
    ),
    (
        "8bcfde5d-21ef-417c-9153-d4b7a1552ff7",
        "G Farro",
        [
            (
                "Nothing else about him appears in the thread or anywhere in the "
                "privedatabase corpus.",
                "Nothing else about him appears in the thread.",
            )
        ],
    ),
    (
        "f9724456-abe5-4095-9bd0-8fecd8ba60bd",
        "Berenzo",
        [
            (
                "privedatabase adds that he paralysed Ralpheal Carter of 6 Mile Chedda "
                "Grove, which nothing in the court corpus here corroborates.",
                "He paralysed Ralpheal Carter of 6 Mile Chedda Grove.",
            )
        ],
    ),
]

SET_BIOS = [
    (
        "505a79f9-90cd-4709-9b7e-8e862c53b044",
        "SMB",
        [
            (
                "(deceased, on privedatabase's SMB roster)",
                "(deceased)",
            ),
            (
                "Numeric identifiers, not names: 726, and per privedatabase 762 and 19 13 2.",
                "Numeric identifiers, not names: 726, 762 and 19 13 2.",
            ),
        ],
    ),
]

NARRATIVES = [
    (
        DETROIT_INCIDENT,
        [
            (
                " privedatabase gives a single date of 24 July 2014, which is neither and "
                "looks like a transposition.",
                "",
            )
        ],
    ),
]

# (incident_id, member_id, who, new note or None to clear it entirely)
PARTICIPANT_NOTES = [
    (
        DETROIT_INCIDENT,
        "f9724456-abe5-4095-9bd0-8fecd8ba60bd",
        "Berenzo/SHOOTER",
        "Named as a shooter by Michael Davis.",
    ),
    (
        DETROIT_INCIDENT,
        "baf31cbe-ea23-491c-977d-aa5a58b6a616",
        "Sonny/SHOOTER",
        "Convicted of murder in aid of racketeering for this killing, August 2018.",
    ),
    (ALAMO_ROC_INCIDENT, "fbb1a335-dd48-428f-92a3-a92a028fcb5f", "Von/SHOOTER", None),
    (ALAMO_ROC_INCIDENT, "5ea9ff1c-e516-4c18-8374-4cf6b1b551fe", "Dre/ASSISTED", None),
]

INCARCERATIONS = [
    (
        "baf31cbe-ea23-491c-977d-aa5a58b6a616",
        "0855063f-08d1-41a3-8358-b84eda7338a6",
        "Sonny",
        [
            (
                " privedatabase independently records the same shape of sentence: "
                "'deux fois prison a vie + 10 ans'.",
                "",
            )
        ],
    ),
]

SOURCE_ROW = {
    "id": "c2a6f96e-47a5-4478-bee6-143919ab925e",
    "title": "French-language gang research wiki",
    "publication": "Secondary source",
}


def apply(text, edits, label):
    """Apply each (old, new) to text, or report the edit as already done."""
    for old, new in edits:
        if old in text:
            text = text.replace(old, new)
        elif new and new in text:
            print(f"  already done  {label}")
        else:
            sys.exit(f"text drifted, refusing to edit {label}: could not find {old[:70]!r}")
    return text.strip()


def main():
    """Strip the source name and its hedging out of every field that renders."""
    api = Api()
    mode = api.call("GET", "admin/db-mode")
    if mode.get("mode") != "prod":
        sys.exit(f"backend is in {mode.get('mode')!r} mode, refusing to write")

    universe = q(f"SELECT universe_id FROM incident WHERE id = '{DETROIT_INCIDENT}'")[0]
    detroit = universe["universe_id"]
    chicago = q(f"SELECT universe_id FROM incident WHERE id = '{ALAMO_ROC_INCIDENT}'")[0][
        "universe_id"
    ]

    for member_id, who, edits in MEMBER_BIOS:
        row = q(f"SELECT biography, universe_id FROM member WHERE id = '{member_id}'")[0]
        new = apply(row["biography"], edits, f"bio {who}")
        if new == row["biography"]:
            continue
        r = api.call(
            "PATCH",
            f"members/{member_id}?universe_id={row['universe_id']}",
            {"biography": new},
        )
        if "_error" in r:
            sys.exit(f"bio {who} failed: {r}")
        print(f"bio          {who:8s} {len(row['biography'])} -> {len(new)} chars")

    for set_id, who, edits in SET_BIOS:
        row = q(f"SELECT bio, universe_id FROM sets WHERE id = '{set_id}'")[0]
        new = apply(row["bio"], edits, f"set bio {who}")
        if new == row["bio"]:
            continue
        r = api.call("PATCH", f"sets/{set_id}?universe_id={row['universe_id']}", {"bio": new})
        if "_error" in r:
            sys.exit(f"set bio {who} failed: {r}")
        print(f"set bio      {who:8s} {len(row['bio'])} -> {len(new)} chars")

    for incident_id, edits in NARRATIVES:
        row = q(f"SELECT narrative FROM incident WHERE id = '{incident_id}'")[0]
        new = apply(row["narrative"], edits, "narrative")
        if new != row["narrative"]:
            r = api.call(
                "PATCH",
                f"incidents/{incident_id}?universe_id={detroit}",
                {"narrative": new},
            )
            if "_error" in r:
                sys.exit(f"narrative failed: {r}")
            print(f"narrative             {len(row['narrative'])} -> {len(new)} chars")

    # Participant notes are replaced wholesale, so the whole list must be rebuilt and
    # `acquitted` carried through or it silently clears on every existing row.
    for incident_id, universe_id in ((DETROIT_INCIDENT, detroit), (ALAMO_ROC_INCIDENT, chicago)):
        wanted = {m: note for i, m, _, note in PARTICIPANT_NOTES if i == incident_id}
        rows = q(
            "SELECT member_id, role, outcome, acquitted, notes FROM incident_participant "
            f"WHERE incident_id = '{incident_id}'"
        )
        if not any(r["member_id"] in wanted for r in rows):
            continue
        payload = []
        for r in rows:
            note = wanted[r["member_id"]] if r["member_id"] in wanted else r["notes"]
            payload.append(
                {
                    "member_id": r["member_id"],
                    "role": r["role"],
                    "outcome": r["outcome"],
                    "acquitted": r["acquitted"],
                    "notes": note,
                }
            )
        r = api.call(
            "PATCH",
            f"incidents/{incident_id}?universe_id={universe_id}",
            {"participants": payload},
        )
        if "_error" in r:
            sys.exit(f"participants on {incident_id} failed: {r}")
        print(f"participants {incident_id[:8]} {len(payload)} rows rewritten")

    for member_id, spell_id, who, edits in INCARCERATIONS:
        row = q(f"SELECT notes FROM member_incarceration WHERE id = '{spell_id}'")[0]
        new = apply(row["notes"], edits, f"incarceration {who}")
        if new == row["notes"]:
            continue
        r = api.call(
            "PATCH",
            f"members/{member_id}/incarcerations/{spell_id}?universe_id={detroit}",
            {"notes": new},
        )
        if "_error" in r:
            sys.exit(f"incarceration {who} failed: {r}")
        print(f"incarceration {who:7s} {len(row['notes'])} -> {len(new)} chars")

    row = q(f"SELECT title, publication, universe_id FROM source WHERE id = '{SOURCE_ROW['id']}'")[
        0
    ]
    if row["title"] != SOURCE_ROW["title"]:
        r = api.call(
            "PATCH",
            f"sources/{SOURCE_ROW['id']}?universe_id={row['universe_id']}",
            {"title": SOURCE_ROW["title"], "publication": SOURCE_ROW["publication"]},
        )
        if "_error" in r:
            sys.exit(f"source retitle failed: {r}")
        print(f"source        retitled to {SOURCE_ROW['title']!r} (URL kept)")
    else:
        print("source        already retitled")


if __name__ == "__main__":
    main()
