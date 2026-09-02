"""Add fleet_invites table

Revision ID: d54845acfb95
Revises: b4d5ed426fd0
Create Date: 2026-08-21 17:49:23.059617

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd54845acfb95'
down_revision: Union[str, None] = 'c2557519ddca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('fleet_invites',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('company_id', sa.Integer(), nullable=False, comment='The company this invite belongs to'),
    sa.Column('invite_token', sa.String(length=255), nullable=False, comment='Unique token embedded in QR code'),
    sa.Column('label', sa.String(length=255), nullable=True, comment="Human-readable label for this invite (e.g. 'Delhi Hub Drivers')"),
    sa.Column('is_active', sa.Boolean(), nullable=False, default=True, comment='Whether this invite can still be used'),
    sa.Column('max_uses', sa.Integer(), nullable=True, comment='Maximum number of times this invite can be used (null=unlimited)'),
    sa.Column('use_count', sa.Integer(), nullable=False, default=0, comment='How many times this invite has been used'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, comment='Optional expiry date for the invite'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fleet_invites_company_id'), 'fleet_invites', ['company_id'], unique=False)
    op.create_index(op.f('ix_fleet_invites_invite_token'), 'fleet_invites', ['invite_token'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_fleet_invites_invite_token'), table_name='fleet_invites')
    op.drop_index(op.f('ix_fleet_invites_company_id'), table_name='fleet_invites')
    op.drop_table('fleet_invites')
