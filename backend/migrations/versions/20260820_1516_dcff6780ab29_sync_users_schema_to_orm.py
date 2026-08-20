"""Sync users schema to ORM

Revision ID: dcff6780ab29
Revises: 005a340d1e3d
Create Date: 2026-08-20 15:16:27.368062

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dcff6780ab29'
down_revision: Union[str, None] = '005a340d1e3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns if they do not exist
    op.add_column('users', sa.Column('full_name', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('mobile_number', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.alter_column('users', 'hashed_password', new_column_name='password_hash')
    op.create_index(op.f('ix_users_mobile_number'), 'users', ['mobile_number'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

def downgrade() -> None:
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_mobile_number'), table_name='users')
    op.alter_column('users', 'password_hash', new_column_name='hashed_password')
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'created_at')
    op.drop_column('users', 'mobile_number')
    op.drop_column('users', 'full_name')
