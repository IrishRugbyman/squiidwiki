"""Unit tests for the shared slug helper.

Expected values are written from the rule (fold to ASCII, lowercase, hyphenate)
rather than from running the function, so a regression in the folding shows up
as a failure rather than as a quietly updated expectation.
"""

import pytest

from app.core.slug import slugify


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # The Corsica names that exposed the bug: \w is Unicode-aware, so the
        # previous implementation kept the accents.
        ("Gérard Ziglioli", "gerard-ziglioli"),
        ("François-Marie Santucci", "francois-marie-santucci"),
        ("Sorbo-Ocagnano", "sorbo-ocagnano"),
        # Latin letters NFKD alone does not decompose.
        ("ÆØÅ", "aeoa"),
        ("Straße", "strasse"),
        ("Þór", "thor"),
        ("Łódź", "lodz"),
        # Ordinary shaping.
        ("Le Castel", "le-castel"),
        ("L'Apocalypse", "lapocalypse"),
        ("O'Neill  Jr.", "oneill-jr"),
        ("a_b c", "a-b-c"),
        ("  Already-Fine  ", "already-fine"),
    ],
)
def test_slugify_folds_to_ascii(raw: str, expected: str):
    assert slugify(raw, "member") == expected


@pytest.mark.parametrize("raw", ["北京", "Пётр", "   ", "---", "!!!"])
def test_slugify_falls_back_when_nothing_survives(raw: str):
    """A name that folds away entirely takes the fallback.

    Deliberate: a fallback slug is navigable and `_unique_slug` disambiguates
    it, whereas a percent-encoded one is not. The display name lives on the
    entity, not in its URL.
    """
    assert slugify(raw, "member") == "member"


def test_slugify_fallback_is_per_entity():
    assert slugify("", "alliance") == "alliance"
    assert slugify("", "business") == "business"


def test_slugify_is_idempotent():
    """Re-slugging a slug must not change it, or re-saving an entity would
    walk its URL."""
    for raw in ["Gérard Ziglioli", "L'Apocalypse", "Straße", "Le Castel"]:
        once = slugify(raw, "member")
        assert slugify(once, "member") == once
