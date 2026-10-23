"""Extend password reset requests and tokens for admin approval workflow

Revision ID: b2c3d4e5f6a1
Revises: a1f893e4b7c2
Create Date: 2026-10-22 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a1'
down_revision: Union[str, None] = 'a1f893e4b7c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_cols_admin_req = [c['name'] for c in inspector.get_columns('admin_password_reset_requests')]

    if 'user_id' not in existing_cols_admin_req:
        op.add_column('admin_password_reset_requests', sa.Column('user_id', sa.Integer(), nullable=True))
        try:
            op.create_foreign_key('fk_admin_password_reset_requests_user_id', 'admin_password_reset_requests', 'users', ['user_id'], ['id'], ondelete='SET NULL')
        except Exception:
            pass

    if 'token_hash' not in existing_cols_admin_req:
        op.add_column('admin_password_reset_requests', sa.Column('token_hash', sa.String(length=128), nullable=True))
        try:
            op.create_index(op.f('ix_admin_password_reset_requests_token_hash'), 'admin_password_reset_requests', ['token_hash'], unique=False)
        except Exception:
            pass

    if 'token_issued_at' not in existing_cols_admin_req:
        op.add_column('admin_password_reset_requests', sa.Column('token_issued_at', sa.DateTime(timezone=True), nullable=True))

    if 'token_expires_at' not in existing_cols_admin_req:
        op.add_column('admin_password_reset_requests', sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True))

    if 'token_used_at' not in existing_cols_admin_req:
        op.add_column('admin_password_reset_requests', sa.Column('token_used_at', sa.DateTime(timezone=True), nullable=True))

    if 'token_revoked_at' not in existing_cols_admin_req:
        op.add_column('admin_password_reset_requests', sa.Column('token_revoked_at', sa.DateTime(timezone=True), nullable=True))

    if 'rejection_reason' not in existing_cols_admin_req:
        op.add_column('admin_password_reset_requests', sa.Column('rejection_reason', sa.Text(), nullable=True))

    existing_cols_tokens = [c['name'] for c in inspector.get_columns('password_reset_tokens')]
    if 'reset_request_id' not in existing_cols_tokens:
        op.add_column('password_reset_tokens', sa.Column('reset_request_id', sa.Integer(), nullable=True))
        try:
            op.create_foreign_key('fk_password_reset_tokens_request_id', 'password_reset_tokens', 'admin_password_reset_requests', ['reset_request_id'], ['id'], ondelete='SET NULL')
            op.create_index(op.f('ix_password_reset_tokens_reset_request_id'), 'password_reset_tokens', ['reset_request_id'], unique=False)
        except Exception:
            pass


def downgrade() -> None:
    pass
