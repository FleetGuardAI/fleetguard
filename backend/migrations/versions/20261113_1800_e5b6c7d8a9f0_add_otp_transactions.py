"""Add otp_transactions table for persistent FG-SEC-002 identity binding

Revision ID: e5b6c7d8a9f0
Revises: f1a2b3c4d5e6
Create Date: 2026-11-13 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e5b6c7d8a9f0'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'otp_transactions' not in tables:
        op.create_table(
            'otp_transactions',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column('req_id', sa.String(length=128), nullable=False),
            sa.Column('recipient_fingerprint', sa.String(length=64), nullable=False),
            sa.Column('provider', sa.String(length=50), nullable=False, server_default='MSG91'),
            sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('is_consumed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('consumed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index('ix_otp_transactions_req_id', 'otp_transactions', ['req_id'], unique=True)
        op.create_index('ix_otp_transactions_recipient_fingerprint', 'otp_transactions', ['recipient_fingerprint'])
        op.create_index('ix_otp_transactions_expires_at', 'otp_transactions', ['expires_at'])
        op.create_index('ix_otp_transactions_is_consumed', 'otp_transactions', ['is_consumed'])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'otp_transactions' in tables:
        op.drop_index('ix_otp_transactions_is_consumed', table_name='otp_transactions')
        op.drop_index('ix_otp_transactions_expires_at', table_name='otp_transactions')
        op.drop_index('ix_otp_transactions_recipient_fingerprint', table_name='otp_transactions')
        op.drop_index('ix_otp_transactions_req_id', table_name='otp_transactions')
        op.drop_table('otp_transactions')
