"""add to_date to member_incarceration

Revision ID: 4ed6ee82caee
Revises: ab151cacd566
Create Date: 2026-08-25 21:59:39.728613

Autogenerate produced a page of unrelated drift (trigram indexes, partial unique
indexes and foreign keys declared in raw SQL that no model mirrors). All of it is
deleted here: this migration adds one column and nothing else.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "4ed6ee82caee"
down_revision: str | None = "ab151cacd566"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "member_incarceration",
        sa.Column("to_date", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("member_incarceration", "to_date")
