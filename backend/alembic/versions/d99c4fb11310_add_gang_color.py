"""add color to gang

Stores a CSS color (hex like #RRGGBB or #RRGGBBAA) per gang nation. Sets,
alliances, and members can derive their UI tint from their gang's color so
the same affiliation is visually consistent across avatars and the map.

Revision ID: d99c4fb11310
Revises: b0521b6276d5
Create Date: 2026-05-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d99c4fb11310"
down_revision: Union[str, None] = "b0521b6276d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("gang", sa.Column("color", sa.String(length=16), nullable=True))


def downgrade() -> None:
    op.drop_column("gang", "color")
