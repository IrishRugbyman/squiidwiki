"""set lineage (directional descent) and per-set emojis

Two additions to sets, one structural and one a column.

**set_lineage** records which set came out of which. It is a new table rather
than new values on `setrelationshiptype` - which is what docs/ROADMAP.md
proposed - because `set_relationships` is symmetric by construction: a
`set_a_id < set_b_id` CHECK plus the `enforce_set_relationship_ordering`
trigger store the endpoints in UUID order, so that table cannot say which of a
pair is the parent. Its `uq_set_relationship_current` partial index also allows
only one open row per pair, and a splinter set at war with the set it left needs
both facts at once. Nothing about the existing table changes here.

`kind` reads **child KIND parent** in every case, so a row is unambiguous
whichever column it is read from.

**sets.emojis** is a plain JSONB list of glyphs. First entry is the badge shown
wherever the set is listed; the rest are the other glyphs the set is known by.
Members signal affiliation with these in bios and display names, so the list is
what makes an emoji seen in a handle resolvable back to a set.

Revision ID: 09fbe10e849f
Revises: 25a6aa16b972
Create Date: 2026-08-29
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "09fbe10e849f"
down_revision = "25a6aa16b972"
branch_labels = None
depends_on = None

LINEAGE_KINDS = ("SPLINTERED_FROM", "RENAMED_FROM", "MERGED_FROM", "YOUNGER_GENERATION_OF")


def upgrade() -> None:
    # Created explicitly, not inferred: create_table would emit CREATE TYPE too,
    # and this way the downgrade has something symmetrical to drop.
    setlineagekind = postgresql.ENUM(*LINEAGE_KINDS, name="setlineagekind")
    setlineagekind.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "set_lineage",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=False),
        sa.Column("child_id", sa.Uuid(), nullable=False),
        sa.Column(
            "kind",
            postgresql.ENUM(*LINEAGE_KINDS, name="setlineagekind", create_type=False),
            nullable=False,
        ),
        sa.Column("from_date", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("until_date", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["parent_id"], ["sets.id"]),
        sa.ForeignKeyConstraint(["child_id"], ["sets.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("parent_id <> child_id", name="ck_set_lineage_no_self"),
    )
    op.create_index("ix_set_lineage_parent_id", "set_lineage", ["parent_id"])
    op.create_index("ix_set_lineage_child_id", "set_lineage", ["child_id"])
    # One *open* descent row per ordered pair. Closed rows are history and may
    # repeat, the same way set_relationships allows a pair to be allies twice.
    op.create_index(
        "uq_set_lineage_current",
        "set_lineage",
        ["parent_id", "child_id"],
        unique=True,
        postgresql_where=sa.text("until_date IS NULL"),
    )

    op.add_column(
        "sets", sa.Column("emojis", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    # Containment index, for resolving a glyph seen in a handle back to its sets
    # (`sets.emojis @> '["<glyph>"]'`), which is the research direction.
    op.create_index("ix_sets_emojis", "sets", ["emojis"], postgresql_using="gin", postgresql_ops={})


def downgrade() -> None:
    op.drop_index("ix_sets_emojis", table_name="sets")
    op.drop_column("sets", "emojis")
    op.drop_index("uq_set_lineage_current", table_name="set_lineage")
    op.drop_index("ix_set_lineage_child_id", table_name="set_lineage")
    op.drop_index("ix_set_lineage_parent_id", table_name="set_lineage")
    op.drop_table("set_lineage")
    postgresql.ENUM(name="setlineagekind").drop(op.get_bind(), checkfirst=True)
