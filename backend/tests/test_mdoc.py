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

from app.services.mdoc import (
    MdocParseError,
    decode_data_uri,
    parse_mdoc_html,
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
