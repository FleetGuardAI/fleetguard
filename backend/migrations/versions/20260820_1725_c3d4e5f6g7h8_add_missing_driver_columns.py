"""add_missing_driver_columns

Revision ID: c3d4e5f6g7h8
Revises: b2c3d4e5f6g7
Create Date: 2026-08-20 17:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('drivers') as batch_op:
        # Rename phone to phone_number
        batch_op.alter_column('phone', new_column_name='phone_number')
        batch_op.create_index('ix_drivers_phone_number', ['phone_number'], unique=True)
        
        # Add new columns
        batch_op.add_column(sa.Column('avatar_url', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_drivers_users_id', 'users', ['user_id'], ['id'], ondelete='SET NULL')
        batch_op.create_unique_constraint('uq_drivers_user_id', ['user_id'])
        
        batch_op.add_column(sa.Column('license_front_url', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('license_back_url', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('aadhaar_front_url', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('aadhaar_back_url', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('selfie_url', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('aadhaar_number', sa.String(20), nullable=True))
        
        batch_op.add_column(sa.Column('verification_status', sa.String(50), nullable=True))
        batch_op.create_index('ix_drivers_verification_status', ['verification_status'])
        
        batch_op.add_column(sa.Column('face_verified', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('duty_status', sa.String(50), nullable=True))
        
        batch_op.add_column(sa.Column('last_known_lat', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('last_known_lng', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('last_location_at', sa.DateTime(timezone=True), nullable=True))
        
        batch_op.add_column(sa.Column('fcm_token', sa.String(500), nullable=True))
        batch_op.add_column(sa.Column('driver_score', sa.Float(), server_default='85.0', nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('drivers') as batch_op:
        batch_op.drop_column('driver_score')
        batch_op.drop_column('fcm_token')
        batch_op.drop_column('last_location_at')
        batch_op.drop_column('last_known_lng')
        batch_op.drop_column('last_known_lat')
        batch_op.drop_column('duty_status')
        batch_op.drop_column('face_verified')
        batch_op.drop_index('ix_drivers_verification_status')
        batch_op.drop_column('verification_status')
        batch_op.drop_column('aadhaar_number')
        batch_op.drop_column('selfie_url')
        batch_op.drop_column('aadhaar_back_url')
        batch_op.drop_column('aadhaar_front_url')
        batch_op.drop_column('license_back_url')
        batch_op.drop_column('license_front_url')
        batch_op.drop_constraint('uq_drivers_user_id', type_='unique')
        batch_op.drop_constraint('fk_drivers_users_id', type_='foreignkey')
        batch_op.drop_column('user_id')
        batch_op.drop_column('avatar_url')
        batch_op.drop_index('ix_drivers_phone_number')
        batch_op.alter_column('phone_number', new_column_name='phone')
