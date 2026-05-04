"""merge fight enum and reserved sets

Revision ID: 146b17a0feff
Revises: c4d5e6f7a8b9, f9a1b2c3d4e5
Create Date: 2026-05-03 15:20:27.720258

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = '146b17a0feff'
down_revision: Union[str, None] = ('c4d5e6f7a8b9', 'f9a1b2c3d4e5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
