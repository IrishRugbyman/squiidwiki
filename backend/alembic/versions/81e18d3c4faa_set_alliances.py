"""set alliances: a set can sit in more than one alliance

`alliance_set` has existed since the first schema and was never written: every
reader went through `sets.alliance_id`, so the table sat empty (0 rows in prod
on 2026-09-29). It becomes the membership table, exactly as `set_gang` did for
gangs: every alliance a set is in, ordered by `position` (0 is the primary).
TMC is in TMCNE and was one of the five sets that formed RHN; one column could
hold only one of them.

`sets.alliance_id` stays as the mirror of the position-0 row, kept by
`_sync_set_alliances` in crud/gang_set.py, so every existing reader keeps
working. Both foreign keys now cascade, and the set side gets its own index.

Revision ID: 81e18d3c4faa
Revises: 2d5a7ab2c470
Create Date: 2026-09-30
"""

import sqlalchemy as sa

from alembic import op

revision = "81e18d3c4faa"
down_revision = "2d5a7ab2c470"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "alliance_set",
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
    )
    op.drop_constraint("alliance_set_alliance_id_fkey", "alliance_set", type_="foreignkey")
    op.drop_constraint("alliance_set_set_id_fkey", "alliance_set", type_="foreignkey")
    op.create_foreign_key(
        "alliance_set_alliance_id_fkey",
        "alliance_set",
        "alliance",
        ["alliance_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "alliance_set_set_id_fkey", "alliance_set", "sets", ["set_id"], ["id"], ondelete="CASCADE"
    )
    op.create_index("ix_alliance_set_set_id", "alliance_set", ["set_id"])
    # The table was never written, but clear it rather than trust that.
    op.execute("DELETE FROM alliance_set")
    op.execute(
        "INSERT INTO alliance_set (alliance_id, set_id, position) "
        "SELECT alliance_id, id, 0 FROM sets WHERE alliance_id IS NOT NULL"
    )


def downgrade() -> None:
    # sets.alliance_id held the primary all along; secondary memberships are lost.
    op.execute("DELETE FROM alliance_set")
    op.drop_index("ix_alliance_set_set_id", table_name="alliance_set")
    op.drop_constraint("alliance_set_set_id_fkey", "alliance_set", type_="foreignkey")
    op.drop_constraint("alliance_set_alliance_id_fkey", "alliance_set", type_="foreignkey")
    op.create_foreign_key(
        "alliance_set_alliance_id_fkey", "alliance_set", "alliance", ["alliance_id"], ["id"]
    )
    op.create_foreign_key("alliance_set_set_id_fkey", "alliance_set", "sets", ["set_id"], ["id"])
    op.drop_column("alliance_set", "position")
