"""trip_domain_foundation

Revision ID: a34e738eba91
Revises: 26b5d244efc9
Create Date: 2026-07-16 01:31:44.281347

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a34e738eba91'
down_revision: Union[str, None] = '26b5d244efc9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'trips',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('trip_id', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='CREATED', nullable=False),
        sa.Column('origin_location', sa.String(length=255), nullable=True),
        sa.Column('destination_location', sa.String(length=255), nullable=True),
        sa.Column('planned_distance', sa.Float(), nullable=True),
        sa.Column('actual_distance', sa.Float(), nullable=True),
        sa.Column('planned_start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('planned_end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('vehicle_id', sa.Integer(), nullable=True),
        sa.Column('driver_id', sa.Integer(), nullable=True),
        sa.Column('origin_type', sa.String(length=50), nullable=True),
        sa.Column('origin_id', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('trips', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_trips_driver_id'), ['driver_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_trips_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_trips_trip_id'), ['trip_id'], unique=True)
        batch_op.create_index(batch_op.f('ix_trips_vehicle_id'), ['vehicle_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('trips', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_trips_vehicle_id'))
        batch_op.drop_index(batch_op.f('ix_trips_trip_id'))
        batch_op.drop_index(batch_op.f('ix_trips_status'))
        batch_op.drop_index(batch_op.f('ix_trips_driver_id'))
    op.drop_table('trips')
