"""merge_metadata_and_selfie

Revision ID: 8af4e498d85e
Revises: 892bd5f1331d, 8bfb490d091f
Create Date: 2026-09-06 19:33:31.627096

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8af4e498d85e'
down_revision: Union[str, None] = ('892bd5f1331d', '8bfb490d091f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
