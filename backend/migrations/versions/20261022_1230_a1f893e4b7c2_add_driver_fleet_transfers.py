"""Add driver_fleet_transfers table

Revision ID: a1f893e4b7c2
Revises: 73ee1c2f0419
Create Date: 2026-10-22 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1f893e4b7c2'
down_revision: Union[str, None] = '73ee1c2f0419'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Notice: Table may already exist from create_all in idempotent environment
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'driver_fleet_transfers' not in inspector.get_table_names():
        op.create_table(
            'driver_fleet_transfers',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('driver_id', sa.Integer(), nullable=False, comment='The driver requesting the transfer'),
            sa.Column('from_company_id', sa.Integer(), nullable=False, comment='Source fleet company ID'),
            sa.Column('to_company_id', sa.Integer(), nullable=False, comment='Target fleet company ID'),
            sa.Column('invite_token', sa.String(length=255), nullable=True, comment='The QR invite token used to initiate the transfer'),
            sa.Column('status', sa.String(length=50), nullable=False, comment='Status of the transfer request'),
            sa.Column('rejection_reason', sa.Text(), nullable=True, comment='Explanation if the transfer was rejected'),
            sa.Column('reviewed_by', sa.Integer(), nullable=True, comment='Admin user who approved or rejected the transfer'),
            sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp of approval or rejection'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['from_company_id'], ['companies.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['to_company_id'], ['companies.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_driver_fleet_transfers_driver_id'), 'driver_fleet_transfers', ['driver_id'], unique=False)
        op.create_index(op.f('ix_driver_fleet_transfers_from_company_id'), 'driver_fleet_transfers', ['from_company_id'], unique=False)
        op.create_index(op.f('ix_driver_fleet_transfers_to_company_id'), 'driver_fleet_transfers', ['to_company_id'], unique=False)
        op.create_index(op.f('ix_driver_fleet_transfers_status'), 'driver_fleet_transfers', ['status'], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'driver_fleet_transfers' in inspector.get_table_names():
        op.drop_index(op.f('ix_driver_fleet_transfers_status'), table_name='driver_fleet_transfers')
        op.drop_index(op.f('ix_driver_fleet_transfers_to_company_id'), table_name='driver_fleet_transfers')
        op.drop_index(op.f('ix_driver_fleet_transfers_from_company_id'), table_name='driver_fleet_transfers')
        op.drop_index(op.f('ix_driver_fleet_transfers_driver_id'), table_name='driver_fleet_transfers')
        op.drop_table('driver_fleet_transfers')
