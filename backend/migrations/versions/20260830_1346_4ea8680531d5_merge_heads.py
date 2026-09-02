"""merge_heads

Revision ID: 4ea8680531d5
Revises: ecaec75c011c, c121c0718965
Create Date: 2026-08-30 13:46:04.911798

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ea8680531d5'
down_revision: Union[str, None] = ('ecaec75c011c', 'c121c0718965')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
