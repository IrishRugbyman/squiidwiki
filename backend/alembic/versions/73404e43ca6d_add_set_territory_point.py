"""add territory_point to sets

Adds an optional GeoJSON Point field for sets that only have a known
intersection / address rather than a full polygon territory.

Revision ID: 73404e43ca6d
Revises: 02b201cab602
Create Date: 2026-05-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "73404e43ca6d"
down_revision: Union[str, None] = "02b201cab602"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("sets", sa.Column("territory_point", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("sets", "territory_point")
