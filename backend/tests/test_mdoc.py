"""Parser tests for the rebuilt MDOC OTIS profile page.

The fixture's *markup* is copied from a real OTIS profile so the selectors under
test are the real ones; every *value* in it is invented, because a real
offender's record must not live in this repo. Expected values below are read
off the fixture by hand - never produced by running the parser.
"""

import base64
import io
import re
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
# Both fixtures are live OTIS pages (the layout of 2026-11-04) with every identifying
# value replaced by an invented one and the markup left as served: `otis_profile`
# is a prisoner serving three sentences, `otis_profile_probation` a probationer with
# one finished prison sentence and one running probation sentence.
FIXTURE_PROBATION = Path(__file__).parent / "fixtures" / "otis_profile_probation.html"


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


@pytest.fixture(scope="module")
def released_html(photo_bytes: bytes) -> str:
    uri = "data:image/gif;base64," + base64.b64encode(photo_bytes).decode("ascii")
    return FIXTURE_PROBATION.read_text(encoding="utf-8").replace("__PHOTO_DATA_URI__", uri)


@pytest.fixture(scope="module")
def released(released_html: str):
    return parse_mdoc_html(released_html)


class TestBiographical:
    def test_name_is_title_cased_and_despaced(self, profile):
        # The name cell is split over lines: "Jordan \n Avery \n Reed".
        assert profile.legal_name == "Jordan Avery Reed"

    def test_identifiers(self, profile):
        assert profile.mdoc_number == "111222"
        assert profile.sid_number == "9998887A"

    def test_dob_ignores_the_trailing_age(self, profile):
        # The cell reads "3/9/1991 (35)".
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

    def test_the_second_fixture_reads_too(self, released):
        assert released.legal_name == "Casey Lee Dunmore"
        assert (released.mdoc_number, released.sid_number) == ("333444", "7776665B")
        assert (released.dob.year, released.dob.month, released.dob.day) == (1985, 7, 21)
        assert (released.race, released.sex) == ("Black or African American", "Male")
        assert (released.hair, released.eyes) == ("Black", "Brown")
        assert (released.height, released.weight) == ("5' 10\"", "165 lbs")
        assert (released.image_date.year, released.image_date.month) == (2025, 3)


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
        discharged = re.sub(
            r"<span>Prisoner</span>", "<span>Discharged</span>", profile_html, count=1
        )
        assert discharged != profile_html
        parsed = parse_mdoc_html(discharged)
        assert parsed.status == "Discharged"
        assert parsed.discharge_date is not None
        assert parsed.max_discharge_date is None

    def test_a_probationer_has_a_supervising_office_and_no_release_dates(self, released):
        assert released.status == "Probationer"
        assert released.facility == "Example County/Example Office/Probation"
        assert released.security_level is None
        assert released.earliest_release_date is None
        assert released.discharge_date is None


class TestLists:
    def test_aliases(self, profile, released):
        assert profile.aliases == ["JAY"]
        assert released.aliases == ["DUNMORE CASEY L"]

    def test_marks_are_exactly_the_marks_rows(self, profile, released):
        """The marks list must stop at the next section heading. It once ran on
        into "Prison Sentences", "Active" and every sentence after it."""
        assert profile.marks == [
            "Tattoo- Lower Left Arm - Example Crew",
            "Tattoo - Chest - eagle",
            "Scar - Left Leg - long scar",
        ]
        assert released.marks == ["Tattoo - Right Bicep - star", "Scar - Left Knee - small scar"]

    def test_none_is_not_read_as_an_entry(self, profile):
        assert all(m.lower() != "none" for m in profile.marks + profile.aliases)

    def test_an_empty_section_is_empty_not_an_error(self, profile_html):
        """ "none" (or no rows) in Aliases and Marks is a real answer."""
        emptied = re.sub(
            r"(<h2 id=\"Aliases\">.*?</tr>)\s*<tr>\s*<td>\s*JAY\s*</td>\s*</tr>",
            r"\1",
            profile_html,
            flags=re.S,
        )
        assert emptied != profile_html
        assert parse_mdoc_html(emptied).aliases == []


class TestSentences:
    def test_counts_by_kind_and_state(self, profile, released):
        # profile: prison Active 3, Inactive none; probation Active none, Inactive 1.
        prison = [s for s in profile.sentences if s.kind == "prison"]
        probation = [s for s in profile.sentences if s.kind == "probation"]
        assert len(prison) == 3 and all(s.active for s in prison)
        assert len(probation) == 1 and probation[0].active is False
        # released: prison Active none, Inactive 1; probation Active 1, Inactive none.
        assert [(s.kind, s.active) for s in released.sentences] == [
            ("prison", False),
            ("probation", True),
        ]

    def test_active_prison_sentence_detail(self, profile):
        s = profile.sentences[0]
        assert s.kind == "prison"
        assert s.offense == "Homicide - Murder, Second Degree"
        assert s.mcl == ["750.317", "769.11"]
        assert s.court_file == "20001111-01-FH"
        assert s.county == "Wayne"
        assert s.conviction_type == "Jury"
        assert s.minimum_sentence == "60 Years 0 Months 0 Days"
        assert s.maximum_sentence == "90 Years 0 Months 0 Days"
        assert (s.date_of_offense.year, s.date_of_offense.month, s.date_of_offense.day) == (
            2020,
            6,
            1,
        )
        assert s.date_of_sentence == _ymd(2020, 9, 15)
        # An active sentence has not been discharged.
        assert s.date_of_discharge is None
        assert s.discharge_reason is None

    def test_sentences_come_in_page_order(self, profile):
        assert [(s.offense, s.mcl) for s in profile.sentences if s.kind == "prison"] == [
            ("Homicide - Murder, Second Degree", ["750.317", "769.11"]),
            ("Weapons - Felony Firearms", ["750.227BA"]),
            ("Assault with Intent to Commit Murder", ["750.83", "769.11"]),
        ]

    def test_inactive_sentence_carries_discharge_detail(self, released):
        s = released.sentences[0]
        assert s.offense == "Robbery - Unarmed"
        assert s.mcl == ["750.530"]
        assert s.court_file == "19000555-01"
        assert s.minimum_sentence == "10 Years 0 Months 0 Days"
        assert s.discharge_reason == "Closed Offender Charge"
        assert s.date_of_sentence == _ymd(1996, 8, 20)
        assert s.date_of_discharge == _ymd(2007, 1, 9)

    def test_a_probation_sentence_marked_by_an_h4(self, released):
        """Probation sentences are announced by an <h4> with no id, which must
        not be mistaken for the start of a new section."""
        s = released.sentences[1]
        assert (s.kind, s.active) == ("probation", True)
        assert s.offense == "Assault with Dangerous Weapon (Felonious Assault)"
        assert s.court_file == "25000777-01-FH"
        assert s.date_of_sentence == _ymd(2025, 6, 10)
        assert s.date_of_discharge is None

    def test_unavailable_minimum_is_kept_as_the_text_it_is(self, profile):
        s = next(x for x in profile.sentences if x.kind == "probation")
        assert s.minimum_sentence == "Unavailable"
        assert s.maximum_sentence == "2 Years 0 Months 0 Days"


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

    @pytest.mark.parametrize("section", ["Status", "Aliases", "Marks", "Sentences", "Probation"])
    def test_a_missing_section_is_a_parse_error_not_empty_fields(self, profile_html, section):
        """A profile whose layout moved must fail loudly. Dropping a heading is
        what the parser used to see after a redesign, and it returned a profile
        with no status, facility or sentences and said nothing."""
        broken = re.sub(rf'(<h[24]) id="{section}"', r"\1 id=\"x\"", profile_html)
        assert broken != profile_html
        with pytest.raises(MdocParseError, match=f"'{section}' section"):
            parse_mdoc_html(broken)

    def test_the_pre_2026_11_markup_is_not_accepted(self, profile_html):
        """Section headings were <h4> and sentence states <h5> before the
        move; that layout is gone and is not silently half-read."""
        old = profile_html.replace("<h2", "<h5").replace("</h2>", "</h5>")
        with pytest.raises(MdocParseError):
            parse_mdoc_html(old)

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
        # Three active prison sentences, all handed down 9/15/2020 in one file.
        spells = derive_spells(profile)
        assert len(spells) == 3
        assert [s.case_id for s in spells] == ["20001111-01-FH"] * 3
        assert [s.from_date for s in spells] == [_ymd(2020, 9, 15)] * 3
        assert [s.to_date for s in spells] == [None] * 3

    def test_probation_is_never_a_spell(self, profile):
        """The fixture has a probation sentence; probation is not custody."""
        assert any(s.kind == "probation" for s in profile.sentences)
        assert len(derive_spells(profile)) == 3

    def test_a_finished_sentence_carries_the_date_it_actually_ended(self, released):
        (served,) = derive_spells(released)
        assert served.from_date == _ymd(1996, 8, 20)
        assert served.to_date == _ymd(2007, 1, 9)
        assert served.case_id == "19000555-01"
        assert served.life_sentence is False

    def test_a_probationers_office_is_not_a_prison_facility(self, released):
        """No sentence is running in prison, so nothing takes the Status block."""
        (served,) = derive_spells(released)
        assert served.facility is None
        assert served.earliest_release_date is None
        assert served.max_discharge_date is None

    def test_projections_land_on_the_controlling_sentence_only(self, profile):
        """Earliest release, max discharge and facility are offender-level.

        Copying them onto every spell would put the same release on the
        calendar once per sentence. They sit on the 90-year count, the longest.
        """
        controlling, firearm, assault = derive_spells(profile)
        assert controlling.earliest_release_date == _ymd(2031, 4, 15)
        assert controlling.max_discharge_date == _ymd(2046, 4, 15)
        assert controlling.facility == "Example Correctional Facility"
        for other in (firearm, assault):
            assert other.earliest_release_date is None
            assert other.max_discharge_date is None
            assert other.facility is None

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

    def test_notes_state_the_sentence_facts(self, released):
        (served,) = derive_spells(released)
        assert served.notes is not None
        assert served.notes.splitlines() == [
            "Offense: Robbery - Unarmed",
            "MCL 750.530",
            "County: Wayne",
            "Conviction type: Plea",
            "Sentence: 10 Years 0 Months 0 Days to 20 Years 0 Months 0 Days",
            "Date of offense: Apr 4, 1995",
            "Discharge reason: Closed Offender Charge",
        ]

    def test_notes_name_no_source_and_hedge_nothing(self, profile, released):
        """House rule: entity text that renders on a page states the fact and stops."""
        for spell in derive_spells(profile) + derive_spells(released):
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

SEARCH_FORM = (
    "<html><head><title>OTIS Offender Search - OTIS</title></head><body>"
    '<form action="/Search" method="post">'
    '<input name="__RequestVerificationToken" type="hidden" value="tok-123" />'
    "</form></body></html>"
)
SEARCH_FORM_NO_TOKEN = (
    "<html><head><title>OTIS Offender Search - OTIS</title></head><body></body></html>"
)
RESULTS = "<html><head><title>Results Page - OTIS</title></head><body></body></html>"
RUNTIME_ERROR = "<html><head><title>Runtime Error</title></head><body></body></html>"


class _StubClient:
    """Stands in for httpx.AsyncClient. `posts` is consumed in order:
    the search POST first, then the LoadProfile POST."""

    def __init__(self, posts, *, raise_on_get=None, search_page=None, landed=None, **kwargs):
        self._posts = list(posts)
        self._raise_on_get = raise_on_get
        self._search_page = search_page or SEARCH_FORM
        # Where the GET ends up after redirects; None means where it was sent.
        self._landed = landed
        self.requested = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, url, **kwargs):
        if self._raise_on_get:
            raise self._raise_on_get
        return httpx.Response(
            200, text=self._search_page, request=httpx.Request("GET", self._landed or url)
        )

    async def post(self, url, data=None, **kwargs):
        self.requested.append((url, data))
        resp = self._posts.pop(0)
        # httpx refuses raise_for_status() on a response with no request bound,
        # so give the stub one rather than dropping the check from the code.
        if resp._request is None:
            resp._request = httpx.Request("POST", url)
        return resp


def _install(monkeypatch, posts, raise_on_get=None, search_page=None, landed=None):
    """Every attempt sees the same responses. Retry delays are zeroed so a test
    of the give-up path does not spend the real backoff sleeping."""
    holder = {"clients": 0}

    def factory(**kwargs):
        holder["clients"] += 1
        holder["client"] = _StubClient(
            posts, raise_on_get=raise_on_get, search_page=search_page, landed=landed, **kwargs
        )
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


RESULTS_HEADER = (
    '<tr class="ResultsHeader" role="heading">'
    + "".join(
        f'<td><a href="/About#x">{h}</a></td>'
        for h in (
            "Offender Number",
            "Last Name",
            "First Name",
            "Date of Birth",
            "Sex ",
            "Race ",
            "Location",
            "Status",
            "Parole Board Jurisdiction Date",
            "Maximum Date",
            "Date Paroled",
        )
    )
    + "</tr>"
)


def _results_page(rows, *, total=None, next_page=False, header=RESULTS_HEADER) -> str:
    """The live column layout (no MCL column), people invented."""
    trs = "".join(
        f'<tr><td><input type="submit" name="action:LoadProfile" value="{n}" class="btn" /></td>'
        f"<td>{last}</td><td>{first}</td><td>{dob}</td><td>{sex}</td><td>{race}</td>"
        f'<td><a href="https://example.test/x">Somewhere CF</a></td>'
        f'<td><a href="/About#stat">{status}</a></td>'
        "<td><span>11/8/2024</span></td><td><span>4/8/2028</span></td><td><span></span></td></tr>"
        for n, last, first, dob, sex, race, status in rows
    )
    matches = f"<tr><td>{total} matches found</td></tr>" if total is not None else ""
    nxt = '<input type="submit" name="action:Pagination" value="Next" />' if next_page else ""
    return (
        "<html><head><title>Results Page - OTIS</title></head><body>"
        f'<form action="/Results" method="post"><table><tbody>{matches}{header}{trs}'
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
        assert first.location == "Somewhere CF"
        assert (first.parole_board_date.year, first.parole_board_date.month) == (2024, 11)
        assert (first.max_date.year, first.max_date.month, first.max_date.day) == (2028, 4, 8)
        assert first.date_paroled is None  # an empty cell is None, not a date
        assert total == 2
        assert has_next is False

    def test_next_page_is_detected(self):
        _, _, has_next = parse_mdoc_results(_results_page(ROWS_P1, next_page=True))
        assert has_next is True

    def test_a_page_with_no_results_yields_nothing(self):
        rows, _, _ = parse_mdoc_results(_results_page([], total=0))
        assert rows == []

    def test_columns_are_found_by_header_not_position(self):
        """Dropping a column must not shift the others: a positional read once
        put the parole-board date in `status` after OTIS removed the MCL column."""
        page = _results_page(ROWS_P1, header=RESULTS_HEADER.replace("Race ", "Ancestry "))
        rows, _, _ = parse_mdoc_results(page)
        assert rows[0].race is None
        assert rows[0].status == "Parole"

    def test_a_results_table_without_a_header_is_an_error(self):
        with pytest.raises(MdocParseError, match="no header row"):
            parse_mdoc_results(_results_page(ROWS_P1, header=""))

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
        out = await mdoc_service.search_mdoc(last_name="Perkins", proxy="socks5://x:1")
        assert [r.mdoc_number for r in out.rows] == ["111111", "222222", "333333"]
        assert out.total == 3
        assert out.truncated is False

    @pytest.mark.asyncio
    async def test_a_pagination_that_repeats_itself_terminates(self, monkeypatch):
        """If Next serves the same page back, the loop must stop rather than
        spin to max_pages and duplicate every row. That is not truncation."""
        same = _results_page(ROWS_P1, total=2, next_page=True)
        _install(monkeypatch, [httpx.Response(200, text=same) for _ in range(12)])
        out = await mdoc_service.search_mdoc(last_name="Perkins", proxy="socks5://x:1")
        assert [r.mdoc_number for r in out.rows] == ["111111", "222222"]
        assert out.truncated is False

    @pytest.mark.asyncio
    async def test_max_pages_caps_the_walk_and_says_so(self, monkeypatch):
        pages = [
            httpx.Response(
                200,
                text=_results_page(
                    [(f"{i}00000", "X", "Y", "1/1/1990", "M", "Black", "Parole")],
                    total=8,
                    next_page=True,
                ),
            )
            for i in range(1, 9)
        ]
        holder = _install(monkeypatch, pages)
        out = await mdoc_service.search_mdoc(last_name="X", max_pages=3, proxy="socks5://x:1")
        assert [r.mdoc_number for r in out.rows] == ["100000", "200000", "300000"]
        assert out.total == 8
        assert out.truncated is True
        # one search POST plus two Next POSTs: the third page is read, not fetched past
        assert len(holder["client"].requested) == 3

    @pytest.mark.asyncio
    async def test_a_walk_that_ends_exactly_on_the_cap_is_not_truncated(self, monkeypatch):
        _install(
            monkeypatch,
            [
                httpx.Response(200, text=_results_page(ROWS_P1, total=3, next_page=True)),
                httpx.Response(200, text=_results_page(ROWS_P2, total=3)),
            ],
        )
        out = await mdoc_service.search_mdoc(last_name="P", max_pages=2, proxy="socks5://x:1")
        assert len(out.rows) == 3
        assert out.truncated is False

    @pytest.mark.asyncio
    async def test_empty_search_is_refused_before_any_request(self, monkeypatch):
        holder = _install(monkeypatch, [])
        with pytest.raises(ValueError, match="at least a name, an MDOC number or a tattoo"):
            await mdoc_service.search_mdoc(proxy="socks5://x:1")
        # Filters alone are not a search either.
        with pytest.raises(ValueError, match="at least a name"):
            await mdoc_service.search_mdoc(race="White", age=30, proxy="socks5://x:1")
        assert holder["clients"] == 2  # sessions opened, but nothing was posted
        assert holder["client"].requested == []

    @pytest.mark.asyncio
    async def test_transport_failure_points_at_the_proxy(self, monkeypatch):
        _install(monkeypatch, [], raise_on_get=httpx.ConnectError("nope"))
        with pytest.raises(mdoc_service.MdocFetchError, match="MDOC_PROXY"):
            await mdoc_service.search_mdoc(last_name="Perkins", proxy="socks5://x:1")


class TestSearchRefusals:
    """OTIS says no in two ways, and neither may read as "no matches"."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status", [403, 429, 500])
    async def test_an_http_error_keeps_its_status(self, monkeypatch, status):
        _install(monkeypatch, [httpx.Response(status, text=RUNTIME_ERROR)])
        with pytest.raises(mdoc_service.MdocHttpError) as exc:
            await mdoc_service.search_mdoc(last_name="Perkins", proxy="socks5://x:1")
        assert exc.value.status == status

    @pytest.mark.asyncio
    async def test_the_search_form_instead_of_results_is_an_error_not_no_matches(self, monkeypatch):
        _install(monkeypatch, [httpx.Response(200, text=SEARCH_FORM)])
        with pytest.raises(mdoc_service.MdocBounced, match="rejected the session"):
            await mdoc_service.search_mdoc(last_name="Perkins", proxy="socks5://x:1")

    @pytest.mark.asyncio
    async def test_a_results_page_with_no_rows_is_an_honest_empty_result(self, monkeypatch):
        _install(monkeypatch, [httpx.Response(200, text=_results_page([], total=0))])
        out = await mdoc_service.search_mdoc(last_name="Perkins", proxy="socks5://x:1")
        assert (out.rows, out.total, out.truncated) == ([], 0, False)


class TestSearchPages:
    @pytest.mark.asyncio
    async def test_pages_are_fetched_only_as_the_caller_asks(self, monkeypatch):
        holder = _install(
            monkeypatch,
            [
                httpx.Response(200, text=_results_page(ROWS_P1, total=3, next_page=True)),
                httpx.Response(200, text=_results_page(ROWS_P2, total=3)),
            ],
        )
        async with mdoc_service.OtisSession("socks5://x:1") as otis:
            pages = otis.search_pages(last_name="Perkins")
            rows, total, has_next = await anext(pages)
            assert ([r.mdoc_number for r in rows], total, has_next) == (
                ["111111", "222222"],
                3,
                True,
            )
            assert len(holder["client"].requested) == 1  # page 2 not requested yet
            rows, _, has_next = await anext(pages)
            assert ([r.mdoc_number for r in rows], has_next) == (["333333"], False)
            with pytest.raises(StopAsyncIteration):
                await anext(pages)


class TestSearchFields:
    """Every form field reaches OTIS under its form name, and enums are checked."""

    @pytest.mark.asyncio
    async def test_all_fields_are_posted_under_the_forms_names(self, monkeypatch):
        holder = _install(monkeypatch, [httpx.Response(200, text=_results_page([], total=0))])
        await mdoc_service.search_mdoc(
            last_name=" Perkins ",
            first_name="Aaron",
            mdoc_number="111111",
            sex="Male",
            race="Pacific Islander",
            age=41,
            status="Parole",
            tattoos=" rose ",
            proxy="socks5://x:1",
        )
        _, data = holder["client"].requested[0]
        assert data == {
            "LastName": "Perkins",
            "FirstName": "Aaron",
            "MDOCNumber": "111111",
            "Sex": "Male",
            "Race": "Pacific Islander",
            "Age": "41",
            "OffenderStatus": "Parole",
            "MarksScarsTattoos": "rose",
            "action:Search": "Search",
            "__RequestVerificationToken": "tok-123",
        }

    @pytest.mark.asyncio
    async def test_status_defaults_to_the_module_default_and_filters_stay_open(self, monkeypatch):
        holder = _install(monkeypatch, [httpx.Response(200, text=_results_page([], total=0))])
        await mdoc_service.search_mdoc(last_name="Perkins", proxy="socks5://x:1")
        _, data = holder["client"].requested[0]
        assert data["OffenderStatus"] == mdoc_service.DEFAULT_STATUS == "Active Offenders"
        assert (data["Sex"], data["Race"], data["Age"], data["MarksScarsTattoos"]) == (
            "Either",
            "All",
            "",
            "",
        )

    @pytest.mark.asyncio
    async def test_a_tattoo_only_search_is_allowed(self, monkeypatch):
        holder = _install(monkeypatch, [httpx.Response(200, text=_results_page(ROWS_P2, total=1))])
        out = await mdoc_service.search_mdoc(tattoos="anchor", proxy="socks5://x:1")
        _, data = holder["client"].requested[0]
        assert (data["LastName"], data["FirstName"], data["MDOCNumber"]) == ("", "", "")
        assert data["MarksScarsTattoos"] == "anchor"
        assert [r.mdoc_number for r in out.rows] == ["333333"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("field", "bad"),
        [
            ("sex", "male"),
            ("sex", "M"),
            ("race", "Black or African American"),
            ("race", "black"),
            ("status", "Prisoners"),
            ("status", "Active"),
        ],
    )
    async def test_a_value_outside_the_forms_vocabulary_is_refused(self, monkeypatch, field, bad):
        holder = _install(monkeypatch, [])
        with pytest.raises(ValueError, match=f"{field} must be one of"):
            await mdoc_service.search_mdoc(
                last_name="Perkins", proxy="socks5://x:1", **{field: bad}
            )
        assert holder["client"].requested == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize("age", [0, -3, 130, "abc", "4.5"])
    async def test_a_nonsense_age_is_refused(self, monkeypatch, age):
        _install(monkeypatch, [])
        with pytest.raises(ValueError, match="age must be"):
            await mdoc_service.search_mdoc(last_name="P", age=age, proxy="socks5://x:1")

    @pytest.mark.asyncio
    async def test_the_vocabularies_are_the_forms_option_values(self):
        assert mdoc_service.SEX_VALUES == ("Either", "Male", "Female")
        assert mdoc_service.STATUS_VALUES == (
            "Active Offenders",
            "All",
            "Prison",
            "Parole",
            "Probation",
            "Discharged",
            "Abscond1",
            "Abscond2",
        )
        assert len(mdoc_service.RACE_VALUES) == 8
        assert "Middle Eastern/North African" in mdoc_service.RACE_VALUES


class TestSearchSession:
    """The move of 2026-10-31: the search must post back the form's token, to
    the host the search page was served from, or OTIS returns the bare form,
    which parses as no matches."""

    @pytest.mark.asyncio
    async def test_search_posts_the_forms_token(self, monkeypatch):
        holder = _install(monkeypatch, [httpx.Response(200, text=_results_page(ROWS_P2, total=1))])
        await mdoc_service.search_mdoc(last_name="Perkins", proxy="socks5://x:1")
        _, data = holder["client"].requested[0]
        assert data["__RequestVerificationToken"] == "tok-123"
        assert data["LastName"] == "Perkins"

    @pytest.mark.asyncio
    async def test_posts_follow_the_host_the_search_page_came_from(self, monkeypatch):
        holder = _install(
            monkeypatch,
            [
                httpx.Response(200, text=_results_page(ROWS_P1, total=3, next_page=True)),
                httpx.Response(200, text=_results_page(ROWS_P2, total=3)),
            ],
            landed="https://otis.moved.example/Search",
        )
        await mdoc_service.search_mdoc(last_name="Perkins", proxy="socks5://x:1")
        urls = [u for u, _ in holder["client"].requested]
        assert urls == [
            "https://otis.moved.example/Search",
            "https://otis.moved.example/Results",
        ]

    @pytest.mark.asyncio
    async def test_one_session_runs_several_searches_on_one_get(self, monkeypatch):
        """The point of the session object: the search page (and its token) is
        fetched once, not once per search."""
        gets = []
        holder = _install(
            monkeypatch,
            [
                httpx.Response(200, text=_results_page(ROWS_P1, total=2)),
                httpx.Response(200, text=_results_page(ROWS_P2, total=1)),
                httpx.Response(200, text=_results_page([], total=0)),
            ],
        )
        original_get = _StubClient.get

        async def counting_get(self, url, **kwargs):
            gets.append(url)
            return await original_get(self, url, **kwargs)

        monkeypatch.setattr(_StubClient, "get", counting_get)
        async with mdoc_service.OtisSession("socks5://x:1") as otis:
            a = await otis.search(last_name="Perkins")
            b = await otis.search(first_name="Carl")
            c = await otis.search(tattoos="nothing")
        assert [len(x.rows) for x in (a, b, c)] == [2, 1, 0]
        assert len(gets) == 1
        assert holder["clients"] == 1
        tokens = {d["__RequestVerificationToken"] for _, d in holder["client"].requested}
        assert tokens == {"tok-123"}

    @pytest.mark.asyncio
    async def test_a_session_serves_a_search_then_a_profile(self, monkeypatch, profile_html):
        holder = _install(
            monkeypatch,
            [
                httpx.Response(200, text=_results_page(ROWS_P1, total=2)),
                httpx.Response(200, text=RESULTS),
                httpx.Response(200, text=profile_html),
            ],
        )
        async with mdoc_service.OtisSession("socks5://x:1") as otis:
            await otis.search(last_name="Perkins")
            parsed = await otis.profile("111222")
        assert parsed.mdoc_number == "111222"
        assert holder["clients"] == 1

    @pytest.mark.asyncio
    async def test_using_a_session_outside_its_block_is_an_error(self):
        otis = mdoc_service.OtisSession("socks5://x:1")
        with pytest.raises(RuntimeError, match="not open"):
            await otis.search(last_name="Perkins")

    @pytest.mark.asyncio
    async def test_a_search_page_without_a_token_is_an_error_not_an_empty_result(self, monkeypatch):
        holder = _install(monkeypatch, [], search_page=SEARCH_FORM_NO_TOKEN)
        with pytest.raises(mdoc_service.MdocFetchError, match="anti-forgery token"):
            await mdoc_service.search_mdoc(last_name="Perkins", proxy="socks5://x:1")
        assert holder["client"].requested == []

    @pytest.mark.asyncio
    async def test_profile_walk_posts_the_token_and_follows_the_host(
        self, monkeypatch, profile_html
    ):
        holder = _install(
            monkeypatch,
            [httpx.Response(200, text=RESULTS), httpx.Response(200, text=profile_html)],
            landed="https://otis.moved.example/Search",
        )
        await mdoc_service.fetch_mdoc_profile("111222", proxy="socks5://x:1")
        (search_url, search_data), (profile_url, _) = holder["client"].requested
        assert search_url == "https://otis.moved.example/Search"
        assert search_data["__RequestVerificationToken"] == "tok-123"
        assert search_data["MDOCNumber"] == "111222"
        assert profile_url == "https://otis.moved.example/Results"

    @pytest.mark.asyncio
    async def test_profile_walk_without_a_token_is_an_error(self, monkeypatch):
        _install(monkeypatch, [], search_page=SEARCH_FORM_NO_TOKEN)
        with pytest.raises(mdoc_service.MdocFetchError, match="anti-forgery token"):
            await mdoc_service.fetch_mdoc_profile("111222", proxy="socks5://x:1")


# ---------------------------------------------------------------------------
# POST /api/v1/mdoc/search
# ---------------------------------------------------------------------------


class TestSearchRoute:
    """The route is a thin layer over search_mdoc; the service is stubbed so
    only the HTTP contract is under test: auth, body mapping, response shape,
    error mapping."""

    @pytest.fixture
    def seen(self, monkeypatch):
        from app.routers import mdoc as mdoc_router

        calls = []

        async def fake_search(**kwargs):
            calls.append(kwargs)
            rows, total, _ = parse_mdoc_results(_results_page(ROWS_P1, total=40, next_page=True))
            return mdoc_service.MdocSearchOutcome(rows=rows, total=total, truncated=True)

        monkeypatch.setattr(mdoc_router, "search_mdoc", fake_search)
        return calls

    @pytest.mark.asyncio
    async def test_requires_auth(self, anon_client, seen):
        resp = await anon_client.post("/api/v1/mdoc/search", json={"last_name": "Perkins"})
        assert resp.status_code == 401
        assert seen == []

    @pytest.mark.asyncio
    async def test_maps_the_body_and_returns_rows_total_truncated(self, client, db_session, seen):
        from tests.test_members import _admin_token

        token = await _admin_token(client, db_session)
        resp = await client.post(
            "/api/v1/mdoc/search",
            json={"tattoos": "anchor", "race": "White", "age": 33, "max_pages": 2},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, resp.text
        assert seen == [
            {
                "last_name": "",
                "first_name": "",
                "mdoc_number": "",
                "sex": "Either",
                "race": "White",
                "age": 33,
                "status": "Active Offenders",
                "tattoos": "anchor",
                "max_pages": 2,
            }
        ]
        body = resp.json()
        assert body["total"] == 40
        assert body["truncated"] is True
        first = body["rows"][0]
        assert first["mdoc_number"] == "111111"
        assert (first["last_name"], first["first_name"]) == ("PERKINS", "AARON")
        assert first["dob"]["year"] == 2000
        assert first["location"] == "Somewhere CF"
        assert first["status"] == "Parole"
        assert first["max_date"]["year"] == 2028

    @pytest.mark.asyncio
    async def test_max_pages_is_capped(self, client, db_session, seen):
        from tests.test_members import _admin_token

        token = await _admin_token(client, db_session)
        resp = await client.post(
            "/api/v1/mdoc/search",
            json={"last_name": "P", "max_pages": 21},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422
        assert seen == []

    @pytest.mark.asyncio
    async def test_a_service_value_error_is_a_400(self, client, db_session, monkeypatch):
        from app.routers import mdoc as mdoc_router
        from tests.test_members import _admin_token

        async def refuse(**kwargs):
            raise ValueError("sex must be one of Either, Male, Female; got 'x'")

        monkeypatch.setattr(mdoc_router, "search_mdoc", refuse)
        token = await _admin_token(client, db_session)
        resp = await client.post(
            "/api/v1/mdoc/search",
            json={"last_name": "P", "sex": "x"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        assert "sex must be one of" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_an_unreachable_otis_is_a_502(self, client, db_session, monkeypatch):
        from app.routers import mdoc as mdoc_router
        from tests.test_members import _admin_token

        async def down(**kwargs):
            raise mdoc_service.MdocFetchError("proxy down")

        monkeypatch.setattr(mdoc_router, "search_mdoc", down)
        token = await _admin_token(client, db_session)
        resp = await client.post(
            "/api/v1/mdoc/search",
            json={"last_name": "P"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 502
