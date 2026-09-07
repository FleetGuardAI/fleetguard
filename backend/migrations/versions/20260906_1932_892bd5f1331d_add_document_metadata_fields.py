"""add_document_metadata_fields

Revision ID: 892bd5f1331d
Revises: 3a4b5c6d7e8f
Create Date: 2026-09-06 19:32:39.729742

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '892bd5f1331d'
down_revision: Union[str, None] = '3a4b5c6d7e8f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('documents', sa.Column('name', sa.String(length=255), nullable=True))
    op.add_column('documents', sa.Column('category', sa.String(length=100), nullable=True))
    op.add_column('documents', sa.Column('expiry_date', sa.String(length=50), nullable=True))
    op.add_column('documents', sa.Column('target_id', sa.String(length=100), nullable=True))
    op.add_column('documents', sa.Column('target_type', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_documents_target_id'), 'documents', ['target_id'], unique=False)
    op.create_index(op.f('ix_documents_target_type'), 'documents', ['target_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_documents_target_type'), table_name='documents')
    op.drop_index(op.f('ix_documents_target_id'), table_name='documents')
    op.drop_column('documents', 'target_type')
    op.drop_column('documents', 'target_id')
    op.drop_column('documents', 'expiry_date')
    op.drop_column('documents', 'category')
    op.drop_column('documents', 'name')
