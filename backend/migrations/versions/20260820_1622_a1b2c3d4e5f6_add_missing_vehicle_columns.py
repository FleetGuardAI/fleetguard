"""add_missing_vehicle_columns

Revision ID: a1b2c3d4e5f6
Revises: c4683c6b38c6
Create Date: 2026-08-20 16:22:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'c4683c6b38c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns that exist in the ORM model but are missing from the DB
    with op.batch_alter_table('vehicles') as batch_op:
        batch_op.add_column(sa.Column('make', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('model', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('year', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('tank_capacity', sa.Float(), nullable=False, server_default='400.0'))
        batch_op.add_column(sa.Column('assigned_driver_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_vehicles_assigned_driver_id',
            'drivers', ['assigned_driver_id'], ['id'],
            ondelete='SET NULL'
        )
        batch_op.create_index('ix_vehicles_assigned_driver_id', ['assigned_driver_id'])


def downgrade() -> None:
    with op.batch_alter_table('vehicles') as batch_op:
        batch_op.drop_index('ix_vehicles_assigned_driver_id')
        batch_op.drop_constraint('fk_vehicles_assigned_driver_id', type_='foreignkey')
        batch_op.drop_column('assigned_driver_id')
        batch_op.drop_column('tank_capacity')
        batch_op.drop_column('year')
        batch_op.drop_column('model')
        batch_op.drop_column('make')
