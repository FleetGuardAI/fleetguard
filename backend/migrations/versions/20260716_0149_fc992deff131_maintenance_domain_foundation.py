"""maintenance_domain_foundation

Revision ID: fc992deff131
Revises: a34e738eba91
Create Date: 2026-07-16 01:49:40.071324

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fc992deff131'
down_revision: Union[str, None] = 'a34e738eba91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'maintenance_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('business_id', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='CREATED', nullable=False),
        sa.Column('category', sa.String(length=20), server_default='PREVENTIVE', nullable=False),
        sa.Column('vehicle_id', sa.Integer(), nullable=True),
        sa.Column('workshop', sa.String(length=255), nullable=True),
        sa.Column('service_provider', sa.String(length=255), nullable=True),
        sa.Column('scheduled_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('origin_type', sa.String(length=50), nullable=True),
        sa.Column('origin_id', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('maintenance_records', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_maintenance_records_business_id'), ['business_id'], unique=True)
        batch_op.create_index(batch_op.f('ix_maintenance_records_category'), ['category'], unique=False)
        batch_op.create_index(batch_op.f('ix_maintenance_records_status'), ['status'], unique=False)
        batch_op.create_index(batch_op.f('ix_maintenance_records_vehicle_id'), ['vehicle_id'], unique=False)

    op.create_table(
        'maintenance_tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('maintenance_record_id', sa.Integer(), nullable=False),
        sa.Column('task_type', sa.String(length=50), server_default='OTHER', nullable=False),
        sa.Column('description', sa.String(length=500), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='PENDING', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('performed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('origin_type', sa.String(length=50), nullable=True),
        sa.Column('origin_id', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['maintenance_record_id'], ['maintenance_records.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('maintenance_tasks', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_maintenance_tasks_maintenance_record_id'), ['maintenance_record_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('maintenance_tasks', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_maintenance_tasks_maintenance_record_id'))
    op.drop_table('maintenance_tasks')

    with op.batch_alter_table('maintenance_records', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_maintenance_records_vehicle_id'))
        batch_op.drop_index(batch_op.f('ix_maintenance_records_status'))
        batch_op.drop_index(batch_op.f('ix_maintenance_records_category'))
        batch_op.drop_index(batch_op.f('ix_maintenance_records_business_id'))
    op.drop_table('maintenance_records')
