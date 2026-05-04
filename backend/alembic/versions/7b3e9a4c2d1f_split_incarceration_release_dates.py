"""split incarceration to_date into earliest_release_date + max_discharge_date

Revision ID: 7b3e9a4c2d1f
Revises: 146b17a0feff
Create Date: 2026-05-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '7b3e9a4c2d1f'
down_revision = '146b17a0feff'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('member_incarceration', sa.Column('earliest_release_date', JSONB, nullable=True))
    op.add_column('member_incarceration', sa.Column('max_discharge_date', JSONB, nullable=True))
    op.execute('UPDATE member_incarceration SET max_discharge_date = to_date WHERE to_date IS NOT NULL')
    op.drop_column('member_incarceration', 'to_date')


def downgrade():
    op.add_column('member_incarceration', sa.Column('to_date', JSONB, nullable=True))
    op.execute('UPDATE member_incarceration SET to_date = max_discharge_date WHERE max_discharge_date IS NOT NULL')
    op.drop_column('member_incarceration', 'earliest_release_date')
    op.drop_column('member_incarceration', 'max_discharge_date')
