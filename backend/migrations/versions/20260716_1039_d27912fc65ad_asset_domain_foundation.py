"""asset_domain_foundation

Revision ID: d27912fc65ad
Revises: 42a8922a1403
Create Date: 2026-07-16 10:39:20.731083

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd27912fc65ad'
down_revision: Union[str, None] = '42a8922a1403'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'assets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('business_id', sa.String(length=255), nullable=False),
        sa.Column('asset_type', sa.String(length=50), nullable=False),
        sa.Column('manufacturer', sa.String(length=255), nullable=True),
        sa.Column('model', sa.String(length=255), nullable=True),
        sa.Column('serial_number', sa.String(length=255), nullable=True),
        sa.Column('firmware_version', sa.String(length=255), nullable=True),
        sa.Column('purchase_information', sa.JSON(), nullable=True),
        sa.Column('warranty_information', sa.JSON(), nullable=True),
        sa.Column('current_vehicle_id', sa.Integer(), nullable=True),
        sa.Column('installation_status', sa.String(length=20), server_default='REGISTERED', nullable=False),
        sa.Column('operational_status', sa.String(length=20), server_default='OK', nullable=False),
        sa.Column('origin_type', sa.String(length=50), nullable=True),
        sa.Column('origin_id', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['current_vehicle_id'], ['vehicles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('assets', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_assets_business_id'), ['business_id'], unique=True)
        batch_op.create_index(batch_op.f('ix_assets_asset_type'), ['asset_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_assets_serial_number'), ['serial_number'], unique=False)
        batch_op.create_index(batch_op.f('ix_assets_current_vehicle_id'), ['current_vehicle_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_assets_installation_status'), ['installation_status'], unique=False)
        batch_op.create_index(batch_op.f('ix_assets_operational_status'), ['operational_status'], unique=False)

    op.create_table(
        'asset_history_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('event_category', sa.String(length=50), nullable=False),
        sa.Column('performed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('origin_type', sa.String(length=50), nullable=True),
        sa.Column('origin_id', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('asset_history_records', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_asset_history_records_asset_id'), ['asset_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('asset_history_records', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_asset_history_records_asset_id'))
    op.drop_table('asset_history_records')

    with op.batch_alter_table('assets', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_assets_operational_status'))
        batch_op.drop_index(batch_op.f('ix_assets_installation_status'))
        batch_op.drop_index(batch_op.f('ix_assets_current_vehicle_id'))
        batch_op.drop_index(batch_op.f('ix_assets_serial_number'))
        batch_op.drop_index(batch_op.f('ix_assets_asset_type'))
        batch_op.drop_index(batch_op.f('ix_assets_business_id'))
    op.drop_table('assets')
