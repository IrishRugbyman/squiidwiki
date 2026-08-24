"""add mdoc_number to member

The MDOC offender number is the handle OTIS looks people up by, and since the
2026 rebuild it is the *only* stable one: profiles no longer have URLs, so a
number is the sole way back to a record. Without this column every lookup began
from a name search, and a spell inside could never be re-checked as release
dates moved with parole and resentencing.

Nullable, and deliberately not unique: OTIS is the authority on whether two
people share a number, not this table.

Autogenerate proposed 82 operations for this one column, including dropping
ix_alliance_name_trgm, ix_sets_name_trgm, ix_source_title_trgm, several
ix_incident_* and ix_member_* indexes, the uq_gang_universe_name and
uq_gang_universe_slug unique constraints, and rewriting a dozen foreign keys.
All of it is pre-existing manual SQL that no model declares, so autogenerate
reads it as removed. Stripped: this revision adds one column and its index.

Revision ID: ab151cacd566
Revises: 9c86862259a3
Create Date: 2026-08-24 22:25:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

revision: str = "ab151cacd566"
down_revision: str | None = "9c86862259a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "member",
        sa.Column("mdoc_number", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    op.create_index(op.f("ix_member_mdoc_number"), "member", ["mdoc_number"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_member_mdoc_number"), table_name="member")
    op.drop_column("member", "mdoc_number")
