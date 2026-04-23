"""replace lat/lng with geometry JSONB on municipality

Revision ID: b5e3f1a2d4c6
Revises: a4f2c9e1d8b3
Create Date: 2026-04-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = 'b5e3f1a2d4c6'
down_revision: Union[str, None] = 'a4f2c9e1d8b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('municipality', 'latitude')
    op.drop_column('municipality', 'longitude')
    op.add_column('municipality', sa.Column('geometry', JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column('municipality', 'geometry')
    op.add_column('municipality', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('municipality', sa.Column('longitude', sa.Float(), nullable=True))
