"""app/core/sources.py: URL normal form, kind and custody lookup detection.

The normaliser and lookup rules mirror research/tools/wikilib/identity.py,
which resolves case-file references against these rows; the vectors here are
the ones its tests pin too.
"""

import pytest

from app.core.sources import (
    LookupSystem,
    SourceKind,
    classify_kind,
    domain_of,
    lookup_locator,
    lookup_system,
    normalise_url,
)


def test_normalise_url_strips_only_tracking_params():
    assert normalise_url("HTTPS://Example.com/a/?utm_source=x&id=7") == "https://example.com/a?id=7"
    assert normalise_url("https://example.com/a/") == "https://example.com/a"
    assert normalise_url("https://example.com/a?fbclid=z") == "https://example.com/a"


@pytest.mark.parametrize(
    "url,system",
    [
        ("https://www.bop.gov/inmateloc/", LookupSystem.BOP),
        (
            "https://www.bop.gov/PublicInfo/execute/inmateloc?todo=query&inmateNum=12345-039",
            LookupSystem.BOP,
        ),
        ("https://mdocweb.state.mi.us/OTIS2", LookupSystem.MDOC_OTIS),
        (
            "https://mdocweb.state.mi.us/OTIS2/otis2profile.aspx?mdocNumber=123456",
            LookupSystem.MDOC_OTIS,
        ),
        ("https://services.gdc.ga.gov/GDC/OffenderQuery/jsp/OffQryForm.jsp", LookupSystem.GDC),
        ("https://www.justice.gov/x", None),
    ],
)
def test_lookup_system(url, system):
    assert lookup_system(url) == system


def test_lookup_locator_reads_url_then_title():
    assert lookup_locator("https://www.bop.gov/x?inmateNum=12345-039") == "12345-039"
    assert lookup_locator(None, "OTIS offender profile, Person A #654321") == "654321"
    assert lookup_locator(None, "register numbers confirmed 2026-09-17") is None


@pytest.mark.parametrize(
    "url,kind",
    [
        ("https://www.instagram.com/p/x/", SourceKind.SOCIAL),
        ("https://storage.courtlistener.com/recap/a.pdf", SourceKind.COURT),
        ("https://www.justice.gov/usao-edmi/pr/x", SourceKind.COURT),
        ("https://www.clickondetroit.com/news/x", SourceKind.PRESS),
        ("https://www.bop.gov/inmateloc/", SourceKind.CUSTODY),
        ("https://www.youtube.com/watch?v=x", SourceKind.VIDEO),
        ("https://privedatabase.wordpress.com/x", SourceKind.WIKI),
        ("https://www.google.com/maps/d/viewer?mid=1", SourceKind.MAP),
        ("research-file:detroit/documents/x", SourceKind.INTERNAL),
        ("https://www.unknown-site.example/", SourceKind.OTHER),
    ],
)
def test_classify_kind(url, kind):
    assert classify_kind(url) == kind


def test_domain_of():
    assert domain_of("https://www.clickondetroit.com/news") == "clickondetroit.com"
    assert domain_of("research-file:x") is None
