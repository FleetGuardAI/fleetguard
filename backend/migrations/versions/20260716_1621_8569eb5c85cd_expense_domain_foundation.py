"""expense_domain_foundation

Revision ID: 8569eb5c85cd
Revises: e5653c63763b
Create Date: 2026-07-16 16:21:45.869900

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8569eb5c85cd'
down_revision: Union[str, None] = 'e5653c63763b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'expenses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='INR'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='RECORDED'),
        sa.Column('expense_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('receipt_reference', sa.String(length=255), nullable=True),
        sa.Column('business_id', sa.String(length=255), nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=True),
        sa.Column('driver_id', sa.Integer(), nullable=True),
        sa.Column('trip_id', sa.Integer(), nullable=True),
        sa.Column('maintenance_id', sa.Integer(), nullable=True),
        sa.Column('origin_type', sa.String(length=100), nullable=False, server_default='verified_event'),
        sa.Column('origin_id', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('expenses', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_expenses_category'), ['category'], unique=False)
        batch_op.create_index(batch_op.f('ix_expenses_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_expenses_business_id'), ['business_id'], unique=True)
        batch_op.create_index(batch_op.f('ix_expenses_vehicle_id'), ['vehicle_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_expenses_driver_id'), ['driver_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_expenses_trip_id'), ['trip_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_expenses_maintenance_id'), ['maintenance_id'], unique=False)

def downgrade() -> None:
    with op.batch_alter_table('expenses', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_expenses_maintenance_id'))
        batch_op.drop_index(batch_op.f('ix_expenses_trip_id'))
        batch_op.drop_index(batch_op.f('ix_expenses_driver_id'))
        batch_op.drop_index(batch_op.f('ix_expenses_vehicle_id'))
        batch_op.drop_index(batch_op.f('ix_expenses_business_id'))
        batch_op.drop_index(batch_op.f('ix_expenses_status'))
        batch_op.drop_index(batch_op.f('ix_expenses_category'))
    op.drop_table('expenses')
