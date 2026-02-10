"""Add nickname_unknown to members

Revision ID: add_nickname_unknown
Revises: 21738d47ae82
Create Date: 2026-02-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'add_nickname_unknown'
down_revision: Union[str, None] = '21738d47ae82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('members', sa.Column('nickname_unknown', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column('members', 'nickname_unknown')
