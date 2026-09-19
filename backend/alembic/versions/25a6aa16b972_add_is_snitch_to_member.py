"""add is_snitch to member

Revision ID: 25a6aa16b972
Revises: 4ed6ee82caee
Create Date: 2026-08-28 13:52:00.272357

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "25a6aa16b972"
down_revision: str | None = "4ed6ee82caee"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "member", sa.Column("is_snitch", sa.Boolean(), server_default="false", nullable=False)
    )


def downgrade() -> None:
    op.drop_column("member", "is_snitch")
