"""processing_engine_foundation

Revision ID: e5653c63763b
Revises: d27912fc65ad
Create Date: 2026-07-16 15:45:12.936581

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5653c63763b'
down_revision: Union[str, None] = 'd27912fc65ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'processing_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='PENDING', nullable=False),
        sa.Column('domains_invoked', sa.JSON(), nullable=True),
        sa.Column('domains_failed', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('processing_records', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_processing_records_event_id'), ['event_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_processing_records_status'), ['status'], unique=False)

def downgrade() -> None:
    with op.batch_alter_table('processing_records', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_processing_records_status'))
        batch_op.drop_index(batch_op.f('ix_processing_records_event_id'))
    op.drop_table('processing_records')
