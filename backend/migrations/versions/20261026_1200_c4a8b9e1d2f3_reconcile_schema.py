"""reconcile_ghost_revision

Revision ID: c4a8b9e1d2f3
Revises: 5df0285937a9
Create Date: 2026-10-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4a8b9e1d2f3'
down_revision: Union[str, None] = '5df0285937a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
