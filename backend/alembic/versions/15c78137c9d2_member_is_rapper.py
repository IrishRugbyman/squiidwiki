"""add member.is_rapper

Rapping is an attribute of the person, so it gets a column instead of living as
a biography sentence ("A rapper.") that the bio rule bans.

Revision ID: 15c78137c9d2
Revises: d22cf0b32fde
Create Date: 2026-08-22
"""

import sqlalchemy as sa

from alembic import op

revision = "15c78137c9d2"
down_revision = "d22cf0b32fde"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "member",
        sa.Column("is_rapper", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("member", "is_rapper")
