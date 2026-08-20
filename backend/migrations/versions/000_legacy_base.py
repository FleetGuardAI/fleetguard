"""legacy_base

Revision ID: 000_legacy_base
Revises: 
Create Date: 2026-07-10 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '000_legacy_base'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Create Enums (split for asyncpg)
    op.execute("CREATE TYPE ticketstatus AS ENUM ('OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED', 'REJECTED');")
    op.execute("CREATE TYPE risklevel AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');")
    op.execute("CREATE TYPE fuel_source AS ENUM ('TELEMATICS', 'MANUAL_ENTRY', 'CALCULATED');")
    op.execute("CREATE TYPE fuel_state_reliability AS ENUM ('HIGH', 'MEDIUM', 'LOW');")
    op.execute("CREATE TYPE fuel_transaction_type AS ENUM ('REFILL', 'THEFT', 'CONSUMPTION');")

    op.create_table('companies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_table('trucks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('license_plate', sa.String(length=50), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('license_plate')
    )
    op.create_table('drivers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('risk_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('rating', sa.Float(), nullable=False, server_default='5.0'),
        sa.Column('total_trips', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_expenses', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('fuel_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('truck_id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('raw_level', sa.Float(), nullable=False),
        sa.Column('filtered_level', sa.Float(), nullable=False),
        sa.Column('expected_level', sa.Float(), nullable=False),
        sa.Column('speed', sa.Float(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('is_theft_alert', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['truck_id'], ['trucks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('fuel_states',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('truck_id', sa.Integer(), nullable=False),
        sa.Column('current_level', sa.Float(), nullable=False),
        sa.Column('source', postgresql.ENUM(name='fuel_source', create_type=False), nullable=False),
        sa.Column('reliability', postgresql.ENUM(name='fuel_state_reliability', create_type=False), nullable=False),
        sa.Column('last_operational_event_id', sa.String(length=255), nullable=True),
        sa.Column('last_updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['truck_id'], ['trucks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('fuel_transactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('truck_id', sa.Integer(), nullable=False),
        sa.Column('transaction_type', postgresql.ENUM(name='fuel_transaction_type', create_type=False), nullable=False),
        sa.Column('amount_liters', sa.Float(), nullable=False),
        sa.Column('origin_type', sa.String(length=50), nullable=True),
        sa.Column('origin_id', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['truck_id'], ['trucks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tickets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('truck_id', sa.Integer(), nullable=True),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('issue_type', sa.String(length=100), nullable=False),
        sa.Column('vendor_name', sa.String(length=200), nullable=True),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('fair_price', sa.Float(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location_lat', sa.Float(), nullable=True),
        sa.Column('location_lng', sa.Float(), nullable=True),
        sa.Column('location_name', sa.String(length=300), nullable=True),
        sa.Column('receipt_url', sa.String(length=500), nullable=True),
        sa.Column('ocr_raw_response', sa.Text(), nullable=True),
        sa.Column('status', postgresql.ENUM(name='ticketstatus', create_type=False), nullable=False),
        sa.Column('risk_level', postgresql.ENUM(name='risklevel', create_type=False), nullable=False),
        sa.Column('risk_reasons', sa.Text(), nullable=True),
        sa.Column('is_duplicate', sa.Boolean(), nullable=False),
        sa.Column('expense_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('payout_reference', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ),
        sa.ForeignKeyConstraint(['truck_id'], ['trucks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('tickets')
    op.drop_table('fuel_transactions')
    op.drop_table('fuel_states')
    op.drop_table('fuel_logs')
    op.drop_table('drivers')
    op.drop_table('trucks')
    op.drop_table('users')
    op.drop_table('companies')
    op.execute("DROP TYPE IF EXISTS ticketstatus;")
    op.execute("DROP TYPE IF EXISTS risklevel;")
    op.execute("DROP TYPE IF EXISTS fuel_source;")
    op.execute("DROP TYPE IF EXISTS fuel_state_reliability;")
    op.execute("DROP TYPE IF EXISTS fuel_transaction_type;")
