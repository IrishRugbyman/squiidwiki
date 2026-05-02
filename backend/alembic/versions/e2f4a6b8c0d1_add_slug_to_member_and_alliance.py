"""add slug to member and alliance

Revision ID: e2f4a6b8c0d1
Revises: 10d0ba868d7f
Create Date: 2026-04-20

"""
from alembic import op
import sqlalchemy as sa

revision = 'e2f4a6b8c0d1'
down_revision = '10d0ba868d7f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('member', sa.Column('slug', sa.String(), nullable=True))
    op.create_index('ix_member_slug', 'member', ['slug'])
    op.add_column('alliance', sa.Column('slug', sa.String(), nullable=True))
    op.create_index('ix_alliance_slug', 'alliance', ['slug'])


def downgrade():
    op.drop_index('ix_alliance_slug', table_name='alliance')
    op.drop_column('alliance', 'slug')
    op.drop_index('ix_member_slug', table_name='member')
    op.drop_column('member', 'slug')
