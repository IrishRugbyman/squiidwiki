"""add member_alias table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'member_alias',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('member_id', UUID(as_uuid=True), nullable=False),
        sa.Column('alias', sa.Text(), nullable=False),
        sa.Column('from_date', JSONB(), nullable=True),
        sa.Column('until_date', JSONB(), nullable=True),
        sa.Column('source_id', UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['member_id'], ['member.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['source.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_member_alias_member_id', 'member_alias', ['member_id'])


def downgrade() -> None:
    op.drop_index('ix_member_alias_member_id', table_name='member_alias')
    op.drop_table('member_alias')
