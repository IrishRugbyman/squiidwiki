"""alliance relationships: an alliance's own allies and enemies

A new table, `alliance_relationship`, for friend/enemy links held by a whole
alliance. The far side is either another alliance or a single set, never both.

`set_relationships` cannot hold these: both its ends are sets. Until now a bloc's
war with another bloc had to be written as an edge from some stand-in set: a
"core" set named after the alliance, which existed only so the bloc's enemies had
somewhere to hang.

Alliance-to-alliance rows are stored once in UUID order (`alliance_id <
other_alliance_id`, a CHECK rather than the trigger `set_relationships` uses:
application CRUD normalises before insert). Alliance-to-set rows always put the
alliance in `alliance_id`. One open row per pair, by two partial unique indexes,
one per kind of far side. Both ends cascade on delete.

`setrelationshiptype` already exists and is reused, not recreated.

Revision ID: eccb7ce3c92a
Revises: af5914edd23e
Create Date: 2026-09-26
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "eccb7ce3c92a"
down_revision = "af5914edd23e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alliance_relationship",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("alliance_id", sa.Uuid(), nullable=False),
        sa.Column("other_alliance_id", sa.Uuid(), nullable=True),
        sa.Column("other_set_id", sa.Uuid(), nullable=True),
        sa.Column(
            "relationship_type",
            postgresql.ENUM("FRIEND", "ENEMY", name="setrelationshiptype", create_type=False),
            nullable=False,
        ),
        sa.Column("from_date", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("until_date", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["alliance_id"], ["alliance.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["other_alliance_id"], ["alliance.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["other_set_id"], ["sets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "num_nonnulls(other_alliance_id, other_set_id) = 1",
            name="ck_alliance_relationship_one_target",
        ),
        sa.CheckConstraint(
            "other_alliance_id IS NULL OR alliance_id < other_alliance_id",
            name="ck_alliance_relationship_ordering",
        ),
    )
    op.create_index(
        "ix_alliance_relationship_alliance_id", "alliance_relationship", ["alliance_id"]
    )
    op.create_index(
        "ix_alliance_relationship_other_alliance_id",
        "alliance_relationship",
        ["other_alliance_id"],
    )
    op.create_index(
        "ix_alliance_relationship_other_set_id", "alliance_relationship", ["other_set_id"]
    )
    op.create_index(
        "uq_alliance_relationship_current_alliance",
        "alliance_relationship",
        ["alliance_id", "other_alliance_id"],
        unique=True,
        postgresql_where=sa.text("until_date IS NULL AND other_alliance_id IS NOT NULL"),
    )
    op.create_index(
        "uq_alliance_relationship_current_set",
        "alliance_relationship",
        ["alliance_id", "other_set_id"],
        unique=True,
        postgresql_where=sa.text("until_date IS NULL AND other_set_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_alliance_relationship_current_set", table_name="alliance_relationship")
    op.drop_index("uq_alliance_relationship_current_alliance", table_name="alliance_relationship")
    op.drop_index("ix_alliance_relationship_other_set_id", table_name="alliance_relationship")
    op.drop_index("ix_alliance_relationship_other_alliance_id", table_name="alliance_relationship")
    op.drop_index("ix_alliance_relationship_alliance_id", table_name="alliance_relationship")
    op.drop_table("alliance_relationship")
