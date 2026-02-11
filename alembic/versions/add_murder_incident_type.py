"""Add MURDER to incident type enum

Revision ID: add_murder_incident_type
Revises: add_nickname_unknown
Create Date: 2026-02-11

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'add_murder_incident_type'
down_revision: Union[str, None] = 'add_nickname_unknown'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite doesn't support ALTER TYPE for enums directly
    # We need to work around this by not enforcing enum constraint at DB level
    # The application layer will enforce the enum values
    pass


def downgrade() -> None:
    pass
