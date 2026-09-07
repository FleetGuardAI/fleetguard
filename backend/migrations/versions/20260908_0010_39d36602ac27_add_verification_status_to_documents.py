"""Add verification status to documents

Revision ID: 39d36602ac27
Revises: d56fa17ce72e
Create Date: 2026-09-08 00:10:57.059614

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39d36602ac27'
down_revision: Union[str, None] = 'd56fa17ce72e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add verification fields to documents table
    op.add_column('documents', sa.Column('verification_status', sa.String(length=50), server_default='PENDING', nullable=False))
    op.add_column('documents', sa.Column('rejection_reason', sa.String(length=500), nullable=True))
    op.add_column('documents', sa.Column('verified_by', sa.String(length=255), nullable=True))
    op.add_column('documents', sa.Column('verified_at', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_documents_verification_status'), 'documents', ['verification_status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_documents_verification_status'), table_name='documents')
    op.drop_column('documents', 'verified_at')
    op.drop_column('documents', 'verified_by')
    op.drop_column('documents', 'rejection_reason')
    op.drop_column('documents', 'verification_status')
