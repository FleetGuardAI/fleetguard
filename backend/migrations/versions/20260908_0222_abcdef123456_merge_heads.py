"""Merge migration heads

Revision ID: abcdef123456
Revises: 39d36602ac27, a1b2c3d4e5f7
Create Date: 2026-09-08 02:22:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abcdef123456'
down_revision: Union[str, tuple[str, ...], None] = ('39d36602ac27', 'a1b2c3d4e5f7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
