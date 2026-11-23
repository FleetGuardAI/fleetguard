"""merge main and develop migration heads

Revision ID: c91c576a9bba
Revises: 31203b23ef0b, f2b3c4d5e6a7
Create Date: 2026-11-24 01:59:13.375571

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c91c576a9bba'
down_revision: Union[str, None] = ('31203b23ef0b', 'f2b3c4d5e6a7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
