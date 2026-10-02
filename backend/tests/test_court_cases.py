"""API integration tests for /api/v1/court-cases.

Every expected value is written out from the setup in the test itself: a case
covering one incident, one participant, one verdict. Nothing is read back from
the code under test to build an expectation.
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import create_user
from app.core.enums import GlobalRole

pytestmark = pytest.mark.asyncio(loop_scope="session")


def _uid() -> str:
    return uuid.uuid4().hex[:8]


class _Api:
    """A logged-in admin with the few calls these tests repeat."""

    def __init__(self, client: AsyncClient, token: str):
        self.client = client
        self.auth = {"Authorization": f"Bearer {token}"}

    async def post(self, path: str, body: dict, params: dict | None = None) -> dict:
        resp = await self.client.post(path, json=body, params=params, headers=self.auth)
        assert resp.status_code == 201, resp.text
        return resp.json()

    async def universe(self) -> tuple[str, str]:
        slug = f"uni-{_uid()}"
        u = await self.post("/api/v1/universes/", {"name": f"Uni {_uid()}", "slug": slug})
        return u["id"], slug

    async def member(self, universe_id: str, nickname: str) -> str:
        m = await self.post("/api/v1/members/", {"universe_id": universe_id, "nickname": nickname})
        return m["id"]

    async def case(self, universe_id: str, **fields) -> dict:
        body = {
            "universe_id": universe_id,
            "name": f"United States v. Doe {_uid()}",
            "jurisdiction": "US_FEDERAL",
            "court": "E.D. Mich.",
            **fields,
        }
        return await self.post("/api/v1/court-cases/", body)

    async def defendant(self, case: dict, **fields) -> dict:
        return await self.post(
            f"/api/v1/court-cases/{case['id']}/defendants",
            fields,
            params={"universe_id": case["universe_id"]},
        )

    async def acquitted(self, incident_id: str, universe_id: str, member_id: str) -> bool:
        resp = await self.client.get(
            f"/api/v1/incidents/{incident_id}",
            params={"universe_id": universe_id},
            headers=self.auth,
        )
        assert resp.status_code == 200, resp.text
        (p,) = [p for p in resp.json()["participants"] if p["member_id"] == member_id]
        return p["acquitted"]


@pytest.fixture
async def api(client: AsyncClient, db_session: AsyncSession) -> _Api:
    email = f"admin_{_uid()}@example.com"
    await create_user(db_session, email, "adminpass", GlobalRole.ADMIN)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "adminpass"})
    return _Api(client, resp.json()["access_token"])


async def _shooting(api: _Api, universe_id: str, shooter: str, *, acquitted=False) -> str:
    inc = await api.post(
        "/api/v1/incidents/",
        {
            "universe_id": universe_id,
            "type": "SHOOTING",
            "participants": [
                {
                    "member_id": shooter,
                    "role": "SHOOTER",
                    "outcome": "UNHARMED",
                    "acquitted": acquitted,
                }
            ],
        },
    )
    return inc["id"]


async def test_create_and_read_a_case_by_slug_or_id(api: _Api):
    uid, slug = await api.universe()
    docket = f"2:99-cr-{_uid()}"
    case = await api.case(
        uid,
        name="United States v. Doe et al.",
        docket=docket,
        docket_aliases=[f"  {docket}   (E.D. Mich.) ", f"{docket} (E.D. Mich.)"],
        filed_at={"year": 2017, "month": 10, "precision": "YM", "approx": False},
        judge="  Hon.  A. Judge ",
    )
    assert case["slug"] == "united-states-v-doe-et-al"
    assert case["universe_slug"] == slug
    assert case["kind"] == "CRIMINAL"
    # Whitespace collapsed, duplicates dropped.
    assert case["docket_aliases"] == [f"{docket} (E.D. Mich.)"]
    assert case["judge"] == "Hon. A. Judge"

    for ref in (case["id"], "united-states-v-doe-et-al"):
        resp = await api.client.get(
            f"/api/v1/court-cases/{ref}", params={"universe_id": uid}, headers=api.auth
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["id"] == case["id"]
        assert body["defendants"] == [] and body["incidents"] == [] and body["spells"] == []


async def test_court_and_docket_are_unique_together(api: _Api):
    uid, _ = await api.universe()
    docket = f"2:{_uid()}"
    await api.case(uid, docket=docket)
    resp = await api.client.post(
        "/api/v1/court-cases/",
        json={
            "universe_id": uid,
            "name": "Another name",
            "jurisdiction": "US_FEDERAL",
            "court": "E.D. Mich.",
            "docket": docket,
        },
        headers=api.auth,
    )
    assert resp.status_code == 409
    # The same number in another court is another case.
    await api.case(uid, docket=docket, court="W.D. Mich.")
    # And a case without a docket (a French trial known by name) is never a clash.
    await api.case(uid, jurisdiction="FR", court="Cour d'assises de Haute-Corse")
    await api.case(uid, jurisdiction="FR", court="Cour d'assises de Haute-Corse")


async def test_sets_and_sources_must_be_in_the_case_universe(api: _Api):
    here, _ = await api.universe()
    there, _ = await api.universe()
    foreign_set = await api.post("/api/v1/sets/", {"universe_id": there, "name": f"S {_uid()}"})
    foreign_source = await api.post(
        "/api/v1/sources/",
        {"universe_id": there, "url": "https://example.com/x", "title": "X", "reliability": "HIGH"},
    )
    for links in ({"set_ids": [foreign_set["id"]]}, {"source_ids": [foreign_source["id"]]}):
        resp = await api.client.post(
            "/api/v1/court-cases/",
            json={
                "universe_id": here,
                "name": "N",
                "jurisdiction": "US_STATE",
                "court": "Wayne County Circuit Court",
                **links,
            },
            headers=api.auth,
        )
        assert resp.status_code == 422, links


async def test_a_case_can_cover_an_incident_in_another_universe(api: _Api):
    home, _ = await api.universe()
    away, away_slug = await api.universe()
    shooter = await api.member(home, "Traveller")
    incident = await _shooting(api, away, shooter)
    case = await api.case(home, incident_ids=[incident])
    resp = await api.client.get(
        f"/api/v1/court-cases/{case['id']}", params={"universe_id": home}, headers=api.auth
    )
    (inc,) = resp.json()["incidents"]
    assert inc["id"] == incident
    assert inc["universe_slug"] == away_slug
    # The incident's own list of cases finds it from the other side.
    resp = await api.client.get(
        "/api/v1/court-cases/",
        params={"universe_id": away, "incident_id": incident},
        headers=api.auth,
    )
    assert [c["id"] for c in resp.json()["items"]] == [case["id"]]


async def test_a_parent_case_cannot_close_a_loop(api: _Api):
    uid, _ = await api.universe()
    trial = await api.case(uid)
    appeal = await api.case(uid, kind="APPEAL", parent_case_id=trial["id"])
    resp = await api.client.patch(
        f"/api/v1/court-cases/{trial['id']}",
        params={"universe_id": uid},
        json={"parent_case_id": appeal["id"]},
        headers=api.auth,
    )
    assert resp.status_code == 422
    detail = (
        await api.client.get(
            f"/api/v1/court-cases/{trial['id']}", params={"universe_id": uid}, headers=api.auth
        )
    ).json()
    assert [c["id"] for c in detail["children"]] == [appeal["id"]]


async def test_defendants_named_or_labelled(api: _Api):
    home, home_slug = await api.universe()
    court_universe, _ = await api.universe()
    member = await api.member(home, "Named One")
    case = await api.case(court_universe)

    named = await api.defendant(
        case,
        member_id=member,
        defendant_number="D-1",
        disposition="CONVICTED",
        charges=[{"count": 1, "statute": "18 U.S.C. 1962(d)", "offense": "RICO conspiracy"}],
        sentence_months=420,
        supervised_release_months=60,
    )
    assert named["sentence_months"] == 420
    unnamed = await api.defendant(case, label="D-7", disposition="PLEADED", cooperated=True)
    assert unnamed["member_id"] is None and unnamed["cooperated"] is True

    resp = await api.client.post(
        f"/api/v1/court-cases/{case['id']}/defendants",
        params={"universe_id": court_universe},
        json={"disposition": "PENDING"},
        headers=api.auth,
    )
    assert resp.status_code == 422  # neither a member nor a label
    resp = await api.client.post(
        f"/api/v1/court-cases/{case['id']}/defendants",
        params={"universe_id": court_universe},
        json={"member_id": member},
        headers=api.auth,
    )
    assert resp.status_code == 409  # the same member twice

    detail = (
        await api.client.get(
            f"/api/v1/court-cases/{case['id']}",
            params={"universe_id": court_universe},
            headers=api.auth,
        )
    ).json()
    by_number = {d["defendant_number"] or d["label"]: d for d in detail["defendants"]}
    assert by_number["D-1"]["member_name"] == "Named One"
    assert by_number["D-1"]["member_universe_slug"] == home_slug
    assert by_number["D-1"]["charges"][0]["statute"] == "18 U.S.C. 1962(d)"
    assert by_number["D-7"]["member_name"] is None

    # The member's own list reaches the case in the other universe, with his part in it.
    resp = await api.client.get(
        "/api/v1/court-cases/", params={"universe_id": home, "member_id": member}, headers=api.auth
    )
    (item,) = resp.json()["items"]
    assert item["id"] == case["id"]
    assert item["viewer_disposition"] == "CONVICTED"
    assert item["viewer_sentence_months"] == 420
    assert item["defendant_count"] == 2


async def test_an_acquittal_sets_the_participant_flag_and_a_conviction_clears_it(api: _Api):
    uid, _ = await api.universe()
    shooter = await api.member(uid, "Shooter")
    incident = await _shooting(api, uid, shooter)
    case = await api.case(uid, incident_ids=[incident])
    assert await api.acquitted(incident, uid, shooter) is False

    d = await api.defendant(case, member_id=shooter, disposition="ACQUITTED")
    assert await api.acquitted(incident, uid, shooter) is True

    resp = await api.client.patch(
        f"/api/v1/court-cases/{case['id']}/defendants/{d['id']}",
        params={"universe_id": uid},
        json={"disposition": "CONVICTED"},
        headers=api.auth,
    )
    assert resp.status_code == 200, resp.text
    assert await api.acquitted(incident, uid, shooter) is False


async def test_an_acquittal_another_case_contradicts_does_not_clear(api: _Api):
    # Acquitted by the state, convicted federally of the same shooting.
    uid, _ = await api.universe()
    shooter = await api.member(uid, "Twice Tried")
    incident = await _shooting(api, uid, shooter)
    state = await api.case(
        uid, jurisdiction="US_STATE", court="Wayne County Circuit Court", incident_ids=[incident]
    )
    federal = await api.case(uid, incident_ids=[incident])
    await api.defendant(state, member_id=shooter, disposition="ACQUITTED")
    assert await api.acquitted(incident, uid, shooter) is True
    await api.defendant(federal, member_id=shooter, disposition="CONVICTED")
    assert await api.acquitted(incident, uid, shooter) is False


async def test_a_flag_no_case_speaks_to_is_left_alone(api: _Api):
    # 18 flags were set by hand before cases existed; a case about someone else
    # in the same incident must not touch them.
    uid, _ = await api.universe()
    cleared = await api.member(uid, "Cleared By Hand")
    other = await api.member(uid, "Other")
    inc = await api.post(
        "/api/v1/incidents/",
        {
            "universe_id": uid,
            "type": "SHOOTING",
            "participants": [
                {"member_id": cleared, "role": "SHOOTER", "outcome": "UNHARMED", "acquitted": True},
                {"member_id": other, "role": "ASSISTED", "outcome": "UNHARMED"},
            ],
        },
    )
    case = await api.case(uid, incident_ids=[inc["id"]])
    await api.defendant(case, member_id=other, disposition="CONVICTED")
    assert await api.acquitted(inc["id"], uid, cleared) is True
    assert await api.acquitted(inc["id"], uid, other) is False


async def test_the_verdict_survives_an_incident_edit_and_releases_on_removal(api: _Api):
    uid, _ = await api.universe()
    shooter = await api.member(uid, "Acquitted")
    incident = await _shooting(api, uid, shooter)
    case = await api.case(uid, incident_ids=[incident])
    d = await api.defendant(case, member_id=shooter, disposition="ACQUITTED")

    # The incident form sends the participant list back whole, flag included; a
    # payload that says False must not undo the court's acquittal.
    resp = await api.client.patch(
        f"/api/v1/incidents/{incident}",
        params={"universe_id": uid},
        json={
            "participants": [
                {"member_id": shooter, "role": "SHOOTER", "outcome": "UNHARMED", "acquitted": False}
            ]
        },
        headers=api.auth,
    )
    assert resp.status_code == 200, resp.text
    assert await api.acquitted(incident, uid, shooter) is True

    # Unlinking the incident takes the verdict with it.
    resp = await api.client.patch(
        f"/api/v1/court-cases/{case['id']}",
        params={"universe_id": uid},
        json={"incident_ids": []},
        headers=api.auth,
    )
    assert resp.status_code == 200, resp.text
    assert await api.acquitted(incident, uid, shooter) is False

    # Linked again it comes back; then deleting the defendant releases it.
    await api.client.patch(
        f"/api/v1/court-cases/{case['id']}",
        params={"universe_id": uid},
        json={"incident_ids": [incident]},
        headers=api.auth,
    )
    assert await api.acquitted(incident, uid, shooter) is True
    resp = await api.client.delete(
        f"/api/v1/court-cases/{case['id']}/defendants/{d['id']}",
        params={"universe_id": uid},
        headers=api.auth,
    )
    assert resp.status_code == 204
    assert await api.acquitted(incident, uid, shooter) is False


async def test_deleting_a_case_releases_its_verdicts(api: _Api):
    uid, _ = await api.universe()
    shooter = await api.member(uid, "Released")
    incident = await _shooting(api, uid, shooter)
    case = await api.case(uid, incident_ids=[incident])
    await api.defendant(case, member_id=shooter, disposition="ACQUITTED")
    assert await api.acquitted(incident, uid, shooter) is True
    resp = await api.client.delete(
        f"/api/v1/court-cases/{case['id']}", params={"universe_id": uid}, headers=api.auth
    )
    assert resp.status_code == 204
    assert await api.acquitted(incident, uid, shooter) is False


async def test_deleting_a_member_keeps_the_defendant_row_under_his_name(api: _Api):
    uid, _ = await api.universe()
    member = await api.member(uid, "Gone From The Wiki")
    case = await api.case(uid)
    await api.defendant(case, member_id=member, disposition="CONVICTED")
    resp = await api.client.delete(
        f"/api/v1/members/{member}", params={"universe_id": uid}, headers=api.auth
    )
    assert resp.status_code == 204, resp.text
    detail = (
        await api.client.get(
            f"/api/v1/court-cases/{case['id']}", params={"universe_id": uid}, headers=api.auth
        )
    ).json()
    (d,) = detail["defendants"]
    assert d["member_id"] is None
    assert d["label"] == "Gone From The Wiki"
    assert d["disposition"] == "CONVICTED"


async def test_a_spell_links_to_its_case(api: _Api):
    uid, _ = await api.universe()
    member = await api.member(uid, "Serving")
    case = await api.case(uid)
    spell = await api.post(
        f"/api/v1/members/{member}/incarcerations",
        {
            "from_date": {"year": 2019, "precision": "Y", "approx": False},
            "facility": "FCI Milan",
            "case_id": "2:99-cr-1 (E.D. Mich.)",
            "court_case_id": case["id"],
        },
        params={"universe_id": uid},
    )
    assert spell["court_case_id"] == case["id"]
    assert spell["case_id"] == "2:99-cr-1 (E.D. Mich.)"
    detail = (
        await api.client.get(
            f"/api/v1/court-cases/{case['id']}", params={"universe_id": uid}, headers=api.auth
        )
    ).json()
    (s,) = detail["spells"]
    assert (s["member_name"], s["facility"]) == ("Serving", "FCI Milan")

    resp = await api.client.post(
        f"/api/v1/members/{member}/incarcerations",
        params={"universe_id": uid},
        json={"court_case_id": str(uuid.uuid4())},
        headers=api.auth,
    )
    assert resp.status_code == 422


async def test_search_finds_a_case_by_any_spelling_of_its_docket(api: _Api):
    uid, _ = await api.universe()
    number = f"{_uid()}-FC"
    case = await api.case(
        uid,
        jurisdiction="US_STATE",
        court="Wayne County Circuit Court",
        docket=number,
        docket_aliases=[f"Wayne Circuit {number}"],
    )
    for q in (number, f"Circuit {number[:6]}", case["name"][-8:]):
        resp = await api.client.get(
            "/api/v1/court-cases/search", params={"universe_id": uid, "q": q}, headers=api.auth
        )
        assert [c["id"] for c in resp.json()] == [case["id"]], q


async def test_set_list_and_source_citation_count(api: _Api):
    uid, _ = await api.universe()
    gang_set = await api.post("/api/v1/sets/", {"universe_id": uid, "name": f"S {_uid()}"})
    source = await api.post(
        "/api/v1/sources/",
        {
            "universe_id": uid,
            "url": "https://example.com/doj",
            "title": "DOJ",
            "reliability": "HIGH",
        },
    )
    case = await api.case(uid, set_ids=[gang_set["id"]], source_ids=[source["id"]])
    resp = await api.client.get(
        "/api/v1/court-cases/",
        params={"universe_id": uid, "set_id": gang_set["id"]},
        headers=api.auth,
    )
    assert [c["id"] for c in resp.json()["items"]] == [case["id"]]
    resp = await api.client.get("/api/v1/sources/", params={"universe_id": uid}, headers=api.auth)
    (row,) = [s for s in resp.json()["items"] if s["id"] == source["id"]]
    assert row["court_case_count"] == 1


async def test_editing_a_docket_into_another_case_is_a_conflict(api: _Api):
    uid, _ = await api.universe()
    taken = f"2:{_uid()}"
    await api.case(uid, docket=taken)
    other = await api.case(uid, docket=f"2:{_uid()}")
    resp = await api.client.patch(
        f"/api/v1/court-cases/{other['id']}",
        params={"universe_id": uid},
        json={"docket": taken},
        headers=api.auth,
    )
    assert resp.status_code == 409
