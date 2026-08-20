"""give member_set and set_relationships a time dimension

Both tables were keyed on the pair itself, so they could hold exactly one row
per (member, set) and per (set_a, set_b). That records the present and forgets
everything else: a member who left one set for another, or two sets that were
allies until they fell out, could not be represented at all.

Each table gains a surrogate id plus from_date/until_date (FuzzyDate JSONB, as
everywhere else in the schema), so a pair can hold one row per spell. The
current spell is the one with until_date IS NULL, and a partial unique index
allows only one of those per pair. Existing rows become open-ended current
spells with an unknown start, which is exactly what they meant.

Revision ID: 57f8aaa46bdd
Revises: 6b102eb7959a
Create Date: 2026-08-20
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "57f8aaa46bdd"
down_revision = "6b102eb7959a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── member_set ────────────────────────────────────────────────────────────
    op.add_column("member_set", sa.Column("id", sa.Uuid(), nullable=True))
    op.execute("UPDATE member_set SET id = gen_random_uuid() WHERE id IS NULL")
    op.alter_column("member_set", "id", nullable=False)

    op.drop_constraint("member_set_pkey", "member_set", type_="primary")
    op.create_primary_key("member_set_pkey", "member_set", ["id"])

    # The composite PK used to index member_id as its leading column.
    op.create_index("ix_member_set_member_id", "member_set", ["member_id"])

    op.add_column(
        "member_set", sa.Column("from_date", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    op.add_column(
        "member_set",
        sa.Column("until_date", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # At most one open spell per (member, set). Closed spells may repeat freely.
    op.execute(
        "CREATE UNIQUE INDEX uq_member_set_current ON member_set (member_id, set_id) "
        "WHERE until_date IS NULL"
    )
    # The old index would have made a member's closed primary spell block a new
    # one, so it has to be narrowed to the open spell too.
    op.drop_index("ux_member_set_one_primary", table_name="member_set")
    op.execute(
        "CREATE UNIQUE INDEX ux_member_set_one_primary ON member_set (member_id) "
        "WHERE is_primary AND until_date IS NULL"
    )

    # ── set_relationships ─────────────────────────────────────────────────────
    op.add_column("set_relationships", sa.Column("id", sa.Uuid(), nullable=True))
    op.execute("UPDATE set_relationships SET id = gen_random_uuid() WHERE id IS NULL")
    op.alter_column("set_relationships", "id", nullable=False)

    # Named uq_set_relationship_pair but created as the PRIMARY KEY.
    op.drop_constraint("uq_set_relationship_pair", "set_relationships", type_="primary")
    op.create_primary_key("set_relationships_pkey", "set_relationships", ["id"])

    op.create_index("ix_set_relationships_set_a_id", "set_relationships", ["set_a_id"])
    op.create_index("ix_set_relationships_set_b_id", "set_relationships", ["set_b_id"])

    op.add_column(
        "set_relationships",
        sa.Column("from_date", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "set_relationships",
        sa.Column("until_date", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.execute(
        "CREATE UNIQUE INDEX uq_set_relationship_current ON set_relationships "
        "(set_a_id, set_b_id) WHERE until_date IS NULL"
    )
    # ck_set_relationship_ordering and trg_set_relationship_ordering still apply
    # per row and are deliberately left in place.


def downgrade() -> None:
    # Collapsing back to one row per pair would silently destroy every closed
    # spell, so refuse rather than pick a winner.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM member_set WHERE until_date IS NOT NULL) THEN
                RAISE EXCEPTION
                    'Cannot downgrade: member_set holds closed spells that a '
                    'composite primary key cannot represent. Delete them first.';
            END IF;
            IF EXISTS (SELECT 1 FROM set_relationships WHERE until_date IS NOT NULL) THEN
                RAISE EXCEPTION
                    'Cannot downgrade: set_relationships holds closed links that a '
                    'composite primary key cannot represent. Delete them first.';
            END IF;
        END $$;
        """
    )

    op.execute("DROP INDEX IF EXISTS uq_set_relationship_current")
    op.drop_index("ix_set_relationships_set_b_id", table_name="set_relationships")
    op.drop_index("ix_set_relationships_set_a_id", table_name="set_relationships")
    op.drop_column("set_relationships", "until_date")
    op.drop_column("set_relationships", "from_date")
    op.drop_constraint("set_relationships_pkey", "set_relationships", type_="primary")
    op.drop_column("set_relationships", "id")
    op.create_primary_key("uq_set_relationship_pair", "set_relationships", ["set_a_id", "set_b_id"])

    op.execute("DROP INDEX IF EXISTS ux_member_set_one_primary")
    op.execute("DROP INDEX IF EXISTS uq_member_set_current")
    op.drop_column("member_set", "until_date")
    op.drop_column("member_set", "from_date")
    op.drop_index("ix_member_set_member_id", table_name="member_set")
    op.drop_constraint("member_set_pkey", "member_set", type_="primary")
    op.drop_column("member_set", "id")
    op.create_primary_key("member_set_pkey", "member_set", ["member_id", "set_id"])
    op.execute(
        "CREATE UNIQUE INDEX ux_member_set_one_primary ON member_set (member_id) WHERE is_primary"
    )
