"""add lat/lng to incident

Revision ID: a1b2c3d4e5f6
Revises: e5f6a7b8c9d0
Create Date: 2026-05-02
"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('incident', sa.Column('lat', sa.Float(), nullable=True))
    op.add_column('incident', sa.Column('lng', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('incident', 'lng')
    op.drop_column('incident', 'lat')
