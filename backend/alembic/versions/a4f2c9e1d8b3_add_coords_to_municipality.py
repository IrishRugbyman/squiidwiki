"""add lat/lng coordinates to municipality

Revision ID: a4f2c9e1d8b3
Revises: e2f4a6b8c0d1
Create Date: 2026-04-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a4f2c9e1d8b3'
down_revision: Union[str, None] = 'e2f4a6b8c0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('municipality', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('municipality', sa.Column('longitude', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('municipality', 'longitude')
    op.drop_column('municipality', 'latitude')
