"""How a set's displayed name is made from its name variants.

A set carries its names as `name_variants`: each entry is one name with its
parts in slots (`name`, `initials`, `number`), and `lead` says which parts are
shown, in order. `sets.name` is not an independent column. It is always the
display of the primary variant, computed here and written by the CRUD layer, so
the label a pill, a caption or a slug is built from can never drift from the
name the set page shows.

`lead` is either one slot or an ordered list of them. The list exists because
some sets are known by a combination: "CFP 2400" is initials then number,
"051 Young Money" is number then name, "No Limit 083" is name then number.
With a single slot those could not be shown at all, so four Cash Flow Posse
sets all displayed as "CFP".

`frontend/src/lib/setDisplay.ts` implements the same rules for the form's live
preview and must stay in step with this module.
"""

from collections.abc import Iterable, Mapping
from typing import Any

SLOTS: tuple[str, ...] = ("name", "initials", "number")


def _get(variant: Any, slot: str) -> str:
    """One slot of a variant, stripped, whether the variant is a model or a dict."""
    value = variant.get(slot) if isinstance(variant, Mapping) else getattr(variant, slot, None)
    return (value or "").strip()


def normalize_lead(lead: Any, variant: Any) -> str | list[str] | None:
    """`lead` reduced to the slots it names that the variant actually fills.

    Unknown slots, empty slots and repeats are dropped. A list of one becomes
    that slot, so the stored shape stays a plain string wherever it can.

    Raises:
        ValueError: If `lead` is neither a slot name, a list of them, nor None.
    """
    if lead is None:
        return None
    if isinstance(lead, str):
        slots = [lead]
    elif isinstance(lead, list | tuple):
        slots = list(lead)
    else:
        raise ValueError(f"lead must be a slot or a list of slots, got {lead!r}")
    for slot in slots:
        if slot not in SLOTS:
            raise ValueError(f"unknown lead slot {slot!r}; expected one of {', '.join(SLOTS)}")
    kept = [s for s in dict.fromkeys(slots) if _get(variant, s)]
    if not kept:
        return None
    return kept[0] if len(kept) == 1 else kept


def lead_slots(variant: Any) -> list[str]:
    """The slots a variant displays, in order: its `lead`, else its first filled slot."""
    raw = variant.get("lead") if isinstance(variant, Mapping) else getattr(variant, "lead", None)
    lead = normalize_lead(raw, variant)
    if isinstance(lead, str):
        return [lead]
    if lead:
        return lead
    for slot in SLOTS:
        if _get(variant, slot):
            return [slot]
    return []


def variant_display(variant: Any) -> str:
    """The text a variant is shown as: its lead slots, joined by a space."""
    return " ".join(_get(variant, slot) for slot in lead_slots(variant))


def primary_variant(variants: Iterable[Any] | None) -> Any | None:
    """The variant marked primary, else the first, else None."""
    items = list(variants or [])
    for v in items:
        primary = v.get("is_primary") if isinstance(v, Mapping) else getattr(v, "is_primary", False)
        if primary:
            return v
    return items[0] if items else None


def display_name(variants: Iterable[Any] | None) -> str:
    """The set's name: the display of its primary variant, or "" with none."""
    primary = primary_variant(variants)
    return variant_display(primary) if primary is not None else ""
