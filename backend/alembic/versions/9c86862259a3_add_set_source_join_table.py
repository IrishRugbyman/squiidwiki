"""add set_source join table

Citations for a set itself, mirroring member_source / incident_source /
business_source. A set's history - when it formed, who founded it, what it split
from - comes from documents rather than from any one person, and until now there
was nowhere to cite that: the only option was hedging prose in `sets.bio`, which
the house rule forbids. Reliability belongs in the source row's rating.

Autogenerate additionally proposed dropping ix_alliance_name_trgm,
ix_sets_name_trgm, ix_source_title_trgm, ix_member_* and
uq_set_relationship_current, and rewriting several foreign keys. All of that is
pre-existing manual SQL that no model declares, so autogenerate reads it as
removed. It has been stripped: this revision creates one table and nothing else.

Revision ID: 9c86862259a3
Revises: 1d0dd3cf2631
Create Date: 2026-08-24 22:05:29.882096

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "9c86862259a3"
down_revision: str | None = "1d0dd3cf2631"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "set_source",
        sa.Column("set_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.Uuid(), nullable=False),
        # No ondelete, matching member_source and incident_source. The CRUD
        # delete paths break join rows explicitly, and declaring a rule here
        # that the model does not would resurface as drift on every autogenerate.
        sa.ForeignKeyConstraint(["set_id"], ["sets.id"]),
        sa.ForeignKeyConstraint(["source_id"], ["source.id"]),
        sa.PrimaryKeyConstraint("set_id", "source_id"),
    )


def downgrade() -> None:
    op.drop_table("set_source")
