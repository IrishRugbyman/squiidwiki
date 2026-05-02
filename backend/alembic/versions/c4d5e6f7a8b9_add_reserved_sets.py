"""add is_reserved to sets and seed Civilian/Police

Revision ID: c4d5e6f7a8b9
Revises: d4e5f6a7b8c9
Create Date: 2026-05-02
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'sets',
        sa.Column('is_reserved', sa.Boolean(), nullable=False, server_default=sa.text('false')),
    )

    conn = op.get_bind()
    universes = conn.execute(sa.text("SELECT id FROM universe")).fetchall()
    for (universe_id,) in universes:
        for name, slug in [('Civilian', 'civilian'), ('Police', 'police')]:
            exists = conn.execute(
                sa.text("SELECT 1 FROM sets WHERE universe_id = :uid AND name = :name LIMIT 1"),
                {"uid": str(universe_id), "name": name},
            ).fetchone()
            if not exists:
                conn.execute(
                    sa.text(
                        "INSERT INTO sets (id, universe_id, name, slug, status, is_reserved, created_at, updated_at)"
                        " VALUES (:id, :uid, :name, :slug, 'ACTIVE', true, now(), now())"
                    ),
                    {"id": str(uuid.uuid4()), "uid": str(universe_id), "name": name, "slug": slug},
                )


def downgrade() -> None:
    op.drop_column('sets', 'is_reserved')
