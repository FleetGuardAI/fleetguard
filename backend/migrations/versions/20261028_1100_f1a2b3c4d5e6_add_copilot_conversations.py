"""Add copilot_conversations and copilot_messages tables

Revision ID: f1a2b3c4d5e6
Revises: 5df0285937a9
Create Date: 2026-10-28 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.types import JSON

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = '5df0285937a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'copilot_conversations' not in tables:
        op.create_table(
            'copilot_conversations',
            sa.Column('id', sa.String(length=50), primary_key=True, nullable=False, comment='UUID string conversation identifier'),
            sa.Column('company_id', sa.Integer(), nullable=False, comment='Tenant company ID'),
            sa.Column('user_id', sa.Integer(), nullable=False, comment='Owner user ID'),
            sa.Column('title', sa.String(length=255), nullable=False, server_default='New Conversation', comment='Display title derived from user inquiry'),
            sa.Column('summary', sa.Text(), nullable=True, comment='Compact rolling summary of older conversational context'),
            sa.Column('summary_updated_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when rolling summary was last generated'),
            sa.Column('is_archived', sa.Boolean(), nullable=False, server_default=sa.text('false'), comment='Archive flag'),
            sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false'), comment='Soft deletion flag'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_copilot_conversations_company_id'), 'copilot_conversations', ['company_id'], unique=False)
        op.create_index(op.f('ix_copilot_conversations_user_id'), 'copilot_conversations', ['user_id'], unique=False)
        op.create_index('ix_copilot_conversations_user_company_updated', 'copilot_conversations', ['company_id', 'user_id', 'updated_at'], unique=False)

    if 'copilot_messages' not in tables:
        op.create_table(
            'copilot_messages',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('conversation_id', sa.String(length=50), nullable=False, comment='Foreign key to copilot_conversations.id'),
            sa.Column('sequence_number', sa.Integer(), nullable=False, server_default='1', comment='Chronological sequence within the conversation'),
            sa.Column('role', sa.String(length=20), nullable=False, comment='Message role: user, assistant, system, tool'),
            sa.Column('content', sa.Text(), nullable=False, comment='Text payload of message'),
            sa.Column('name', sa.String(length=100), nullable=True, comment='Tool name or author label'),
            sa.Column('tool_call_id', sa.String(length=100), nullable=True, comment='Tool call correlation ID for tool messages'),
            sa.Column('tool_calls', JSON, nullable=True, comment='Assistant tool calls payload'),
            sa.Column('message_metadata', JSON, nullable=True, comment='Structured card metadata (proposals, locations, status)'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.ForeignKeyConstraint(['conversation_id'], ['copilot_conversations.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_copilot_messages_conversation_id'), 'copilot_messages', ['conversation_id'], unique=False)
        op.create_index('ix_copilot_messages_conv_sequence', 'copilot_messages', ['conversation_id', 'sequence_number'], unique=False)


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if 'copilot_messages' in tables:
        op.drop_index('ix_copilot_messages_conv_sequence', table_name='copilot_messages')
        op.drop_index(op.f('ix_copilot_messages_conversation_id'), table_name='copilot_messages')
        op.drop_table('copilot_messages')

    if 'copilot_conversations' in tables:
        op.drop_index('ix_copilot_conversations_user_company_updated', table_name='copilot_conversations')
        op.drop_index(op.f('ix_copilot_conversations_user_id'), table_name='copilot_conversations')
        op.drop_index(op.f('ix_copilot_conversations_company_id'), table_name='copilot_conversations')
        op.drop_table('copilot_conversations')
