"""tyre_domain_hardening

Revision ID: e7a8b9c0d1e2
Revises: 8debfb47da0c
Create Date: 2026-10-22 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7a8b9c0d1e2'
down_revision: Union[str, None] = '8debfb47da0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Helper to check if column exists
    def column_exists(table: str, column: str) -> bool:
        res = conn.execute(sa.text(
            f"SELECT column_name FROM information_schema.columns "
            f"WHERE table_name = '{table}' AND column_name = '{column}'"
        ))
        return res.fetchone() is not None

    # 1. Add company_id to tyres
    if not column_exists('tyres', 'company_id'):
        op.add_column('tyres', sa.Column('company_id', sa.Integer(), server_default='1', nullable=False))
        op.create_index(op.f('ix_tyres_company_id'), 'tyres', ['company_id'], unique=False)

    # 2. Add retread_count to tyres
    if not column_exists('tyres', 'retread_count'):
        op.add_column('tyres', sa.Column('retread_count', sa.Integer(), server_default='0', nullable=False))

    # 3. Add total_lifetime_km to tyres
    if not column_exists('tyres', 'total_lifetime_km'):
        op.add_column('tyres', sa.Column('total_lifetime_km', sa.Float(), server_default='0.0', nullable=False))

    # 4. Add current_retread_km to tyres
    if not column_exists('tyres', 'current_retread_km'):
        op.add_column('tyres', sa.Column('current_retread_km', sa.Float(), server_default='0.0', nullable=False))

    # 5. Add current_installation_odometer to tyres
    if not column_exists('tyres', 'current_installation_odometer'):
        op.add_column('tyres', sa.Column('current_installation_odometer', sa.Float(), nullable=True))

    # 6. Add current_tread_depth_mm to tyres
    if not column_exists('tyres', 'current_tread_depth_mm'):
        op.add_column('tyres', sa.Column('current_tread_depth_mm', sa.Float(), nullable=True))

    # 7. Add company_id to tyre_lifecycle_records
    if not column_exists('tyre_lifecycle_records', 'company_id'):
        op.add_column('tyre_lifecycle_records', sa.Column('company_id', sa.Integer(), nullable=True))
        op.create_index(op.f('ix_tyre_lifecycle_records_company_id'), 'tyre_lifecycle_records', ['company_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tyre_lifecycle_records_company_id'), table_name='tyre_lifecycle_records')
    op.drop_column('tyre_lifecycle_records', 'company_id')

    op.drop_column('tyres', 'current_tread_depth_mm')
    op.drop_column('tyres', 'current_installation_odometer')
    op.drop_column('tyres', 'current_retread_km')
    op.drop_column('tyres', 'total_lifetime_km')
    op.drop_column('tyres', 'retread_count')
    op.drop_index(op.f('ix_tyres_company_id'), table_name='tyres')
    op.drop_column('tyres', 'company_id')
