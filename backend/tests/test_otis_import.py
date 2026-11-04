"""Importing an OTIS profile onto a member is idempotent, by count, and never overwrites.

The member form used to decide what was already on file from a cached list the
import never refreshed, so a second import within the cache's lifetime would
have posted every sentence again. The decision now lives in
`POST /members/{id}/incarcerations/import`: a spell matches a row by court file,
offense line and start date, by count; a matched row's empty fields are filled
and every filled field OTIS disagrees with is reported, never written.

Everything here is invented: the court files are in the year 2099, and the
profile is built in code rather than read from a fixture.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.enums import DatePrecision, GlobalRole
from app.core.fuzzy_date import FuzzyDate
from app.services.mdoc import MdocProfile, MdocSentence, derive_spells

pytestmark = pytest.mark.asyncio(loop_scope="session")


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _d(y: int, m: int, d: int) -> FuzzyDate:
    return FuzzyDate(year=y, month=m, day=d, precision=DatePrecision.YMD)


def _count(offense: str, court_file: str, sentenced: FuzzyDate, **kw) -> MdocSentence:
    return MdocSentence(
        kind="prison",
        active=kw.pop("active", True),
        offense=offense,
        court_file=court_file,
        county="Testcounty",
        minimum_sentence="2 years 0 months 0 days",
        maximum_sentence=kw.pop("maximum_sentence", "2 years 0 months"),
        date_of_sentence=sentenced,
        **kw,
    )


def _profile() -> MdocProfile:
    """Five prison counts on three court files, two of them identical, plus probation."""
    return MdocProfile(
        legal_name="Testy Example",
        dob=_d(2070, 1, 1),
        mdoc_number="900001",
        status="Prisoner",
        facility="Test Correctional Facility",
        earliest_release_date=_d(2101, 1, 1),
        discharge_date=_d(2105, 1, 1),
        sentences=[
            _count(
                "Assault with Intent to Commit Murder",
                "2099-000001-FC",
                _d(2099, 3, 1),
                maximum_sentence="20 years 0 months",
            ),
            # Two genuinely separate counts that read the same: both must survive.
            _count("Weapons - Felony Firearms", "2099-000001-FC", _d(2099, 3, 1)),
            _count("Weapons - Felony Firearms", "2099-000001-FC", _d(2099, 3, 1)),
            _count(
                "Controlled Substance-Delivery/Manf.",
                "2098-000002-FH",
                _d(2098, 5, 1),
                active=False,
                date_of_discharge=_d(2098, 11, 1),
            ),
            MdocSentence(
                kind="probation", active=False, offense="Retail Fraud", court_file="2097-000003-FH"
            ),
        ],
    )


def _payload(profile: MdocProfile) -> list[dict]:
    out = []
    for sp in derive_spells(profile):
        body = {}
        for k, v in vars(sp).items():
            body[k] = v.model_dump(mode="json") if isinstance(v, FuzzyDate) else v
        out.append(body)
    return out


class _Member:
    def __init__(self, headers: dict, universe_id: str, member_id: str):
        self.headers = headers
        self.universe_id = universe_id
        self.member_id = member_id

    @property
    def base(self) -> str:
        return f"/api/v1/members/{self.member_id}/incarcerations"

    @property
    def q(self) -> str:
        return f"?universe_id={self.universe_id}"


async def _member(client: AsyncClient, session: AsyncSession) -> _Member:
    email = f"admin_{_uid()}@example.com"
    await create_user(session, email, "adminpass", GlobalRole.ADMIN)
    token = (
        await client.post("/api/v1/auth/login", json={"email": email, "password": "adminpass"})
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/v1/universes/",
        json={"name": f"Uni {_uid()}", "slug": f"uni-{_uid()}"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    universe_id = resp.json()["id"]
    resp = await client.post(
        "/api/v1/members/",
        json={"universe_id": universe_id, "nickname": f"Testy {_uid()}", "status": "LOCKED"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    return _Member(headers, universe_id, resp.json()["id"])


async def _import(client: AsyncClient, m: _Member, spells: list[dict]) -> dict:
    resp = await client.post(f"{m.base}/import{m.q}", json={"spells": spells}, headers=m.headers)
    assert resp.status_code == 200, f"{resp.status_code} {resp.text}"
    return resp.json()


async def _offenses(client: AsyncClient, m: _Member) -> list[str]:
    resp = await client.get(f"{m.base}{m.q}", headers=m.headers)
    assert resp.status_code == 200, resp.text
    return sorted((s["case_id"], s["notes"].split("\n")[0]) for s in resp.json())


EXPECTED = sorted(
    [
        ("2099-000001-FC", "Offense: Assault with Intent to Commit Murder"),
        ("2099-000001-FC", "Offense: Weapons - Felony Firearms"),
        ("2099-000001-FC", "Offense: Weapons - Felony Firearms"),
        ("2098-000002-FH", "Offense: Controlled Substance-Delivery/Manf."),
    ]
)


async def test_reimporting_a_profile_writes_nothing_and_keeps_identical_counts(
    client: AsyncClient, db_session: AsyncSession
):
    m = await _member(client, db_session)
    spells = _payload(_profile())
    assert len(spells) == 4  # probation is never imported

    first = await _import(client, m, spells)
    assert (len(first["created"]), first["matched"]) == (4, 0)
    assert await _offenses(client, m) == EXPECTED

    # Through the old form path, a second import of the same profile re-posted every row.
    for _ in range(2):
        again = await _import(client, m, spells)
        assert (len(again["created"]), again["matched"]) == (0, 4)
    assert await _offenses(client, m) == EXPECTED


async def test_import_matches_by_count_not_by_court_file(
    client: AsyncClient, db_session: AsyncSession
):
    """One felony-firearm count on file and OTIS listing two: the second is written.

    The old form skipped every sentence whose court file was already on record,
    so a count added to a file later (a resentencing) could never arrive.
    """
    m = await _member(client, db_session)
    spells = _payload(_profile())
    firearm = next(s for s in spells if "Felony Firearms" in s["notes"])
    resp = await client.post(f"{m.base}{m.q}", json=firearm, headers=m.headers)
    assert resp.status_code == 201, resp.text

    out = await _import(client, m, spells)
    assert (len(out["created"]), out["matched"]) == (3, 1)
    assert await _offenses(client, m) == EXPECTED


async def test_import_ignores_edits_below_the_offense_line(
    client: AsyncClient, db_session: AsyncSession
):
    """A researcher's edit to a spell's later note lines does not make it new."""
    m = await _member(client, db_session)
    spells = _payload(_profile())
    first = await _import(client, m, spells)
    spell = first["created"][0]
    resp = await client.patch(
        f"{m.base}/{spell['id']}{m.q}",
        json={"notes": spell["notes"].split("\n")[0] + "\nHeld at county pending transfer"},
        headers=m.headers,
    )
    assert resp.status_code == 200, resp.text

    again = await _import(client, m, spells)
    assert (len(again["created"]), again["matched"]) == (0, 4)
    # The edit stays, and the import says it saw something else.
    assert again["differences"] == [
        {
            "spell_id": spell["id"],
            "field": "notes",
            "on_file": spell["notes"].split("\n")[0] + "\nHeld at county pending transfer",
            "incoming": spell["notes"],
        }
    ]
    rows = (await client.get(f"{m.base}{m.q}", headers=m.headers)).json()
    kept = next(r for r in rows if r["id"] == spell["id"])
    assert kept["notes"].endswith("Held at county pending transfer")


# The rows below are the ones the import must not touch. The values are written
# out by hand, not produced by the code under test.
DRUG = "Offense: Controlled Substance-Delivery/Manf."
NOV_1_2098 = {
    "year": 2098,
    "month": 11,
    "day": 1,
    "precision": "YMD",
    "approx": False,
    "circa_text": None,
}
DEC_15_2098 = {
    "year": 2098,
    "month": 12,
    "day": 15,
    "precision": "YMD",
    "approx": False,
    "circa_text": None,
}
JAN_1_2105 = {
    "year": 2105,
    "month": 1,
    "day": 1,
    "precision": "YMD",
    "approx": False,
    "circa_text": None,
}
JUN_1_2106 = {
    "year": 2106,
    "month": 6,
    "day": 1,
    "precision": "YMD",
    "approx": False,
    "circa_text": None,
}


async def _rows(client: AsyncClient, m: _Member) -> list[dict]:
    resp = await client.get(f"{m.base}{m.q}", headers=m.headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_reimport_with_a_changed_to_date_keeps_the_stored_one_and_reports_it(
    client: AsyncClient, db_session: AsyncSession
):
    """OTIS now gives a different discharge date: no new row, the stored date stays."""
    m = await _member(client, db_session)
    spells = _payload(_profile())
    await _import(client, m, spells)
    drug_row = next(r for r in await _rows(client, m) if r["notes"].startswith(DRUG))
    assert drug_row["to_date"] == NOV_1_2098

    changed = [dict(s) for s in spells]
    for s in changed:
        if s["notes"].startswith(DRUG):
            s["to_date"] = DEC_15_2098
    out = await _import(client, m, changed)

    assert (len(out["created"]), out["matched"]) == (0, 4)
    assert out["filled"] == []
    assert out["differences"] == [
        {
            "spell_id": drug_row["id"],
            "field": "to_date",
            "on_file": NOV_1_2098,
            "incoming": DEC_15_2098,
        }
    ]
    rows = await _rows(client, m)
    assert len(rows) == 4
    assert next(r for r in rows if r["id"] == drug_row["id"])["to_date"] == NOV_1_2098


async def test_reimport_never_overwrites_release_dates_or_facility(
    client: AsyncClient, db_session: AsyncSession
):
    m = await _member(client, db_session)
    spells = _payload(_profile())
    await _import(client, m, spells)
    lead = next(r for r in await _rows(client, m) if r["max_discharge_date"] is not None)
    assert (lead["max_discharge_date"], lead["facility"]) == (
        JAN_1_2105,
        "Test Correctional Facility",
    )

    changed = [dict(s) for s in spells]
    for s in changed:
        if s["max_discharge_date"] is not None:
            s["max_discharge_date"] = JUN_1_2106
            s["facility"] = "Other Test Facility"
    out = await _import(client, m, changed)

    assert len(out["created"]) == 0
    assert sorted((d["spell_id"], d["field"]) for d in out["differences"]) == sorted(
        [(lead["id"], "facility"), (lead["id"], "max_discharge_date")]
    )
    after = next(r for r in await _rows(client, m) if r["id"] == lead["id"])
    assert (after["max_discharge_date"], after["facility"]) == (
        JAN_1_2105,
        "Test Correctional Facility",
    )


async def test_a_missing_to_date_on_file_is_filled(client: AsyncClient, db_session: AsyncSession):
    """A row with no end date takes the one OTIS gives; nothing else is written."""
    m = await _member(client, db_session)
    spells = _payload(_profile())
    drug = next(s for s in spells if s["notes"].startswith(DRUG))
    resp = await client.post(f"{m.base}{m.q}", json={**drug, "to_date": None}, headers=m.headers)
    assert resp.status_code == 201, resp.text
    on_file = resp.json()
    assert on_file["to_date"] is None

    out = await _import(client, m, spells)

    assert (len(out["created"]), out["matched"]) == (3, 1)
    assert out["filled"] == [{"spell_id": on_file["id"], "field": "to_date", "value": NOV_1_2098}]
    assert out["differences"] == []
    rows = await _rows(client, m)
    assert len(rows) == 4
    assert next(r for r in rows if r["id"] == on_file["id"])["to_date"] == NOV_1_2098


async def test_two_identical_counts_stay_two_when_their_end_dates_arrive(
    client: AsyncClient, db_session: AsyncSession
):
    """Both felony-firearm counts are matched, by count, and both get the end date."""
    m = await _member(client, db_session)
    spells = _payload(_profile())
    await _import(client, m, spells)

    served = [dict(s) for s in spells]
    for s in served:
        if "Felony Firearms" in s["notes"]:
            s["to_date"] = DEC_15_2098
    out = await _import(client, m, served)

    assert (len(out["created"]), out["matched"]) == (0, 4)
    assert out["differences"] == []
    firearms = [r for r in await _rows(client, m) if "Felony Firearms" in r["notes"]]
    assert len(firearms) == 2
    assert [r["to_date"] for r in firearms] == [DEC_15_2098, DEC_15_2098]
    assert sorted(f["spell_id"] for f in out["filled"]) == sorted(r["id"] for r in firearms)
