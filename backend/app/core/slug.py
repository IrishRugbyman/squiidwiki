import re
import unicodedata

# Latin letters NFKD does not decompose, because they are not an accented form
# of an ASCII letter but letters in their own right. Without this "Æ" folds
# away to nothing rather than to "ae".
_PRE_FOLD = str.maketrans(
    {
        "æ": "ae",
        "Æ": "ae",
        "œ": "oe",
        "Œ": "oe",
        "ø": "o",
        "Ø": "o",
        "ß": "ss",
        "þ": "th",
        "Þ": "th",
        "ð": "d",
        "Ð": "d",
        "đ": "d",
        "Đ": "d",
        "ł": "l",
        "Ł": "l",
        "ı": "i",
    }
)


def slugify(value: str, fallback: str) -> str:
    """Lowercase ASCII slug, used for every entity's URL segment.

    Folds accents to ASCII first. `\\w` is Unicode-aware in Python, so the
    obvious regex keeps accented characters and yields slugs like
    "gerard-ziglioli" spelt with an e-acute. Every universe was ASCII-only
    until Corsica, which is why that went unnoticed: such a slug reaches the
    router percent-encoded and is inconsistent with every other slug in the
    database.

    A name written entirely in a non-Latin script folds away to nothing and
    takes the fallback, which `_unique_slug` then disambiguates. That is
    deliberate: a fallback slug is plainly navigable, a percent-encoded one is
    not, and the display name is carried by the entity itself rather than by
    its URL.
    """
    s = value.translate(_PRE_FOLD)
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower().strip()
    # Underscores survive this pass so the next one can fold them into hyphens.
    s = re.sub(r"[^a-z0-9\s_-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-") or fallback
