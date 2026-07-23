"""tyre_domain_foundation

Revision ID: 42a8922a1403
Revises: fc992deff131
Create Date: 2026-07-16 01:57:47.877273

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '42a8922a1403'
down_revision: Union[str, None] = 'fc992deff131'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tyres',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('serial_number', sa.String(length=255), nullable=False),
        sa.Column('manufacturer', sa.String(length=255), nullable=True),
        sa.Column('brand', sa.String(length=255), nullable=True),
        sa.Column('model', sa.String(length=255), nullable=True),
        sa.Column('size', sa.String(length=50), nullable=True),
        sa.Column('purchase_information', sa.JSON(), nullable=True),
        sa.Column('current_vehicle_id', sa.Integer(), nullable=True),
        sa.Column('current_position', sa.String(length=50), nullable=True),
        sa.Column('current_status', sa.String(length=20), server_default='REGISTERED', nullable=False),
        sa.Column('origin_type', sa.String(length=50), nullable=True),
        sa.Column('origin_id', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['current_vehicle_id'], ['vehicles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('tyres', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_tyres_serial_number'), ['serial_number'], unique=True)
        batch_op.create_index(batch_op.f('ix_tyres_current_vehicle_id'), ['current_vehicle_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_tyres_current_status'), ['current_status'], unique=False)

    op.create_table(
        'tyre_lifecycle_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('tyre_id', sa.Integer(), nullable=False),
        sa.Column('event_category', sa.String(length=50), nullable=False),
        sa.Column('performed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('origin_type', sa.String(length=50), nullable=True),
        sa.Column('origin_id', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['tyre_id'], ['tyres.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('tyre_lifecycle_records', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_tyre_lifecycle_records_tyre_id'), ['tyre_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('tyre_lifecycle_records', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_tyre_lifecycle_records_tyre_id'))
    op.drop_table('tyre_lifecycle_records')

    with op.batch_alter_table('tyres', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_tyres_current_status'))
        batch_op.drop_index(batch_op.f('ix_tyres_current_vehicle_id'))
        batch_op.drop_index(batch_op.f('ix_tyres_serial_number'))
    op.drop_table('tyres')
