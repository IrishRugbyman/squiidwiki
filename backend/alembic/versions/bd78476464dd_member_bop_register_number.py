"""member bop_register_number

Adds the Federal Bureau of Prisons register number to `member`, the federal twin
of `mdoc_number`.

Unlike an MDOC number it is unique within a universe (the BOP assigns one for
life and never reuses it), which a partial index enforces so the many members
without one never collide, and its `NNNNN-NNN` shape is checked in the database
as well as normalised by the API, so a value written around the API is held to
the same rule.

Written by hand. Autogenerate against this database proposes dropping the
trigram, emoji and partial indexes and rewriting a dozen foreign keys that no
model declares, which is drift, not this change.

Revision ID: bd78476464dd
Revises: 1ce08fbdeab7
Create Date: 2026-09-17 16:59:26.141821

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

revision: str = "bd78476464dd"
down_revision: str | None = "1ce08fbdeab7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "member",
        sa.Column("bop_register_number", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    op.create_check_constraint(
        "ck_member_bop_register_number_format",
        "member",
        "bop_register_number ~ '^[0-9]{5}-[0-9]{3}$'",
    )
    op.create_index(
        "uq_member_universe_bop_register_number",
        "member",
        ["universe_id", "bop_register_number"],
        unique=True,
        postgresql_where=sa.text("bop_register_number IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_member_universe_bop_register_number", table_name="member")
    op.drop_constraint("ck_member_bop_register_number_format", "member", type_="check")
    op.drop_column("member", "bop_register_number")
