"""add company_id to expenses

Revision ID: c121c0718965
Revises: 989d835589c7
Create Date: 2026-08-25 01:48:54.526368

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c121c0718965'
down_revision: Union[str, None] = '989d835589c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Safely add column if it doesn't exist
    conn = op.get_bind()
    
    # 1. Add company_id to expenses
    op.add_column('expenses', sa.Column('company_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_expenses_company_id'), 'expenses', ['company_id'], unique=False)
    
    # 2. Make users.email nullable
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)
               
    try:
        op.drop_constraint('users_email_key', 'users', type_='unique')
    except Exception:
        pass

def downgrade() -> None:
    pass
