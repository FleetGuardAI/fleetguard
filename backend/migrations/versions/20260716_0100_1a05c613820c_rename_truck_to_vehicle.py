"""rename_truck_to_vehicle

Revision ID: 1a05c613820c
Revises: 001_operational_event
Create Date: 2026-07-16 01:00:51.382057

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a05c613820c'
down_revision: Union[str, None] = '001_operational_event'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename tables
    op.rename_table('trucks', 'vehicles')
    
    # Rename columns in related tables (SQLite safe using explicit alter_column with batch or raw SQL)
    # Using batch_alter_table is safer across all SQL backends for SQLite.
    
    with op.batch_alter_table('vehicles') as batch_op:
        batch_op.alter_column('license_plate', new_column_name='registration_number')
        batch_op.add_column(sa.Column('vin', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('engine_number', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('status', sa.String(20), server_default='ACTIVE', nullable=False))
        batch_op.add_column(sa.Column('ownership_info', sa.String(255), nullable=True))
        batch_op.add_column(sa.Column('origin_type', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('origin_id', sa.String(255), nullable=True))
        batch_op.create_index('ix_vehicles_vin', ['vin'], unique=True)
        batch_op.create_index('ix_vehicles_status', ['status'])

    with op.batch_alter_table('tickets') as batch_op:
        batch_op.alter_column('truck_id', new_column_name='vehicle_id')
        
    with op.batch_alter_table('fuel_logs') as batch_op:
        batch_op.alter_column('truck_id', new_column_name='vehicle_id')

    with op.batch_alter_table('fuel_states') as batch_op:
        batch_op.alter_column('truck_id', new_column_name='vehicle_id')

    with op.batch_alter_table('fuel_transactions') as batch_op:
        batch_op.alter_column('truck_id', new_column_name='vehicle_id')


def downgrade() -> None:
    with op.batch_alter_table('fuel_transactions') as batch_op:
        batch_op.alter_column('vehicle_id', new_column_name='truck_id')
        
    with op.batch_alter_table('fuel_states') as batch_op:
        batch_op.alter_column('vehicle_id', new_column_name='truck_id')
        
    with op.batch_alter_table('fuel_logs') as batch_op:
        batch_op.alter_column('vehicle_id', new_column_name='truck_id')

    with op.batch_alter_table('tickets') as batch_op:
        batch_op.alter_column('vehicle_id', new_column_name='truck_id')

    with op.batch_alter_table('vehicles') as batch_op:
        batch_op.drop_index('ix_vehicles_status')
        batch_op.drop_index('ix_vehicles_vin')
        batch_op.drop_column('origin_id')
        batch_op.drop_column('origin_type')
        batch_op.drop_column('ownership_info')
        batch_op.drop_column('status')
        batch_op.drop_column('engine_number')
        batch_op.drop_column('vin')
        batch_op.alter_column('registration_number', new_column_name='license_plate')

    op.rename_table('vehicles', 'trucks')
