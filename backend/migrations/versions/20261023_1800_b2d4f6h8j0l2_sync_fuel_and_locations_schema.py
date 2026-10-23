"""sync_fuel_and_locations_schema

Revision ID: b2d4f6h8j0l2
Revises: a1c2e3g4i5k6
Create Date: 2026-10-23 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b2d4f6h8j0l2'
down_revision: Union[str, None] = 'a1c2e3g4i5k6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    target_schema = op.get_context().version_table_schema
    existing_tables = set(insp.get_table_names(schema=target_schema))

    # 1. Sync fuel_transactions table columns to ORM expectations
    if "fuel_transactions" in existing_tables:
        cols = {c["name"] for c in insp.get_columns("fuel_transactions", schema=target_schema)}
        
        fuel_col_defs = [
            ("fuel_type", sa.String(length=50)),
            ("price_per_liter", sa.Float()),
            ("total_cost", sa.Float()),
            ("odometer", sa.Float()),
            ("station", sa.String(length=255)),
            ("receipt_url", sa.String(length=500)),
            ("reconciliation_status", sa.String(length=50)),
            ("reconciled_sensor_liters", sa.Float()),
            ("variance_liters", sa.Float()),
        ]
        for col_name, col_type in fuel_col_defs:
            if col_name not in cols:
                op.add_column("fuel_transactions", sa.Column(col_name, col_type, nullable=True))

    # 2. Ensure vehicle_current_locations table exists
    if "vehicle_current_locations" not in existing_tables:
        op.create_table(
            'vehicle_current_locations',
            sa.Column('vehicle_id', sa.Integer(), nullable=False),
            sa.Column('source', sa.String(length=50), nullable=False),
            sa.Column('latitude', sa.Float(), nullable=False),
            sa.Column('longitude', sa.Float(), nullable=False),
            sa.Column('speed', sa.Float(), nullable=True),
            sa.Column('heading', sa.Float(), nullable=True),
            sa.Column('accuracy', sa.Float(), nullable=True),
            sa.Column('last_timestamp', sa.DateTime(timezone=True), nullable=False),
            sa.Column('last_received_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('driver_id', sa.Integer(), nullable=True),
            sa.Column('device_id', sa.Integer(), nullable=True),
            sa.Column('source_metadata', sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(['device_id'], ['assets.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('vehicle_id', 'source')
        )
    else:
        vcl_cols = {c["name"] for c in insp.get_columns("vehicle_current_locations", schema=target_schema)}
        if "source_metadata" not in vcl_cols:
            op.add_column("vehicle_current_locations", sa.Column("source_metadata", sa.JSON(), nullable=True))

    # 3. Ensure vehicle_locations table exists
    if "vehicle_locations" not in existing_tables:
        op.create_table(
            'vehicle_locations',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('vehicle_id', sa.Integer(), nullable=False),
            sa.Column('driver_id', sa.Integer(), nullable=True),
            sa.Column('device_id', sa.Integer(), nullable=True),
            sa.Column('company_id', sa.Integer(), nullable=False),
            sa.Column('latitude', sa.Float(), nullable=False),
            sa.Column('longitude', sa.Float(), nullable=False),
            sa.Column('speed', sa.Float(), nullable=True),
            sa.Column('heading', sa.Float(), nullable=True),
            sa.Column('accuracy', sa.Float(), nullable=True),
            sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
            sa.Column('source', sa.String(length=50), nullable=False),
            sa.Column('event_fingerprint', sa.String(length=64), nullable=True),
            sa.Column('source_metadata', sa.JSON(), nullable=True),
            sa.Column('original_driver_location_id', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['device_id'], ['assets.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_vehicle_locations_vehicle_id', 'vehicle_locations', ['vehicle_id'], unique=False)
        op.create_index('ix_vehicle_locations_driver_id', 'vehicle_locations', ['driver_id'], unique=False)
        op.create_index('ix_vehicle_locations_company_id', 'vehicle_locations', ['company_id'], unique=False)
        op.create_index('ix_vehicle_locations_timestamp', 'vehicle_locations', ['timestamp'], unique=False)
    else:
        vl_cols = {c["name"] for c in insp.get_columns("vehicle_locations", schema=target_schema)}
        if "event_fingerprint" not in vl_cols:
            op.add_column("vehicle_locations", sa.Column("event_fingerprint", sa.String(length=64), nullable=True))
        if "source_metadata" not in vl_cols:
            op.add_column("vehicle_locations", sa.Column("source_metadata", sa.JSON(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    target_schema = op.get_context().version_table_schema
    existing_tables = set(insp.get_table_names(schema=target_schema))

    if "vehicle_locations" in existing_tables:
        op.drop_table("vehicle_locations")
    if "vehicle_current_locations" in existing_tables:
        op.drop_table("vehicle_current_locations")
    if "fuel_transactions" in existing_tables:
        cols = {c["name"] for c in insp.get_columns("fuel_transactions", schema=target_schema)}
        for c in ["variance_liters", "reconciled_sensor_liters", "reconciliation_status"]:
            if c in cols:
                op.drop_column("fuel_transactions", c)
