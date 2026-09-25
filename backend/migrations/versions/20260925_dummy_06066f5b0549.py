"""dummy migration to fix render deployment

Revision ID: 06066f5b0549
Revises: 9abf6245e447
Create Date: 2026-09-25 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '06066f5b0549'
down_revision: Union[str, None] = '9abf6245e447'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
