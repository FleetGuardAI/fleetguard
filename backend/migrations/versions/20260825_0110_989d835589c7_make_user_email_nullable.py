"""make_user_email_nullable

Revision ID: 989d835589c7
Revises: c2557519ddca
Create Date: 2026-08-25 01:10:57.319163

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '989d835589c7'
down_revision: Union[str, None] = 'c2557519ddca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('users', 'email', nullable=True)


def downgrade() -> None:
    op.alter_column('users', 'email', nullable=False)
