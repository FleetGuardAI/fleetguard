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
    conn = op.get_bind()
    
    # 1. Add company_id to expenses (idempotent)
    result = conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'expenses' AND column_name = 'company_id'"
    ))
    if result.fetchone() is None:
        op.add_column('expenses', sa.Column('company_id', sa.Integer(), nullable=True))
        op.create_index(op.f('ix_expenses_company_id'), 'expenses', ['company_id'], unique=False)
    
    # 2. Make users.email nullable (idempotent)
    result = conn.execute(sa.text(
        "SELECT is_nullable FROM information_schema.columns "
        "WHERE table_name = 'users' AND column_name = 'email'"
    ))
    row = result.fetchone()
    if row and row[0] == 'NO':
        op.alter_column('users', 'email',
                   existing_type=sa.VARCHAR(length=255),
                   nullable=True)
               
    # 3. Drop unique constraint on users.email if it exists (idempotent)
    result = conn.execute(sa.text(
        "SELECT constraint_name FROM information_schema.table_constraints "
        "WHERE table_name = 'users' AND constraint_name = 'users_email_key'"
    ))
    if result.fetchone() is not None:
        op.drop_constraint('users_email_key', 'users', type_='unique')

def downgrade() -> None:
    # Intentionally minimal — these are one-way schema fixes
    pass
