"""merge multiple heads

Revision ID: 9abf6245e447
Revises: 8f7db5b1c7a5, e578cf4cf607
Create Date: 2026-09-22 22:17:34.681588

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9abf6245e447'
down_revision: Union[str, None] = ('8f7db5b1c7a5', 'e578cf4cf607')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
