"""add color_secondary to gang

Stores a second traditional color per gang nation so territory map polygons
can use primary color for fill and secondary for stroke.

Revision ID: 07ea27d25af6
Revises: 73404e43ca6d
Create Date: 2026-05-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "07ea27d25af6"
down_revision: Union[str, None] = "73404e43ca6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("gang", sa.Column("color_secondary", sa.String(16), nullable=True))


def downgrade() -> None:
    op.drop_column("gang", "color_secondary")
