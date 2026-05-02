"""add set_id and alliance_id to media

Extends the media table so photos can be attached to sets and alliances
in addition to members. Drops the old CHECK constraint (member/incident/source
exactly-one) and replaces it with one that covers all five entity columns.

Revision ID: d1e2f3a4b5c6
Revises: c8a2b3d4e5f6
Create Date: 2026-05-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c8a2b3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('media', sa.Column('set_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('media', sa.Column('alliance_id', postgresql.UUID(as_uuid=True), nullable=True))

    op.create_foreign_key(
        'media_set_id_fkey', 'media', 'sets', ['set_id'], ['id'], ondelete='CASCADE'
    )
    op.create_foreign_key(
        'media_alliance_id_fkey', 'media', 'alliance', ['alliance_id'], ['id'], ondelete='CASCADE'
    )

    op.create_index('ix_media_set_id', 'media', ['set_id'])
    op.create_index('ix_media_alliance_id', 'media', ['alliance_id'])

    op.drop_constraint('media_attaches_to_exactly_one_entity', 'media', type_='check')
    op.create_check_constraint(
        'media_attaches_to_exactly_one_entity',
        'media',
        'num_nonnulls(member_id, incident_id, source_id, set_id, alliance_id) = 1',
    )


def downgrade() -> None:
    op.drop_constraint('media_attaches_to_exactly_one_entity', 'media', type_='check')
    op.create_check_constraint(
        'media_attaches_to_exactly_one_entity',
        'media',
        'num_nonnulls(member_id, incident_id, source_id) = 1',
    )

    op.drop_index('ix_media_alliance_id', table_name='media')
    op.drop_index('ix_media_set_id', table_name='media')
    op.drop_constraint('media_alliance_id_fkey', 'media', type_='foreignkey')
    op.drop_constraint('media_set_id_fkey', 'media', type_='foreignkey')
    op.drop_column('media', 'alliance_id')
    op.drop_column('media', 'set_id')
