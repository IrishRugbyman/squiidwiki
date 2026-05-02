"""add member.death_incident_id

Adds a nullable FK column on member pointing to the incident that killed
them, populated automatically by the incident CRUD when a participant has
outcome=KILLED. ON DELETE SET NULL so deleting an incident gracefully
unlinks the member without flipping their status.

Revision ID: a7c1f3d2e4b5
Revises: d8a1b2c3e4f5
Create Date: 2026-04-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'a7c1f3d2e4b5'
down_revision: Union[str, None] = 'd8a1b2c3e4f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'member',
        sa.Column('death_incident_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'member_death_incident_id_fkey',
        'member',
        'incident',
        ['death_incident_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index(
        'ix_member_death_incident_id',
        'member',
        ['death_incident_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_member_death_incident_id', table_name='member')
    op.drop_constraint('member_death_incident_id_fkey', 'member', type_='foreignkey')
    op.drop_column('member', 'death_incident_id')
