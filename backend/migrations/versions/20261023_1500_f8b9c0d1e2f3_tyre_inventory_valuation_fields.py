"""tyre_inventory_valuation_fields

Revision ID: f8b9c0d1e2f3
Revises: e7a8b9c0d1e2
Create Date: 2026-10-23 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8b9c0d1e2f3'
down_revision: Union[str, None] = 'e7a8b9c0d1e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    existing_cols = {col["name"] for col in insp.get_columns("tyres")}

    # 1. Add purchase_cost (known acquisition cost)
    if "purchase_cost" not in existing_cols:
        op.add_column("tyres", sa.Column("purchase_cost", sa.Float(), nullable=True))

    # 2. Add purchase_date (procurement date)
    if "purchase_date" not in existing_cols:
        op.add_column("tyres", sa.Column("purchase_date", sa.DateTime(timezone=True), nullable=True))

    # 3. Add purchase_currency (ISO currency code, defaults to INR)
    if "purchase_currency" not in existing_cols:
        op.add_column("tyres", sa.Column("purchase_currency", sa.String(length=3), server_default="INR", nullable=False))

    # 4. Add purchase_invoice (invoice or receipt reference)
    if "purchase_invoice" not in existing_cols:
        op.add_column("tyres", sa.Column("purchase_invoice", sa.String(length=255), nullable=True))

    # 5. Add purchase_vendor (supplier / vendor)
    if "purchase_vendor" not in existing_cols:
        op.add_column("tyres", sa.Column("purchase_vendor", sa.String(length=255), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    existing_cols = {col["name"] for col in insp.get_columns("tyres")}

    if "purchase_vendor" in existing_cols:
        op.drop_column("tyres", "purchase_vendor")
    if "purchase_invoice" in existing_cols:
        op.drop_column("tyres", "purchase_invoice")
    if "purchase_currency" in existing_cols:
        op.drop_column("tyres", "purchase_currency")
    if "purchase_date" in existing_cols:
        op.drop_column("tyres", "purchase_date")
    if "purchase_cost" in existing_cols:
        op.drop_column("tyres", "purchase_cost")
