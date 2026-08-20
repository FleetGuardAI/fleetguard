"""add_missing_trip_columns

Revision ID: d4e5f6g7h8i9
Revises: c3d4e5f6g7h8
Create Date: 2026-08-20 17:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6g7h8i9'
down_revision: Union[str, None] = 'c3d4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('trips') as batch_op:
        # Add new columns
        batch_op.add_column(sa.Column('company_id', sa.Integer(), nullable=True))
        
        batch_op.add_column(sa.Column('revenue', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('planned_cost', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('planned_fuel_liters', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('cargo_weight', sa.Float(), nullable=True))
        
    # Set existing company_id to 1 (legacy company fallback) then add constraints
    op.execute("UPDATE trips SET company_id = 1 WHERE company_id IS NULL")
    
    with op.batch_alter_table('trips') as batch_op:
        batch_op.alter_column('company_id', nullable=False)
        batch_op.create_foreign_key('fk_trips_companies_id', 'companies', ['company_id'], ['id'])
        batch_op.create_index('ix_trips_company_id', ['company_id'])
        
        # Also need to fix the status column which might be native_enum=False in ORM
        # Actually it's already a String in the DB (length=20)


def downgrade() -> None:
    with op.batch_alter_table('trips') as batch_op:
        batch_op.drop_index('ix_trips_company_id')
        batch_op.drop_constraint('fk_trips_companies_id', type_='foreignkey')
        batch_op.drop_column('cargo_weight')
        batch_op.drop_column('planned_fuel_liters')
        batch_op.drop_column('planned_cost')
        batch_op.drop_column('revenue')
        batch_op.drop_column('company_id')
