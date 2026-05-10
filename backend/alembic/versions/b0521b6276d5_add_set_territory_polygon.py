"""add territory_polygon to sets

Stores a GeoJSON Polygon (with optional holes) as the visual + spatial boundary
of a set's claimed turf. The existing set_municipality M2M (territory_ids) stays
the source of truth for stats/queries; the polygon is supplementary.

Revision ID: b0521b6276d5
Revises: 1a22eaa1c32a
Create Date: 2026-05-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "b0521b6276d5"
down_revision: Union[str, None] = "1a22eaa1c32a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sets",
        sa.Column("territory_polygon", JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sets", "territory_polygon")
