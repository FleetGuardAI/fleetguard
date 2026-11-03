"""merge_copilot_and_route_heads

Revision ID: 31203b23ef0b
Revises: f1a2b3c4d5e6, b7e2d9a1f3c5
Create Date: 2026-11-04 01:45:26.863043

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '31203b23ef0b'
down_revision: Union[str, None] = ('f1a2b3c4d5e6', 'b7e2d9a1f3c5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
