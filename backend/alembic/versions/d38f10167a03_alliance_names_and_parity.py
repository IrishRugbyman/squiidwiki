"""alliance name variants, emojis, founder, several gangs and lineage

Brings alliances level with sets.

**Names.** `alliance.aliases`, a flat list of strings, is replaced by
`name_variants`, the slot structure sets use (`name`, `initials`, `number` and a
`lead`), and `alliance.name` becomes the derived display of the primary variant,
exactly as `sets.name` is (app/core/set_names.py). There is no compatibility
column: every reader of `aliases` is changed in the same release.

The backfill here is mechanical and loses nothing: the stored name becomes the
primary variant and each alias its own variant, each put in the slot its text
looks like (digits are a number, a short all-capitals token is initials, anything
else a name). The name a variant displays is the text it came from, so no
alliance is renamed and no slug moves. Folding initials and numbers into the
variant they belong to is a judgement per alliance and is done afterwards
through the API, where the audit log records it.

**Emojis**, **founder_id**, **alliance_gang** (several gangs, position 0 mirrored
into `alliance.gang_id`) and **alliance_lineage** (directional descent, reading
child KIND parent like `set_lineage`) mirror their set counterparts.

`founded_at` and the old `aliases` were plain JSONB, so a Python None was stored
as the JSON literal `null` (22 of 25 prod rows for founded_at). Those become SQL
NULL, and both new JSONB columns are `none_as_null`.

Revision ID: d38f10167a03
Revises: 4f215263e2b3
Create Date: 2026-10-06
"""

import json
import re

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "d38f10167a03"
down_revision = "4f215263e2b3"
branch_labels = None
depends_on = None

_INITIALS = re.compile(r"^(?=.*[A-Z])[A-Z0-9.&]{2,6}$")


def _slot(text: str) -> str:
    if text.isdigit():
        return "number"
    if _INITIALS.match(text):
        return "initials"
    return "name"


def _variant(text: str, primary: bool) -> dict:
    slot = _slot(text)
    return {
        "name": text if slot == "name" else None,
        "initials": text if slot == "initials" else None,
        "number": text if slot == "number" else None,
        "is_primary": primary,
        "lead": slot,
    }


def upgrade() -> None:
    bind = op.get_bind()

    op.add_column(
        "alliance",
        sa.Column("name_variants", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "alliance", sa.Column("emojis", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    op.create_index(
        "ix_alliance_emojis", "alliance", ["emojis"], postgresql_using="gin", postgresql_ops={}
    )
    op.add_column("alliance", sa.Column("founder_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_alliance_founder_id_member",
        "alliance",
        "member",
        ["founder_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_alliance_founder_id", "alliance", ["founder_id"])

    bind.execute(sa.text("UPDATE alliance SET founded_at = NULL WHERE founded_at = 'null'::jsonb"))

    rows = bind.execute(sa.text("SELECT id, name, aliases FROM alliance")).all()
    for alliance_id, name, aliases in rows:
        variants = [_variant(name.strip(), True)]
        seen = {name.strip().casefold()}
        for alias in aliases if isinstance(aliases, list) else []:
            text = (alias or "").strip()
            if text and text.casefold() not in seen:
                seen.add(text.casefold())
                variants.append(_variant(text, False))
        bind.execute(
            sa.text("UPDATE alliance SET name_variants = CAST(:v AS jsonb) WHERE id = :id"),
            {"v": json.dumps(variants), "id": alliance_id},
        )
    op.drop_column("alliance", "aliases")

    op.create_table(
        "alliance_gang",
        sa.Column("alliance_id", sa.Uuid(), nullable=False),
        sa.Column("gang_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["alliance_id"], ["alliance.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["gang_id"], ["gang.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("alliance_id", "gang_id"),
    )
    op.create_index("ix_alliance_gang_gang_id", "alliance_gang", ["gang_id"])
    bind.execute(
        sa.text(
            "INSERT INTO alliance_gang (alliance_id, gang_id, position) "
            "SELECT id, gang_id, 0 FROM alliance WHERE gang_id IS NOT NULL"
        )
    )

    op.create_table(
        "alliance_lineage",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=False),
        sa.Column("child_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            postgresql.ENUM(name="setlineagekind", create_type=False),
            nullable=False,
        ),
        sa.Column("from_date", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("until_date", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["alliance.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["child_id"], ["alliance.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("parent_id <> child_id", name="ck_alliance_lineage_no_self"),
    )
    op.create_index("ix_alliance_lineage_parent_id", "alliance_lineage", ["parent_id"])
    op.create_index("ix_alliance_lineage_child_id", "alliance_lineage", ["child_id"])
    op.create_index(
        "uq_alliance_lineage_current",
        "alliance_lineage",
        ["parent_id", "child_id"],
        unique=True,
        postgresql_where=sa.text("until_date IS NULL"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_index("uq_alliance_lineage_current", table_name="alliance_lineage")
    op.drop_index("ix_alliance_lineage_child_id", table_name="alliance_lineage")
    op.drop_index("ix_alliance_lineage_parent_id", table_name="alliance_lineage")
    op.drop_table("alliance_lineage")
    op.drop_index("ix_alliance_gang_gang_id", table_name="alliance_gang")
    op.drop_table("alliance_gang")

    op.add_column(
        "alliance", sa.Column("aliases", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    # Every filled slot of every variant that is not the name itself.
    rows = bind.execute(sa.text("SELECT id, name, name_variants FROM alliance")).all()
    for alliance_id, name, variants in rows:
        aliases: list[str] = []
        for v in variants or []:
            for slot in ("name", "initials", "number"):
                text = (v.get(slot) or "").strip()
                if text and text != name and text not in aliases:
                    aliases.append(text)
        bind.execute(
            sa.text("UPDATE alliance SET aliases = CAST(:a AS jsonb) WHERE id = :id"),
            {"a": json.dumps(aliases) if aliases else None, "id": alliance_id},
        )

    op.drop_index("ix_alliance_founder_id", table_name="alliance")
    op.drop_constraint("fk_alliance_founder_id_member", "alliance", type_="foreignkey")
    op.drop_column("alliance", "founder_id")
    op.drop_index("ix_alliance_emojis", table_name="alliance")
    op.drop_column("alliance", "emojis")
    op.drop_column("alliance", "name_variants")
