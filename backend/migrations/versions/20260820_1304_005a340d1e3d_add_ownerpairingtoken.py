"""Add OwnerPairingToken

Revision ID: 005a340d1e3d
Revises: 123abc456def
Create Date: 2026-08-20 13:04:57.801877

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005a340d1e3d'
down_revision: Union[str, None] = '123abc456def'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('owner_pairing_tokens',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('pairing_token', sa.String(length=255), nullable=False),
    sa.Column('is_used', sa.Boolean(), nullable=False, default=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_owner_pairing_tokens_company_id'), 'owner_pairing_tokens', ['company_id'], unique=False)
    op.create_index(op.f('ix_owner_pairing_tokens_pairing_token'), 'owner_pairing_tokens', ['pairing_token'], unique=True)
    op.create_index(op.f('ix_owner_pairing_tokens_user_id'), 'owner_pairing_tokens', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_owner_pairing_tokens_user_id'), table_name='owner_pairing_tokens')
    op.drop_index(op.f('ix_owner_pairing_tokens_pairing_token'), table_name='owner_pairing_tokens')
    op.drop_index(op.f('ix_owner_pairing_tokens_company_id'), table_name='owner_pairing_tokens')
    op.drop_table('owner_pairing_tokens')
