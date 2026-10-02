"""set_gang: a set can claim more than one gang

A new join table, `set_gang`, holding every gang a set claims, ordered by
`position` (0 is the primary). Some sets run under two cards at once - NBD is
Gangster Disciples and Satan Disciples, LaayMafia is Bloods and Rollin' 60s - and
`sets.gang_id` could hold only one, so the rest was pushed into bio prose.

`sets.gang_id` stays, as a mirror of the position-0 row: the map colours, the
stats and every existing reader use it. Every set that has one today gets it
back as its single, primary `set_gang` row.

Both ends cascade on delete, so removing a set or a gang takes its rows with it.

Revision ID: b305c16cd347
Revises: eccb7ce3c92a
Create Date: 2026-09-28
"""

import sqlalchemy as sa

from alembic import op

revision = "b305c16cd347"
down_revision = "eccb7ce3c92a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "set_gang",
        sa.Column("set_id", sa.Uuid(), nullable=False),
        sa.Column("gang_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["set_id"], ["sets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["gang_id"], ["gang.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("set_id", "gang_id"),
    )
    op.create_index("ix_set_gang_gang_id", "set_gang", ["gang_id"])
    op.execute(
        "INSERT INTO set_gang (set_id, gang_id, position) "
        "SELECT id, gang_id, 0 FROM sets WHERE gang_id IS NOT NULL"
    )


def downgrade() -> None:
    # Only the primary survives in sets.gang_id, which the application kept in
    # step all along; the secondary gangs are lost with the table.
    op.drop_index("ix_set_gang_gang_id", table_name="set_gang")
    op.drop_table("set_gang")
