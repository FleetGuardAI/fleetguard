"""merge_loc_idx_and_release_heads

Revision ID: 5df0285937a9
Revises: 20261023_loc_idx, b2d4f6h8j0l2
Create Date: 2026-10-25 23:10:52.590525

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5df0285937a9'
down_revision: Union[str, None] = ('20261023_loc_idx', 'b2d4f6h8j0l2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
