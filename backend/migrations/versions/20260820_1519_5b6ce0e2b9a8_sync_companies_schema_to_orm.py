"""Sync companies schema to ORM

Revision ID: 5b6ce0e2b9a8
Revises: dcff6780ab29
Create Date: 2026-08-20 15:19:23.363997

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5b6ce0e2b9a8'
down_revision: Union[str, None] = 'dcff6780ab29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename name to company_name
    op.alter_column('companies', 'name', new_column_name='company_name')
    # Add missing columns
    op.add_column('companies', sa.Column('owner_name', sa.String(length=255), nullable=True))
    op.add_column('companies', sa.Column('mobile_number', sa.String(length=20), nullable=True))
    op.add_column('companies', sa.Column('email', sa.String(length=255), nullable=True))
    op.add_column('companies', sa.Column('status', sa.String(length=50), server_default=sa.text("'ACTIVE'"), nullable=True))
    op.add_column('companies', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('companies', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True))

def downgrade() -> None:
    op.drop_column('companies', 'updated_at')
    op.drop_column('companies', 'created_at')
    op.drop_column('companies', 'status')
    op.drop_column('companies', 'email')
    op.drop_column('companies', 'mobile_number')
    op.drop_column('companies', 'owner_name')
    op.alter_column('companies', 'company_name', new_column_name='name')
