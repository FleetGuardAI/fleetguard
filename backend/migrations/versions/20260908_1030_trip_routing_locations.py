"""add trip routing locations

Revision ID: 20260908_1030_routing
Revises: abcdef123456
Create Date: 2026-09-08 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260908_1030_routing'
down_revision: Union[str, None] = 'abcdef123456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Vehicles table
    op.add_column('vehicles', sa.Column('fuel_type', sa.String(length=50), nullable=True))
    
    # Trips table
    op.add_column('trips', sa.Column('origin_lat', sa.Float(), nullable=True))
    op.add_column('trips', sa.Column('origin_lng', sa.Float(), nullable=True))
    op.add_column('trips', sa.Column('origin_place_id', sa.String(length=255), nullable=True))
    op.add_column('trips', sa.Column('origin_address', sa.String(length=500), nullable=True))
    
    op.add_column('trips', sa.Column('destination_lat', sa.Float(), nullable=True))
    op.add_column('trips', sa.Column('destination_lng', sa.Float(), nullable=True))
    op.add_column('trips', sa.Column('destination_place_id', sa.String(length=255), nullable=True))
    op.add_column('trips', sa.Column('destination_address', sa.String(length=500), nullable=True))
    
    op.add_column('trips', sa.Column('route_distance_km', sa.Float(), nullable=True))
    op.add_column('trips', sa.Column('route_duration_hours', sa.Float(), nullable=True))
    op.add_column('trips', sa.Column('route_toll_estimate', sa.Float(), nullable=True))
    op.add_column('trips', sa.Column('route_provider', sa.String(length=50), nullable=True))
    op.add_column('trips', sa.Column('route_polyline', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('vehicles', 'fuel_type')
    
    op.drop_column('trips', 'route_polyline')
    op.drop_column('trips', 'route_provider')
    op.drop_column('trips', 'route_toll_estimate')
    op.drop_column('trips', 'route_duration_hours')
    op.drop_column('trips', 'route_distance_km')
    
    op.drop_column('trips', 'destination_address')
    op.drop_column('trips', 'destination_place_id')
    op.drop_column('trips', 'destination_lng')
    op.drop_column('trips', 'destination_lat')
    
    op.drop_column('trips', 'origin_address')
    op.drop_column('trips', 'origin_place_id')
    op.drop_column('trips', 'origin_lng')
    op.drop_column('trips', 'origin_lat')
