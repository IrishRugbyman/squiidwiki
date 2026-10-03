"""A spell finds or makes the court case its court file names.

Through the API, as the member page, the OTIS import and the `wiki` CLI write
spells. Expected values come from each test's own setup.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.enums import GlobalRole

pytestmark = pytest.mark.asyncio(loop_scope="session")

OTIS_MURDER = (
    "Offense: Homicide - Murder, Second Degree\nMCL 750.317\nCounty: Wayne\n"
    "Conviction type: Plea\nSentence: 20 years 0 months 0 days to 40 years 0 months"
)
OTIS_FIREARM = (
    "Offense: Weapons - Felony Firearms\nMCL 750.227BA\nCounty: Wayne\n"
    "Conviction type: Plea\nSentence: 2 years 0 months 0 days to 2 years 0 months"
)


def _uid() -> str:
    return uuid.uuid4().hex[:8]


@pytest.fixture
async def ctx(client: AsyncClient, db_session: AsyncSession):
    email = f"admin_{_uid()}@example.com"
    await create_user(db_session, email, "adminpass", GlobalRole.ADMIN)
    token = (
        await client.post("/api/v1/auth/login", json={"email": email, "password": "adminpass"})
    ).json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}
    resp = await client.post(
        "/api/v1/universes/", json={"name": f"U {_uid()}", "slug": f"u-{_uid()}"}, headers=auth
    )
    return client, auth, resp.json()["id"]


async def _member(ctx, nickname: str, legal_name: str | None = None) -> str:
    client, auth, uid = ctx
    resp = await client.post(
        "/api/v1/members/",
        json={"universe_id": uid, "nickname": nickname, "legal_name": legal_name},
        headers=auth,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _spell(ctx, member_id: str, **body) -> dict:
    client, auth, uid = ctx
    resp = await client.post(
        f"/api/v1/members/{member_id}/incarcerations",
        params={"universe_id": uid},
        json={"from_date": {"year": 2019, "precision": "Y", "approx": False}, **body},
        headers=auth,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _case(ctx, case_id: str) -> dict:
    client, auth, uid = ctx
    resp = await client.get(
        f"/api/v1/court-cases/{case_id}", params={"universe_id": uid}, headers=auth
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_a_federal_docket_makes_one_case_for_every_defendant(ctx):
    docket = f"2:17-cr-{uuid.uuid4().int % 90000 + 10000}"
    first = await _member(ctx, "First", "Alpha Doe")
    second = await _member(ctx, "Second")
    a = await _spell(ctx, first, case_id=f"{docket} (E.D. Mich.)", notes="guilty plea; 121 months")
    # The other spelling, with the court only in the notes, is the same case.
    b = await _spell(ctx, second, case_id=docket, notes=f"E.D. Mich. {docket}: jury verdict")
    assert a["court_case_id"] is not None
    assert b["court_case_id"] == a["court_case_id"]

    case = await _case(ctx, a["court_case_id"])
    assert (case["name"], case["court"], case["docket"]) == (
        "United States v. Doe",
        "E.D. Mich.",
        docket,
    )
    assert case["jurisdiction"] == "US_FEDERAL"
    assert case["docket_aliases"] == [f"{docket} (E.D. Mich.)"]
    by_member = {d["member_id"]: d["disposition"] for d in case["defendants"]}
    assert by_member == {first: "PLEADED", second: "CONVICTED"}
    assert len(case["spells"]) == 2


async def test_a_notable_state_file_makes_a_case_with_its_counts(ctx):
    member = await _member(ctx, "Shooter", "Beta Roe")
    file_no = f"{uuid.uuid4().int % 90000000 + 10000000}-FC"
    s1 = await _spell(ctx, member, case_id=file_no, notes=OTIS_MURDER)
    s2 = await _spell(ctx, member, case_id=file_no, notes=OTIS_FIREARM)
    assert s1["court_case_id"] and s2["court_case_id"] == s1["court_case_id"]
    case = await _case(ctx, s1["court_case_id"])
    assert (case["name"], case["court"], case["jurisdiction"]) == (
        "People v. Roe",
        "Wayne County Circuit Court",
        "US_STATE",
    )
    (d,) = case["defendants"]
    assert d["disposition"] == "PLEADED"
    assert [c["statute"] for c in d["charges"]] == ["MCL 750.317", "MCL 750.227BA"]


async def test_an_ordinary_state_file_stays_a_spell(ctx):
    member = await _member(ctx, "Carrier")
    spell = await _spell(
        ctx, member, case_id=f"{uuid.uuid4().int % 90000000 + 10000000}-FH", notes=OTIS_FIREARM
    )
    assert spell["court_case_id"] is None


async def test_a_second_defendant_makes_an_ordinary_file_a_case(ctx):
    file_no = f"{uuid.uuid4().int % 90000000 + 10000000}-FH"
    first = await _member(ctx, "One")
    second = await _member(ctx, "Two")
    s1 = await _spell(ctx, first, case_id=file_no, notes=OTIS_FIREARM)
    assert s1["court_case_id"] is None
    s2 = await _spell(ctx, second, case_id=file_no, notes=OTIS_FIREARM)
    assert s2["court_case_id"] is not None


async def test_an_unplaceable_reference_and_a_hand_link_are_left_alone(ctx):
    member = await _member(ctx, "Unplaced")
    no_court = await _spell(ctx, member, case_id="2:22-cr-20074", notes="210 months")
    assert no_court["court_case_id"] is None

    client, auth, uid = ctx
    chosen = (
        await client.post(
            "/api/v1/court-cases/",
            json={
                "universe_id": uid,
                "name": "Chosen",
                "jurisdiction": "OTHER",
                "court": "Elsewhere",
            },
            headers=auth,
        )
    ).json()
    linked = await _spell(
        ctx,
        member,
        case_id="3:21-cr-00036",
        notes="District of North Dakota",
        court_case_id=chosen["id"],
    )
    assert linked["court_case_id"] == chosen["id"]


async def test_changing_the_case_text_relinks(ctx):
    client, auth, uid = ctx
    member = await _member(ctx, "Moved", "Gamma Poe")
    spell = await _spell(ctx, member, case_id="nothing parseable")
    assert spell["court_case_id"] is None
    docket = f"4:24-cr-{uuid.uuid4().int % 90000 + 10000}"
    resp = await client.patch(
        f"/api/v1/members/{member}/incarcerations/{spell['id']}",
        params={"universe_id": uid},
        json={"case_id": docket, "notes": "20 years, conspiracy, M.D. Ga."},
        headers=auth,
    )
    assert resp.status_code == 200, resp.text
    case = await _case(ctx, resp.json()["court_case_id"])
    assert (case["court"], case["docket"]) == ("M.D. Ga.", docket)


async def test_the_working_caption_skips_a_generational_suffix(ctx):
    member = await _member(ctx, "Junior", "Delta Q. Moe Jr.")
    spell = await _spell(
        ctx, member, case_id=f"{uuid.uuid4().int % 90000000 + 10000000}-FC", notes=OTIS_MURDER
    )
    assert (await _case(ctx, spell["court_case_id"]))["name"] == "People v. Moe"


async def test_a_members_list_tells_two_files_apart_by_count_and_date(ctx):
    """Two homicide files against one man, pleaded in one deal: same caption,
    same court, same disposition. His list names each by its count and date."""
    client, auth, uid = ctx
    member = await _member(ctx, "Twice", "Epsilon Voe")
    early = OTIS_MURDER + "\nDate of offense: Jun 2, 2005"
    late = OTIS_MURDER + "\nDate of offense: Feb 14, 2011"
    firearm = OTIS_FIREARM + "\nDate of offense: Jun 2, 2005"
    f1 = f"{uuid.uuid4().int % 90000000 + 10000000}-FC"
    f2 = f"{uuid.uuid4().int % 90000000 + 10000000}-FC"
    await _spell(ctx, member, case_id=f1, notes=late)
    await _spell(ctx, member, case_id=f2, notes=firearm)
    await _spell(ctx, member, case_id=f2, notes=early)
    resp = await client.get(
        "/api/v1/court-cases/", params={"universe_id": uid, "member_id": member}, headers=auth
    )
    by_docket = {c["docket"]: c for c in resp.json()["items"]}
    assert by_docket[f1]["viewer_lead_charge"] == "Homicide - Murder, Second Degree"
    assert by_docket[f1]["viewer_offense_date"]["year"] == 2011
    # The firearm count came first, the murder is still the lead.
    assert by_docket[f2]["viewer_lead_charge"] == "Homicide - Murder, Second Degree"
    assert (
        by_docket[f2]["viewer_offense_date"]["year"],
        by_docket[f2]["viewer_offense_date"]["month"],
    ) == (2005, 6)


async def test_merge_charge_fills_a_missing_date_instead_of_repeating_the_count():
    from app.services.court_case_links import merge_charge

    undated = {"offense": "Robbery", "statute": "MCL 750.530", "offense_date": None}
    dated = {**undated, "offense_date": {"year": 2013, "precision": "Y", "approx": False}}
    assert merge_charge([undated], dated) == [dated]
    other = {
        "offense": "Robbery",
        "statute": "MCL 750.530",
        "offense_date": {"year": 2015, "precision": "Y", "approx": False},
    }
    assert merge_charge([dated], other) == [dated, other]
