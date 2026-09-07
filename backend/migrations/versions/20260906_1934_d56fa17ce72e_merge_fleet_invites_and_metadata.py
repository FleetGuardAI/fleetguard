"""merge_fleet_invites_and_metadata

Revision ID: d56fa17ce72e
Revises: 8af4e498d85e, d54845acfb95
Create Date: 2026-09-06 19:34:24.875298

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd56fa17ce72e'
down_revision: Union[str, None] = ('8af4e498d85e', 'd54845acfb95')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
