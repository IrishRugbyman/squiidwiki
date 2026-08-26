"""Parser tests for the rebuilt MDOC OTIS profile page.

The fixture's *markup* is copied from a real OTIS profile so the selectors under
test are the real ones; every *value* in it is invented, because a real
offender's record must not live in this repo. Expected values below are read
off the fixture by hand - never produced by running the parser.
"""

import base64
import io
from pathlib import Path

import pytest
from PIL import Image

from app.core.enums import DatePrecision
from app.core.fuzzy_date import FuzzyDate
from app.services.mdoc import (
    MdocParseError,
    MdocProfile,
    MdocSentence,
    decode_data_uri,
    derive_spells,
    parse_mdoc_html,
    parse_mdoc_results,
)

FIXTURE = Path(__file__).parent / "fixtures" / "otis_profile.html"


def _jpeg_bytes() -> bytes:
    """A real (tiny) JPEG, so the magic-byte sniff has something honest to read."""
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (10, 20, 30)).save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture(scope="module")
def photo_bytes() -> bytes:
    return _jpeg_bytes()


@pytest.fixture(scope="module")
def profile_html(photo_bytes: bytes) -> str:
    # Declared as image/gif on purpose: OTIS mislabels its JPEGs exactly so.
    uri = "data:image/gif;base64," + base64.b64encode(photo_bytes).decode("ascii")
    return FIXTURE.read_text(encoding="utf-8").replace("__PHOTO_DATA_URI__", uri)


@pytest.fixture(scope="module")
def profile(profile_html: str):
    return parse_mdoc_html(profile_html)


class TestBiographical:
    def test_name_is_title_cased_and_despaced(self, profile):
        # Fixture holds "JORDAN  AVERY REED  " - doubled and trailing spaces.
        assert profile.legal_name == "Jordan Avery Reed"

    def test_identifiers(self, profile):
        assert profile.mdoc_number == "111222"
        assert profile.sid_number == "9998887A"

    def test_dob_ignores_the_trailing_age(self, profile):
        # Fixture reads "3/9/1991 (35)".
        assert (profile.dob.year, profile.dob.month, profile.dob.day) == (1991, 3, 9)

    def test_physical_description(self, profile):
        assert profile.race == "Black"
        assert profile.sex == "Male"  # label id says Gender, page says Sex
        assert profile.hair == "Black"
        assert profile.eyes == "Brown"
        assert profile.height == "6' 1\""
        assert profile.weight == "180 lbs"

    def test_image_date(self, profile):
        d = profile.image_date
        assert (d.year, d.month, d.day) == (2024, 12, 2)


class TestStatus:
    def test_status_block(self, profile):
        assert profile.status == "Prisoner"
        assert profile.facility == "Example Correctional Facility"
        assert profile.security_level == "IV"

    def test_release_dates(self, profile):
        erd = profile.earliest_release_date
        assert (erd.year, erd.month, erd.day) == (2031, 4, 15)
        dis = profile.discharge_date
        assert (dis.year, dis.month, dis.day) == (2046, 4, 15)

    def test_max_discharge_is_the_discharge_date_while_still_serving(self, profile):
        assert profile.max_discharge_date == profile.discharge_date

    def test_max_discharge_is_none_once_discharged(self, profile_html):
        """The same label means opposite things depending on status.

        For someone already out, Discharge Date is the day they left - reading
        it as a maximum would misdate them by decades, so it must not surface.
        """
        discharged = profile_html.replace(
            "<td>Current Status:</td><td>Prisoner</td>",
            "<td>Current Status:</td><td>Discharged</td>",
        )
        parsed = parse_mdoc_html(discharged)
        assert parsed.status == "Discharged"
        assert parsed.discharge_date is not None
        assert parsed.max_discharge_date is None


class TestLists:
    def test_aliases(self, profile):
        assert profile.aliases == ["JAY", "JORDAN A REED", "JORDAN NMN REED"]

    def test_marks_keep_their_tattoo_text(self, profile):
        assert "Tattoo- Lower Left Arm - Example Crew" in profile.marks
        assert len(profile.marks) == 3

    def test_supervision_none_is_not_read_as_an_entry(self, profile):
        # "None" is OTIS's way of saying the section is empty.
        assert all(m.lower() != "none" for m in profile.marks)


class TestSentences:
    def test_counts_by_kind_and_state(self, profile):
        # Fixture: prison Active 1 + Inactive 1; probation Active none + Inactive 1.
        prison = [s for s in profile.sentences if s.kind == "prison"]
        probation = [s for s in profile.sentences if s.kind == "probation"]
        assert len(prison) == 2
        assert len(probation) == 1
        assert [s.active for s in prison] == [True, False]
        assert probation[0].active is False

    def test_probation_active_none_produces_no_sentence(self, profile):
        assert not [s for s in profile.sentences if s.kind == "probation" and s.active]

    def test_active_prison_sentence_detail(self, profile):
        s = next(x for x in profile.sentences if x.kind == "prison" and x.active)
        assert s.offense == "Weapons - Carrying Concealed"
        assert s.mcl == ["750.227", "769.12"]
        assert s.court_file == "20001111-01-FH"
        assert s.county == "Wayne"
        assert s.conviction_type == "Jury"
        assert s.minimum_sentence == "5 years 0 months 0 days"
        assert s.maximum_sentence == "20 years 0 months"
        assert (s.date_of_offense.year, s.date_of_offense.month, s.date_of_offense.day) == (
            2020,
            6,
            1,
        )
        # An active sentence has not been discharged.
        assert s.date_of_discharge is None
        assert s.discharge_reason is None

    def test_inactive_sentence_carries_discharge_detail(self, profile):
        s = next(x for x in profile.sentences if x.kind == "prison" and not x.active)
        assert s.offense == "Home Invasion - 2nd Degree"
        assert s.mcl == ["750.110A3"]
        assert s.discharge_reason == "Offender Discharge"
        assert (s.date_of_discharge.year, s.date_of_discharge.month) == (2019, 8)

    def test_blank_minimum_sentence_is_none_not_empty_string(self, profile):
        s = next(x for x in profile.sentences if x.kind == "probation")
        assert s.minimum_sentence is None


class TestPhoto:
    def test_photo_bytes_round_trip(self, profile, photo_bytes):
        assert profile.photo is not None
        assert profile.photo.data == photo_bytes

    def test_declared_mime_is_ignored_in_favour_of_the_magic_bytes(self, profile):
        """The fixture declares image/gif over a JPEG payload, as OTIS does."""
        assert profile.photo.content_type == "image/jpeg"

    def test_data_uri_round_trip(self, profile, photo_bytes):
        again = decode_data_uri(profile.photo.as_data_uri())
        assert again.data == photo_bytes
        assert again.content_type == "image/jpeg"

    def test_non_image_payload_is_rejected(self):
        uri = "data:image/jpeg;base64," + base64.b64encode(b"not an image").decode()
        with pytest.raises(ValueError, match="not a recognized image"):
            decode_data_uri(uri)

    def test_undecodable_payload_is_rejected(self):
        with pytest.raises(ValueError):
            decode_data_uri("data:image/jpeg;base64,")


class TestFailureModes:
    def test_search_form_instead_of_profile_is_a_parse_error(self):
        """The failure that actually happens: an expired session or a search
        matching nobody returns the search form, with a 200."""
        form = "<html><head><title>OTIS Offender Search - OTIS</title></head><body><form></form></body></html>"
        with pytest.raises(MdocParseError, match="Name"):
            parse_mdoc_html(form)

    def test_missing_dob_is_a_parse_error(self, profile_html):
        stripped = profile_html.replace("Results_ProfileData_DateOfBirth", "SomethingElse")
        with pytest.raises(MdocParseError, match="Date of Birth"):
            parse_mdoc_html(stripped)

    def test_empty_html_is_a_parse_error(self):
        with pytest.raises(MdocParseError):
            parse_mdoc_html("")


def _ymd(year: int, month: int, day: int) -> FuzzyDate:
    return FuzzyDate(year=year, month=month, day=day, precision=DatePrecision.YMD)


def _sentence(**kw) -> MdocSentence:
    """A prison sentence with everything blank but what the test names."""
    kw.setdefault("kind", "prison")
    kw.setdefault("active", True)
    return MdocSentence(**kw)


def _profile(sentences, **kw) -> MdocProfile:
    """A profile carrying only what a spell derivation reads."""
    kw.setdefault("legal_name", "Test Offender")
    kw.setdefault("dob", _ymd(1990, 1, 1))
    return MdocProfile(sentences=list(sentences), **kw)


class TestDeriveSpells:
    """The sentence rows are the only record a discharged offender has.

    Values here are written by hand from the scenario each test describes, or
    read off the fixture; none is produced by running the derivation.
    """

    def test_fixture_yields_one_spell_per_prison_sentence(self, profile):
        # Fixture prison sentences: active (sentenced 1/12/2021, undischarged)
        # and inactive (sentenced 9/9/2015, discharged 8/1/2019).
        spells = derive_spells(profile)
        assert len(spells) == 2
        assert [s.case_id for s in spells] == ["20001111-01-FH", "15009999-FH"]

    def test_probation_is_never_a_spell(self, profile):
        """The fixture has a probation sentence; probation is not custody."""
        assert any(s.kind == "probation" for s in profile.sentences)
        assert len(derive_spells(profile)) == 2

    def test_running_sentence_carries_its_start_and_no_end(self, profile):
        running = derive_spells(profile)[0]
        assert running.from_date == _ymd(2021, 1, 12)
        assert running.to_date is None

    def test_served_sentence_carries_the_date_it_actually_ended(self, profile):
        served = derive_spells(profile)[1]
        assert served.from_date == _ymd(2015, 9, 9)
        assert served.to_date == _ymd(2019, 8, 1)

    def test_projections_land_on_the_running_sentence_only(self, profile):
        """Earliest release, max discharge and facility are offender-level.

        Copying them onto every spell would put the same release on the
        calendar once per sentence and would date the served spell wrongly.
        """
        running, served = derive_spells(profile)
        assert running.earliest_release_date == _ymd(2031, 4, 15)
        assert running.max_discharge_date == _ymd(2046, 4, 15)
        assert running.facility == "Example Correctional Facility"
        assert served.earliest_release_date is None
        assert served.max_discharge_date is None
        assert served.facility is None

    def test_discharged_offender_with_an_empty_status_block_still_yields_spells(self):
        """The bug this exists for.

        Once someone is out, OTIS blanks Assigned Location and Earliest Release
        Date, and max_discharge_date reads as None by design. Reading only the
        status block therefore imported nothing for anyone not currently inside.
        """
        prof = _profile(
            [
                _sentence(
                    active=False,
                    court_file="11002233-FC",
                    date_of_sentence=_ymd(2011, 3, 4),
                    date_of_discharge=_ymd(2015, 8, 20),
                )
            ],
            status="Discharged",
        )
        assert prof.facility is None
        assert prof.max_discharge_date is None

        (spell,) = derive_spells(prof)
        assert spell.from_date == _ymd(2011, 3, 4)
        assert spell.to_date == _ymd(2015, 8, 20)
        assert spell.case_id == "11002233-FC"

    def test_concurrent_open_sentences_produce_one_projected_release(self):
        prof = _profile(
            [
                _sentence(court_file="A", date_of_sentence=_ymd(2019, 5, 1)),
                _sentence(court_file="B", date_of_sentence=_ymd(2021, 7, 9)),
                _sentence(court_file="C", date_of_sentence=_ymd(2020, 2, 2)),
            ],
            facility="Example Correctional Facility",
            earliest_release_date=_ymd(2030, 1, 1),
        )
        spells = derive_spells(prof)
        assert [s.case_id for s in spells] == ["A", "B", "C"]
        # The latest start (B, 2021) is the one the projection belongs to.
        assert [s.earliest_release_date for s in spells] == [None, _ymd(2030, 1, 1), None]
        assert [s.facility for s in spells] == [None, "Example Correctional Facility", None]

    def test_the_projection_lands_on_the_controlling_sentence(self):
        """Ricardo Stanford's real shape, and the bug it exposed.

        Concurrent counts are handed down on one day, so a start-date tiebreak
        alone is arbitrary - it put a 2051 max discharge beside a two-year
        felony-firearm count while the 20-to-35 assault that actually decides
        the release date showed nothing.
        """
        same_day = _ymd(2015, 9, 3)
        prof = _profile(
            [
                _sentence(
                    court_file="AWIM",
                    date_of_sentence=same_day,
                    minimum_sentence="20 years 0 months 0 days",
                    maximum_sentence="35 years 0 months",
                ),
                _sentence(
                    court_file="FELFIRE",
                    date_of_sentence=same_day,
                    minimum_sentence="2 years 0 months 0 days",
                    maximum_sentence="2 years 0 months",
                ),
            ],
            facility="St. Louis Correctional Facility",
            earliest_release_date=_ymd(2036, 11, 12),
        )
        awim, felfire = derive_spells(prof)
        assert awim.earliest_release_date == _ymd(2036, 11, 12)
        assert awim.facility == "St. Louis Correctional Facility"
        assert felfire.earliest_release_date is None
        assert felfire.facility is None

    def test_a_life_count_outranks_any_term_of_years(self):
        prof = _profile(
            [
                _sentence(court_file="YEARS", maximum_sentence="40 years 0 months"),
                _sentence(court_file="LIFE", maximum_sentence="Life"),
            ],
            earliest_release_date=_ymd(2050, 1, 1),
        )
        years, life = derive_spells(prof)
        assert life.life_sentence is True
        assert years.earliest_release_date is None
        # life_sentence nulls the release dates at the CRUD layer, but the
        # facility still belongs on this row rather than on the shorter count.
        assert life.earliest_release_date == _ymd(2050, 1, 1)

    def test_a_served_sentence_never_takes_the_projection(self):
        """Even when it started later than the one still running."""
        prof = _profile(
            [
                _sentence(court_file="OPEN", date_of_sentence=_ymd(2018, 1, 1)),
                _sentence(
                    active=False,
                    court_file="SERVED",
                    date_of_sentence=_ymd(2022, 1, 1),
                    date_of_discharge=_ymd(2024, 1, 1),
                ),
            ],
            earliest_release_date=_ymd(2030, 1, 1),
        )
        spells = derive_spells(prof)
        assert spells[0].earliest_release_date == _ymd(2030, 1, 1)
        assert spells[1].earliest_release_date is None

    def test_life_maximum_is_flagged_as_a_life_sentence(self):
        prof = _profile([_sentence(minimum_sentence="25 years 0 months", maximum_sentence="Life")])
        assert derive_spells(prof)[0].life_sentence is True

    def test_a_term_of_years_is_not_a_life_sentence(self):
        prof = _profile([_sentence(minimum_sentence="5 years", maximum_sentence="20 years")])
        assert derive_spells(prof)[0].life_sentence is False

    def test_no_prison_sentences_falls_back_to_the_status_block(self):
        """A currently-serving prisoner whose sentence markup did not parse.

        Better one bare spell with the facility and release dates than nothing.
        """
        prof = _profile(
            [_sentence(kind="probation", active=False)],
            facility="Example Correctional Facility",
            earliest_release_date=_ymd(2029, 6, 1),
        )
        (spell,) = derive_spells(prof)
        assert spell.facility == "Example Correctional Facility"
        assert spell.earliest_release_date == _ymd(2029, 6, 1)
        assert spell.from_date is None
        assert spell.case_id is None

    def test_a_probation_only_profile_yields_nothing(self):
        """The shape that looks like a bug and is not.

        OTIS covers probationers as well as prisoners. A discharged probationer
        has an empty Status block *and* an empty Prison Sentences section, so
        zero spells is the correct answer and the member page correctly reads
        "No incarceration records". Loosening the filter to make this import
        look productive would put supervision on the page as time served.
        """
        prof = _profile(
            [
                _sentence(
                    kind="probation",
                    active=False,
                    court_file="11001386-01",
                    date_of_sentence=_ymd(2011, 3, 29),
                    date_of_discharge=_ymd(2012, 3, 2),
                ),
                _sentence(
                    kind="probation",
                    active=False,
                    court_file="17003612-01-FH",
                    date_of_sentence=_ymd(2017, 6, 6),
                    date_of_discharge=_ymd(2019, 6, 13),
                ),
            ],
            status="Discharged",
        )
        assert derive_spells(prof) == []

    def test_an_offender_with_nothing_to_import_yields_no_spells(self):
        assert derive_spells(_profile([])) == []

    def test_notes_state_the_sentence_facts(self, profile):
        served = derive_spells(profile)[1]
        assert served.notes is not None
        lines = served.notes.splitlines()
        assert "Offense: Home Invasion - 2nd Degree" in lines
        assert "MCL 750.110A3" in lines
        assert "County: Oakland" in lines
        assert "Conviction type: Plea" in lines
        assert "Sentence: 2 years 0 months 0 days to 15 years 0 months" in lines
        assert "Discharge reason: Offender Discharge" in lines

    def test_notes_name_no_source_and_hedge_nothing(self, profile):
        """House rule: entity text that renders on a page states the fact and stops."""
        for spell in derive_spells(profile):
            assert spell.notes is not None
            lowered = spell.notes.lower()
            for banned in ("otis", "mdoc", "imported", "according to", "appears to", "reportedly"):
                assert banned not in lowered

    def test_a_sentence_with_no_detail_gets_no_notes(self):
        prof = _profile([_sentence(date_of_sentence=_ymd(2020, 1, 1))])
        assert derive_spells(prof)[0].notes is None


# ---------------------------------------------------------------------------
# fetch_mdoc_profile: the session walk and its failure modes.
#
# Stubbed rather than mocked with a library: the point is to pin down how the
# code reacts to responses OTIS really produces, all of which were observed
# live against mdocweb.state.mi.us before being written down here.
# ---------------------------------------------------------------------------

import httpx  # noqa: E402

from app.services import mdoc as mdoc_service  # noqa: E402

SEARCH_FORM = "<html><head><title>OTIS Offender Search - OTIS</title></head><body></body></html>"
RESULTS = "<html><head><title>Results Page - OTIS</title></head><body></body></html>"
RUNTIME_ERROR = "<html><head><title>Runtime Error</title></head><body></body></html>"


class _StubClient:
    """Stands in for httpx.AsyncClient. `posts` is consumed in order:
    the search POST first, then the LoadProfile POST."""

    def __init__(self, posts, *, raise_on_get=None, **kwargs):
        self._posts = list(posts)
        self._raise_on_get = raise_on_get
        self.requested = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, **kwargs):
        if self._raise_on_get:
            raise self._raise_on_get
        return httpx.Response(200, text=SEARCH_FORM, request=httpx.Request("GET", url))

    async def post(self, url, data=None, **kwargs):
        self.requested.append((url, data))
        resp = self._posts.pop(0)
        # httpx refuses raise_for_status() on a response with no request bound,
        # so give the stub one rather than dropping the check from the code.
        if resp._request is None:
            resp._request = httpx.Request("POST", url)
        return resp


def _install(monkeypatch, posts, raise_on_get=None):
    """Every attempt sees the same responses. Retry delays are zeroed so a test
    of the give-up path does not spend the real backoff sleeping."""
    holder = {"clients": 0}

    def factory(**kwargs):
        holder["clients"] += 1
        holder["client"] = _StubClient(posts, raise_on_get=raise_on_get, **kwargs)
        return holder["client"]

    monkeypatch.setattr(mdoc_service.httpx, "AsyncClient", factory)
    monkeypatch.setattr(mdoc_service, "PROFILE_RETRY_DELAYS", (0, 0))
    return holder


def _install_per_attempt(monkeypatch, attempts):
    """Give each session-walk attempt its own responses, consumed in order.

    OTIS's transient failure is per-session, so reproducing it needs the second
    attempt to answer differently from the first - which the shared-list stub
    above cannot express.
    """
    holder = {"clients": 0}
    remaining = list(attempts)

    def factory(**kwargs):
        holder["clients"] += 1
        holder["client"] = _StubClient(remaining.pop(0), **kwargs)
        return holder["client"]

    monkeypatch.setattr(mdoc_service.httpx, "AsyncClient", factory)
    monkeypatch.setattr(mdoc_service, "PROFILE_RETRY_DELAYS", (0, 0))
    return holder


class TestFetchProfile:
    @pytest.mark.asyncio
    async def test_happy_path_returns_the_parsed_profile(self, monkeypatch, profile_html):
        _install(
            monkeypatch,
            [httpx.Response(200, text=RESULTS), httpx.Response(200, text=profile_html)],
        )
        parsed = await mdoc_service.fetch_mdoc_profile("111222", proxy="socks5://x:1")
        assert parsed.legal_name == "Jordan Avery Reed"
        assert parsed.mdoc_number == "111222"

    @pytest.mark.asyncio
    async def test_load_profile_is_posted_with_the_number(self, monkeypatch, profile_html):
        holder = _install(
            monkeypatch,
            [httpx.Response(200, text=RESULTS), httpx.Response(200, text=profile_html)],
        )
        await mdoc_service.fetch_mdoc_profile("111222", proxy="socks5://x:1")
        url, data = holder["client"].requested[-1]
        assert url.endswith("/Results")
        assert data == {"action:LoadProfile": "111222"}

    @pytest.mark.asyncio
    async def test_a_flaky_search_step_does_not_fail_the_lookup(self, monkeypatch, profile_html):
        """OTIS sometimes bounces the search back to the form for a real
        offender, then loads the profile fine. Observed live; must not fail."""
        _install(
            monkeypatch,
            [httpx.Response(200, text=SEARCH_FORM), httpx.Response(200, text=profile_html)],
        )
        parsed = await mdoc_service.fetch_mdoc_profile("111222", proxy="socks5://x:1")
        assert parsed.mdoc_number == "111222"

    @pytest.mark.asyncio
    async def test_unknown_number_reports_a_missing_offender_not_a_proxy_fault(self, monkeypatch):
        """OTIS answers 500 for a number that doesn't exist, and blaming the
        proxy for that would send someone debugging the wrong thing."""
        _install(
            monkeypatch,
            [httpx.Response(200, text=RESULTS), httpx.Response(500, text=RUNTIME_ERROR)],
        )
        with pytest.raises(mdoc_service.MdocFetchError, match="no offender with MDOC number"):
            await mdoc_service.fetch_mdoc_profile("999999", proxy="socks5://x:1")

    @pytest.mark.asyncio
    async def test_a_profile_for_the_wrong_person_is_refused(self, monkeypatch, profile_html):
        """The fixture is offender 111222; ask for someone else and the
        mismatch must abort rather than attach another man's convictions."""
        _install(
            monkeypatch,
            [httpx.Response(200, text=RESULTS), httpx.Response(200, text=profile_html)],
        )
        with pytest.raises(mdoc_service.MdocFetchError, match="may be someone else"):
            await mdoc_service.fetch_mdoc_profile("352482", proxy="socks5://x:1")

    @pytest.mark.asyncio
    async def test_search_form_instead_of_a_profile_is_a_fetch_error(self, monkeypatch):
        _install(
            monkeypatch,
            [httpx.Response(200, text=RESULTS), httpx.Response(200, text=SEARCH_FORM)],
        )
        with pytest.raises(mdoc_service.MdocFetchError, match="did not load a profile"):
            await mdoc_service.fetch_mdoc_profile("111222", proxy="socks5://x:1")

    @pytest.mark.asyncio
    async def test_a_rejected_session_is_retried_on_a_clean_one(self, monkeypatch, profile_html):
        """The failure that broke real imports.

        OTIS rejects a freshly-built session intermittently and answers
        LoadProfile with the search form. Measured live at 2 failures in 8
        single attempts against a profile that exists, so giving up on the
        first bounce killed roughly one import in four.
        """
        holder = _install_per_attempt(
            monkeypatch,
            [
                [httpx.Response(200, text=RESULTS), httpx.Response(200, text=SEARCH_FORM)],
                [httpx.Response(200, text=RESULTS), httpx.Response(200, text=profile_html)],
            ],
        )
        parsed = await mdoc_service.fetch_mdoc_profile("111222", proxy="socks5://x:1")
        assert parsed.mdoc_number == "111222"
        # A fresh client per attempt: what failed is the session, so reusing its
        # cookies would just reproduce the rejection.
        assert holder["clients"] == 2

    @pytest.mark.asyncio
    async def test_giving_up_takes_every_attempt(self, monkeypatch):
        holder = _install(
            monkeypatch,
            [httpx.Response(200, text=RESULTS), httpx.Response(200, text=SEARCH_FORM)],
        )
        with pytest.raises(mdoc_service.MdocFetchError, match="did not load a profile"):
            await mdoc_service.fetch_mdoc_profile("111222", proxy="socks5://x:1")
        assert holder["clients"] == mdoc_service.PROFILE_ATTEMPTS

    @pytest.mark.asyncio
    async def test_an_unknown_number_is_not_retried(self, monkeypatch):
        """A 500 is definitive. Retrying it would triple the wait to reach the
        same answer, and would read as flakiness rather than "no such offender"."""
        holder = _install(
            monkeypatch,
            [httpx.Response(200, text=RESULTS), httpx.Response(500, text=RUNTIME_ERROR)],
        )
        with pytest.raises(mdoc_service.MdocFetchError, match="no offender with MDOC number"):
            await mdoc_service.fetch_mdoc_profile("999999", proxy="socks5://x:1")
        assert holder["clients"] == 1

    @pytest.mark.asyncio
    async def test_a_dead_proxy_is_not_retried(self, monkeypatch):
        holder = _install(monkeypatch, [], raise_on_get=httpx.ConnectError("nope"))
        with pytest.raises(mdoc_service.MdocFetchError, match="MDOC_PROXY"):
            await mdoc_service.fetch_mdoc_profile("111222", proxy="socks5://x:1")
        assert holder["clients"] == 1

    @pytest.mark.asyncio
    async def test_transport_failure_points_at_the_proxy(self, monkeypatch):
        _install(monkeypatch, [], raise_on_get=httpx.ConnectError("All connection attempts failed"))
        with pytest.raises(mdoc_service.MdocFetchError, match="MDOC_PROXY"):
            await mdoc_service.fetch_mdoc_profile("111222", proxy="socks5://x:1")

    @pytest.mark.asyncio
    async def test_non_numeric_input_is_rejected_before_any_request(self, monkeypatch):
        holder = _install(monkeypatch, [])
        with pytest.raises(ValueError, match="must be digits"):
            await mdoc_service.fetch_mdoc_profile("not-a-number", proxy="socks5://x:1")
        assert "client" not in holder


# ---------------------------------------------------------------------------
# Name search and pagination. Markup shape copied from a real OTIS results
# page; the people in it are invented.
# ---------------------------------------------------------------------------


def _results_page(rows, *, total=None, next_page=False) -> str:
    trs = "".join(
        f'<tr><td><input type="submit" name="action:LoadProfile" value="{n}" class="btn" /></td>'
        f"<td>{last}</td><td>{first}</td><td>{dob}</td><td>{sex}</td><td>{race}</td>"
        f"<td>750.227</td><td>Somewhere</td><td>{status}</td></tr>"
        for n, last, first, dob, sex, race, status in rows
    )
    matches = f"<tr><td>{total} matches found</td></tr>" if total is not None else ""
    nxt = '<input type="submit" name="action:Pagination" value="Next" />' if next_page else ""
    return (
        "<html><head><title>Results Page - OTIS</title></head><body>"
        f'<form action="/OTIS2/Results" method="post"><table><tbody>{matches}{trs}'
        f"</tbody></table>{nxt}</form></body></html>"
    )


ROWS_P1 = [
    ("111111", "PERKINS", "AARON", "9/26/2000", "M", "Black", "Parole"),
    ("222222", "PERKINS", "BETTY", "1/2/1990", "F", "White", "Prisoner"),
]
ROWS_P2 = [("333333", "PERKINS", "CARL", "5/5/1985", "M", "Black", "Discharged")]


class TestResultsParsing:
    def test_rows_and_columns(self):
        rows, total, has_next = parse_mdoc_results(_results_page(ROWS_P1, total=2))
        assert [r.mdoc_number for r in rows] == ["111111", "222222"]
        first = rows[0]
        assert (first.last_name, first.first_name) == ("PERKINS", "AARON")
        assert (first.dob.year, first.dob.month, first.dob.day) == (2000, 9, 26)
        assert (first.sex, first.race, first.status) == ("M", "Black", "Parole")
        assert total == 2
        assert has_next is False

    def test_next_page_is_detected(self):
        _, _, has_next = parse_mdoc_results(_results_page(ROWS_P1, next_page=True))
        assert has_next is True

    def test_a_page_with_no_results_yields_nothing(self):
        rows, _, _ = parse_mdoc_results(_results_page([], total=0))
        assert rows == []

    def test_thousands_separator_in_the_match_count(self):
        _, total, _ = parse_mdoc_results(_results_page(ROWS_P1, total="1,234"))
        assert total == 1234


class TestSearch:
    @pytest.mark.asyncio
    async def test_follows_pagination_and_concatenates(self, monkeypatch):
        _install(
            monkeypatch,
            [
                httpx.Response(200, text=_results_page(ROWS_P1, total=3, next_page=True)),
                httpx.Response(200, text=_results_page(ROWS_P2, total=3)),
            ],
        )
        rows = await mdoc_service.search_mdoc(last_name="Perkins", proxy="socks5://x:1")
        assert [r.mdoc_number for r in rows] == ["111111", "222222", "333333"]

    @pytest.mark.asyncio
    async def test_a_pagination_that_repeats_itself_terminates(self, monkeypatch):
        """If Next serves the same page back, the loop must stop rather than
        spin to max_pages and duplicate every row."""
        same = _results_page(ROWS_P1, total=2, next_page=True)
        _install(monkeypatch, [httpx.Response(200, text=same) for _ in range(12)])
        rows = await mdoc_service.search_mdoc(last_name="Perkins", proxy="socks5://x:1")
        assert [r.mdoc_number for r in rows] == ["111111", "222222"]

    @pytest.mark.asyncio
    async def test_max_pages_caps_the_walk(self, monkeypatch):
        pages = [
            httpx.Response(
                200,
                text=_results_page(
                    [(f"{i}00000", "X", "Y", "1/1/1990", "M", "Black", "Parole")], next_page=True
                ),
            )
            for i in range(1, 9)
        ]
        _install(monkeypatch, pages)
        rows = await mdoc_service.search_mdoc(last_name="X", max_pages=3, proxy="socks5://x:1")
        assert len(rows) == 3

    @pytest.mark.asyncio
    async def test_empty_search_is_refused_before_any_request(self, monkeypatch):
        holder = _install(monkeypatch, [])
        with pytest.raises(ValueError, match="last name or a first name"):
            await mdoc_service.search_mdoc(proxy="socks5://x:1")
        assert "client" not in holder

    @pytest.mark.asyncio
    async def test_transport_failure_points_at_the_proxy(self, monkeypatch):
        _install(monkeypatch, [], raise_on_get=httpx.ConnectError("nope"))
        with pytest.raises(mdoc_service.MdocFetchError, match="MDOC_PROXY"):
            await mdoc_service.search_mdoc(last_name="Perkins", proxy="socks5://x:1")
