"""Names in slots, shared by sets and alliances.

Both carry their names as `name_variants`: each entry is one name with its parts
in slots (`name`, `initials`, `number`) and a `lead` saying which are shown. The
stored `name` column is always the display of the primary variant. The display
rules themselves are in `app/core/set_names.py`; this module holds the request
validation both entities share, so an alliance can never accept a shape a set
would refuse.
"""

import uuid
from typing import Literal, Optional

from pydantic import BaseModel, model_validator

from app.core.set_names import display_name, normalize_lead

Slot = Literal["name", "initials", "number"]


class NameVariant(BaseModel):
    name: Optional[str] = None
    initials: Optional[str] = None
    number: Optional[str] = None
    is_primary: bool = False
    # Which slots are shown, in order: one slot ("initials"), or several
    # (["initials", "number"] shows "CFP 2400"). If None, falls back to
    # name → initials → number. See app/core/set_names.py.
    lead: Optional[Slot | list[Slot]] = None

    @model_validator(mode="after")
    def _at_least_one_field(self):
        if not (self.name or self.initials or self.number):
            raise ValueError("name_variants entry must have at least one of name/initials/number")
        # Slots the variant does not fill are dropped, and a list of one is
        # stored as that slot.
        self.lead = normalize_lead(self.lead, self)
        return self


MAX_EMOJIS = 12
MAX_EMOJI_LENGTH = 16


def normalize_emojis(emojis: Optional[list[str]]) -> Optional[list[str]]:
    """Trim, drop blanks, de-duplicate, and reject anything that is not a glyph.

    Order is meaningful - the first entry is the badge - so de-duplication keeps
    first occurrence rather than sorting.

    The "not a glyph" test is that an entry cannot be *entirely* ASCII. A real
    emoji never is, even the keycaps (`1\ufe0f\u20e3` is an ASCII digit plus two
    non-ASCII code points), while `BO` or `752` is, and those belong in
    `name_variants` where they are searchable as names. Anything looser and this
    column quietly becomes a second alias field.
    """
    if emojis is None:
        return None
    out: list[str] = []
    for raw in emojis:
        e = (raw or "").strip()
        if not e:
            continue
        if len(e) > MAX_EMOJI_LENGTH:
            raise ValueError(f"emoji entry too long (max {MAX_EMOJI_LENGTH} characters): {e!r}")
        if all(ord(c) < 128 for c in e):
            raise ValueError(f"not an emoji: {e!r} - plain text belongs in name_variants")
        if e not in out:
            out.append(e)
    if len(out) > MAX_EMOJIS:
        raise ValueError(f"at most {MAX_EMOJIS} emojis (got {len(out)})")
    return out or None


def normalize_variants(variants: Optional[list[NameVariant]]) -> Optional[list[NameVariant]]:
    if not variants:
        return variants
    primaries = [v for v in variants if v.is_primary]
    if len(primaries) > 1:
        raise ValueError("name_variants may only have one primary entry")
    if not primaries:
        variants[0].is_primary = True
    return variants


def derived_name(sent: Optional[str], variants: list[NameVariant], kind: str = "set") -> str:
    """The name of a set or alliance, computed from its primary variant.

    `sets.name` is never taken from the caller. A caller may still send it, and
    it must then agree with the primary variant: a mismatch means the client
    computed the display differently (the bug that let a form save rename "CFP
    2400" to "CFP"), and is refused rather than silently overridden.
    """
    derived = display_name(variants)
    if sent is not None and sent.strip() != derived:
        raise ValueError(
            f"name {sent!r} does not match the primary name variant, which displays as "
            f"{derived!r}. A {kind}'s name is derived from its primary variant: change "
            "name_variants (its slots or its lead) to rename it"
        )
    return derived


def dedupe_ids(ids: Optional[list[uuid.UUID]]) -> Optional[list[uuid.UUID]]:
    """Keep the first occurrence of each id, preserving order (order is rank)."""
    if ids is None:
        return None
    return list(dict.fromkeys(ids))
