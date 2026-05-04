"""add FIGHT to incidenttype enum

Revision ID: f9a1b2c3d4e5
Revises: f3a8c9d0e1b2
Create Date: 2026-05-03
"""
from alembic import op

revision = 'f9a1b2c3d4e5'
down_revision = 'f3a8c9d0e1b2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE incidenttype ADD VALUE IF NOT EXISTS 'FIGHT'")


def downgrade() -> None:
    # Postgres does not support removing enum values; downgrade is a no-op.
    pass
