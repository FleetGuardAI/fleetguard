"""Add location tracking composite indexes and trip_id to driver_locations

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6a1
Create Date: 2026-10-23 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '20261023_loc_idx'
down_revision: Union[str, None] = 'b2c3d4e5f6a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # 1. Add trip_id column to driver_locations if not exists
    loc_cols = [c['name'] for c in inspector.get_columns('driver_locations')]
    if 'trip_id' not in loc_cols:
        op.add_column('driver_locations', sa.Column('trip_id', sa.String(255), nullable=True))
        op.create_index('ix_driver_locations_trip_id', 'driver_locations', ['trip_id'], unique=False)

    # 2. Add composite indexes for time-series range lookups on driver_locations
    loc_indexes = [idx['name'] for idx in inspector.get_indexes('driver_locations')]
    
    if 'idx_driver_locations_driver_timestamp' not in loc_indexes:
        op.create_index(
            'idx_driver_locations_driver_timestamp',
            'driver_locations',
            ['driver_id', 'timestamp'],
            unique=False
        )
        
    if 'idx_driver_locations_company_driver_ts' not in loc_indexes:
        op.create_index(
            'idx_driver_locations_company_driver_ts',
            'driver_locations',
            ['company_id', 'driver_id', 'timestamp'],
            unique=False
        )

    # 3. Add composite index on trips for company and driver lookup
    trip_indexes = [idx['name'] for idx in inspector.get_indexes('trips')]
    if 'idx_trips_company_driver' not in trip_indexes:
        op.create_index(
            'idx_trips_company_driver',
            'trips',
            ['company_id', 'driver_id'],
            unique=False
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    trip_indexes = [idx['name'] for idx in inspector.get_indexes('trips')]
    if 'idx_trips_company_driver' in trip_indexes:
        op.drop_index('idx_trips_company_driver', table_name='trips')

    loc_indexes = [idx['name'] for idx in inspector.get_indexes('driver_locations')]
    if 'idx_driver_locations_company_driver_ts' in loc_indexes:
        op.drop_index('idx_driver_locations_company_driver_ts', table_name='driver_locations')
    if 'idx_driver_locations_driver_timestamp' in loc_indexes:
        op.drop_index('idx_driver_locations_driver_timestamp', table_name='driver_locations')
    if 'ix_driver_locations_trip_id' in loc_indexes:
        op.drop_index('ix_driver_locations_trip_id', table_name='driver_locations')
        
    loc_cols = [c['name'] for c in inspector.get_columns('driver_locations')]
    if 'trip_id' in loc_cols:
        op.drop_column('driver_locations', 'trip_id')
