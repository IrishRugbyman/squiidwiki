"""family roles go gender-neutral: parent, child, sibling

The family JSONB spoke only of fathers, sons and brothers. That left a
sister recorded as her brother's brother and a mother with no role at all,
and one hand-edited row carrying a `sister` key nothing rendered. Rename
the keys, make `parent` a list (two parents, where the old `father` was one
id), fold `sister` into `sibling`, and mirror every tie onto the relative,
since the backend has always written both sides and the hand-edited row did
not. `cousin`, `spouse`, `uncle` and `nephew` are untouched.

Revision ID: 1ce08fbdeab7
Revises: 09fbe10e849f
Create Date: 2026-09-15

"""

import json

import sqlalchemy as sa

from alembic import op

revision = "1ce08fbdeab7"
down_revision = "09fbe10e849f"
branch_labels = None
depends_on = None

UP = {"father": "parent", "son": "child", "brother": "sibling", "sister": "sibling"}
DOWN = {"parent": "father", "child": "son", "sibling": "brother"}
INVERSE = {
    "parent": "child",
    "child": "parent",
    "sibling": "sibling",
    "cousin": "cousin",
    "spouse": "spouse",
    "uncle": "nephew",
    "nephew": "uncle",
}


def _ids(value) -> list[str]:
    if value is None:
        return []
    return [str(v) for v in value] if isinstance(value, list) else [str(value)]


def _load(bind) -> dict[str, dict]:
    rows = bind.execute(sa.text("SELECT id, family FROM member WHERE family IS NOT NULL"))
    out = {}
    for member_id, family in rows:
        if isinstance(family, str):
            family = json.loads(family)
        out[str(member_id)] = family or {}
    return out


def _store(bind, families: dict[str, dict]) -> None:
    for member_id, family in families.items():
        family = {k: v for k, v in family.items() if v}
        if family:
            bind.execute(
                sa.text("UPDATE member SET family = CAST(:family AS jsonb) WHERE id = :id"),
                {"family": json.dumps(family), "id": member_id},
            )
        else:
            bind.execute(
                sa.text("UPDATE member SET family = NULL WHERE id = :id"), {"id": member_id}
            )


def upgrade() -> None:
    bind = op.get_bind()
    families = {}
    for member_id, family in _load(bind).items():
        renamed: dict[str, list[str]] = {}
        for role, value in family.items():
            ids = renamed.setdefault(UP.get(role, role), [])
            for i in _ids(value):
                if i not in ids:
                    ids.append(i)
        families[member_id] = renamed

    # Mirror every tie. The API writes both sides on every save, so this only
    # changes rows that were edited by hand; an id that names no member row
    # updates nothing and is left where it was.
    known = {str(r[0]) for r in bind.execute(sa.text("SELECT id FROM member")).fetchall()}
    for member_id, family in list(families.items()):
        for role, ids in list(family.items()):
            inverse = INVERSE.get(role)
            if inverse is None:
                continue
            for relative_id in ids:
                if relative_id not in known:
                    continue
                mirror = families.setdefault(relative_id, {}).setdefault(inverse, [])
                if member_id not in mirror:
                    mirror.append(member_id)

    _store(bind, families)


def downgrade() -> None:
    # Lossy on purpose: a second parent has nowhere to go under `father`, and
    # a sibling who was a sister goes back to `brother`. The first parent wins.
    bind = op.get_bind()
    families = {}
    for member_id, family in _load(bind).items():
        renamed: dict = {}
        for role, value in family.items():
            ids = _ids(value)
            old = DOWN.get(role, role)
            if old == "father":
                if ids:
                    renamed["father"] = ids[0]
            else:
                merged = renamed.setdefault(old, [])
                for i in ids:
                    if i not in merged:
                        merged.append(i)
        families[member_id] = renamed
    _store(bind, families)
