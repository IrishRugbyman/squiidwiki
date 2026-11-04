"""Importing an OTIS profile onto a member is idempotent, by count.

Production collected 103 groups of identical spells (same member, court file,
offense line and dates) because the member form decided what was already on
file from a cached list the import never refreshed, so a second import within
the cache's lifetime posted every sentence again. The decision now lives in
`POST /members/{id}/incarcerations/import`.

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

    # The bug: a second (and third) import of the same profile duplicated every row.
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
