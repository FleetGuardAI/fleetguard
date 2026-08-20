"""add generic financial fields

Revision ID: 123abc456def
Revises: 9dae99ddd519
Create Date: 2026-08-19 14:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '123abc456def'
down_revision = '9dae99ddd519'
branch_labels = None
depends_on = None

def upgrade():
    # We use sa.JSON to ensure SQLite tests continue to work while Postgres gets a JSON type
    # For postgres, JSONB is specified using JSON().with_variant(JSONB, 'postgresql') in the model
    # Here in alembic we can specify postgresql.JSONB for the postgres side.
    
    op.add_column('fuel_financial_impacts', sa.Column('baseline_value', sa.Float(), nullable=True))
    op.add_column('fuel_financial_impacts', sa.Column('observed_value', sa.Float(), nullable=True))
    op.add_column('fuel_financial_impacts', sa.Column('domain_context', sa.JSON().with_variant(postgresql.JSONB, 'postgresql'), nullable=True))


def downgrade():
    op.drop_column('fuel_financial_impacts', 'domain_context')
    op.drop_column('fuel_financial_impacts', 'observed_value')
    op.drop_column('fuel_financial_impacts', 'baseline_value')
