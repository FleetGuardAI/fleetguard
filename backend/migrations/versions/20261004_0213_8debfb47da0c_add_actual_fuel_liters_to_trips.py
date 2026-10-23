"""Add actual_fuel_liters to trips

Revision ID: 8debfb47da0c
Revises: 329103976f43
Create Date: 2026-10-04 02:13:08.896703

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8debfb47da0c'
down_revision: Union[str, None] = '329103976f43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('trips', sa.Column('actual_fuel_liters', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('trips', 'actual_fuel_liters')
