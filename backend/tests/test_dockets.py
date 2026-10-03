"""The docket normaliser. Every input is a shape found in member_incarceration
or a research note; every expected value is written out by hand."""

import pytest

from app.core.dockets import (
    disposition_from_notes,
    federal_court,
    is_notable_state_offense,
    otis_charge,
    parse_case_ref,
)
from app.core.enums import CourtCaseKind, CourtJurisdiction


@pytest.mark.parametrize(
    ("case_id", "notes", "court", "docket", "aliases"),
    [
        (
            "2:17-cr-20740 (E.D. Mich.)",
            None,
            "E.D. Mich.",
            "2:17-cr-20740",
            ["2:17-cr-20740 (E.D. Mich.)"],
        ),
        (
            "2:17-cr-20668",
            "E.D. Mich. 2:17-cr-20668 (US v. X), Judge Y",
            "E.D. Mich.",
            "2:17-cr-20668",
            [],
        ),
        (
            "3:23-cr-180 (S.D. W.Va.)",
            None,
            "S.D. W. Va.",
            "3:23-cr-00180",
            ["3:23-cr-180 (S.D. W.Va.)"],
        ),
        (
            "3:21-cr-00036",
            "Federal sentence in the District of North Dakota, 3:21-cr-00036",
            "D.N.D.",
            "3:21-cr-00036",
            [],
        ),
        (
            "4:24-cr-00019",
            "18 months, conspiracy, M.D. Ga.; BOP register 1",
            "M.D. Ga.",
            "4:24-cr-00019",
            [],
        ),
        (
            "5:25-cr-20399",
            "District: Eastern District of Michigan",
            "E.D. Mich.",
            "5:25-cr-20399",
            [],
        ),
    ],
)
def test_federal_dockets(case_id, notes, court, docket, aliases):
    ref = parse_case_ref(case_id, notes)
    assert ref is not None
    assert (ref.jurisdiction, ref.court, ref.docket, ref.aliases) == (
        CourtJurisdiction.US_FEDERAL,
        court,
        docket,
        aliases,
    )
    assert ref.kind == CourtCaseKind.CRIMINAL


def test_a_magistrate_number_is_a_magistrate_case():
    ref = parse_case_ref("2:25-mj-30585", "E.D. Mich.")
    assert ref is not None and ref.kind == CourtCaseKind.MAGISTRATE
    assert ref.docket == "2:25-mj-30585"


@pytest.mark.parametrize(
    "case_id, notes",
    [
        ("2:22-cr-20074", "conspiracy to distribute; 210 months"),  # a docket, no court anywhere
        (
            "E.D. Mich.",
            "Assault with a dangerous weapon in aid of racketeering",
        ),  # a court, no docket
        ("W.D. Tenn.", None),
        ("", None),
        ("09912345-FC", None),  # a court file whose county nothing states
    ],
)
def test_it_does_not_guess(case_id, notes):
    assert parse_case_ref(case_id, notes) is None


@pytest.mark.parametrize(
    ("case_id", "notes", "court", "docket"),
    [
        (
            "09912345-FC",
            "Offense: X\nMCL 750.227B\nCounty: Wayne\nConviction type: Jury",
            "Wayne County Circuit Court",
            "09912345-FC",
        ),
        ("13004321-FH-C30", "County: Oakland", "Oakland County Circuit Court", "13004321-FH-C30"),
        ("25000419-01-FC", "County: Wayne\n", "Wayne County Circuit Court", "25000419-01-FC"),
        ("95002601FCA", "County: Kent", "Kent County Circuit Court", "95002601FCA"),
        ("01011952-03", "County: Wayne", "Wayne County Circuit Court", "01011952-03"),
    ],
)
def test_michigan_court_files(case_id, notes, court, docket):
    ref = parse_case_ref(case_id, notes)
    assert ref is not None
    assert (ref.jurisdiction, ref.court, ref.docket) == (CourtJurisdiction.US_STATE, court, docket)


def test_a_circuit_reference_written_out():
    ref = parse_case_ref("Wayne Circuit 11-054321-FC (MDOC #123456)", None)
    assert ref is not None
    assert (ref.court, ref.docket) == ("Wayne County Circuit Court", "11-054321-FC")
    assert ref.aliases == ["Wayne Circuit 11-054321-FC (MDOC #123456)"]


def test_district_names_in_full_and_short():
    assert federal_court("the Western District of Tennessee") == "W.D. Tenn."
    assert federal_court("District of Minnesota") == "D. Minn."
    assert federal_court("N.D. Ill. case") == "N.D. Ill."
    assert federal_court("nothing here") is None


@pytest.mark.parametrize(
    ("notes", "expected"),
    [
        ("Offense: Robbery\nConviction type: Plea", "PLEADED"),
        ("Offense: Murder\nConviction type: Jury", "CONVICTED"),
        ("Judge Z: guilty plea, conspiracy; 121 months.", "PLEADED"),
        ("Judge Z: jury verdict 2019, conspiracy resulting in death", "CONVICTED"),
        ("Held pending trial on one count of felon in possession", "PENDING"),
        ("the day he pleaded not guilty to all seven counts", "PENDING"),
        ("20 years, conspiracy to possess controlled substances", "CONVICTED"),
        ("Ten years and three months, then supervised release, imposed by Judge X", "CONVICTED"),
        ("possession of a machine gun; detained 2024-02-02; judgment 2025", "CONVICTED"),
        ("", "PENDING"),
    ],
)
def test_disposition_from_notes(notes, expected):
    assert disposition_from_notes(notes) == expected


def test_otis_charge_and_the_notable_rule():
    notes = "Offense: Homicide - Murder, Second Degree\nMCL 750.317\nCounty: Wayne\nConviction type: Plea"
    assert otis_charge(notes) == {
        "count": None,
        "statute": "MCL 750.317",
        "offense": "Homicide - Murder, Second Degree",
        "disposition": "PLEADED",
    }
    assert is_notable_state_offense(notes)
    assert is_notable_state_offense("Offense: Assault with Intent to Rob while Armed")
    assert not is_notable_state_offense("Offense: Police Officer - Assault/Resist/Obstruct")
    assert not is_notable_state_offense("Offense: Weapons - Felony Firearms")
    assert not is_notable_state_offense(None)


@pytest.mark.parametrize(
    ("case_id", "notes", "court", "docket"),
    [
        (
            "150000054321-FH",
            "Offense: X | County: Montcalm | Conviction type: Plea",
            "Montcalm County Circuit Court",
            "150000054321-FH",
        ),
        (
            "CRW012345-FH",
            "Offense: X | County: Washtenaw | Conviction",
            "Washtenaw County Circuit Court",
            "CRW012345-FH",
        ),
        (
            "912345-02",
            "Offense: X | County: Wayne | Conviction type: Bench",
            "Wayne County Circuit Court",
            "912345-02",
        ),
        (
            "07011024-01-FC",
            "First-degree felony murder, LIFE. Bench trial, Wayne County Circuit Court.",
            "Wayne County Circuit Court",
            "07011024-01-FC",
        ),
        ("17005730-FC-M", "County: St. Clair", "St. Clair County Circuit Court", "17005730-FC-M"),
    ],
)
def test_more_state_file_shapes(case_id, notes, court, docket):
    ref = parse_case_ref(case_id, notes)
    assert ref is not None
    assert (ref.court, ref.docket) == (court, docket)


@pytest.mark.parametrize(
    "case_id, notes",
    [
        ("24004586-01-FC / 24004489-01-FC", "Two counts, Wayne County"),  # two files in one spell
        ("08018563-01-FC", "Second-degree murder (MCL 750.317), 25 to 40 years."),  # no county
    ],
)
def test_state_references_it_will_not_place(case_id, notes):
    assert parse_case_ref(case_id, notes) is None
