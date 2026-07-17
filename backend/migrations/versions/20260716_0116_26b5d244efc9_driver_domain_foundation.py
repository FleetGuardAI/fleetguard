"""driver_domain_foundation

Revision ID: 26b5d244efc9
Revises: 1a05c613820c
Create Date: 2026-07-16 01:16:11.277673

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26b5d244efc9'
down_revision: Union[str, None] = '1a05c613820c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('drivers') as batch_op:
        # Add new fields
        batch_op.add_column(sa.Column('employee_id', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('license_number', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('license_valid_until', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('employment_status', sa.String(20), nullable=True))
        batch_op.add_column(sa.Column('status', sa.String(20), server_default='ACTIVE', nullable=False))
        batch_op.add_column(sa.Column('origin_type', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('origin_id', sa.String(255), nullable=True))
        
        # Add new indexes
        batch_op.create_index('ix_drivers_employee_id', ['employee_id'], unique=True)
        batch_op.create_index('ix_drivers_license_number', ['license_number'], unique=True)
        batch_op.create_index('ix_drivers_status', ['status'])

        # Drop legacy fields
        batch_op.drop_column('risk_score')
        batch_op.drop_column('rating')
        batch_op.drop_column('total_trips')
        batch_op.drop_column('total_expenses')
        batch_op.drop_column('is_active')


def downgrade() -> None:
    with op.batch_alter_table('drivers') as batch_op:
        # Re-add legacy fields
        batch_op.add_column(sa.Column('risk_score', sa.Float(), server_default='0.0', nullable=False))
        batch_op.add_column(sa.Column('rating', sa.Float(), server_default='5.0', nullable=False))
        batch_op.add_column(sa.Column('total_trips', sa.Integer(), server_default='0', nullable=False))
        batch_op.add_column(sa.Column('total_expenses', sa.Float(), server_default='0.0', nullable=False))
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False))

        # Drop new indexes
        batch_op.drop_index('ix_drivers_status')
        batch_op.drop_index('ix_drivers_license_number')
        batch_op.drop_index('ix_drivers_employee_id')

        # Drop new fields
        batch_op.drop_column('origin_id')
        batch_op.drop_column('origin_type')
        batch_op.drop_column('status')
        batch_op.drop_column('employment_status')
        batch_op.drop_column('license_valid_until')
        batch_op.drop_column('license_number')
        batch_op.drop_column('employee_id')
