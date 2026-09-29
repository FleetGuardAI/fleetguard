"""Add receiver information to trips

Revision ID: b35f21696b99
Revises: 06066f5b0549
Create Date: 2026-09-29 10:00:00

"""
from alembic import op
import sqlalchemy as sa

revision = 'b35f21696b99'
down_revision = '06066f5b0549'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('trips', sa.Column('receiver_name', sa.String(length=255), nullable=True))
    op.add_column('trips', sa.Column('receiver_phone', sa.String(length=50), nullable=True))
    op.add_column('trips', sa.Column('receiver_company', sa.String(length=255), nullable=True))
    op.add_column('trips', sa.Column('receiver_address', sa.Text(), nullable=True))
    op.add_column('trips', sa.Column('receiver_city', sa.String(length=100), nullable=True))
    op.add_column('trips', sa.Column('receiver_state', sa.String(length=100), nullable=True))
    op.add_column('trips', sa.Column('receiver_pincode', sa.String(length=20), nullable=True))
    op.add_column('trips', sa.Column('receiver_notes', sa.Text(), nullable=True))

def downgrade():
    op.drop_column('trips', 'receiver_notes')
    op.drop_column('trips', 'receiver_pincode')
    op.drop_column('trips', 'receiver_state')
    op.drop_column('trips', 'receiver_city')
    op.drop_column('trips', 'receiver_address')
    op.drop_column('trips', 'receiver_company')
    op.drop_column('trips', 'receiver_phone')
    op.drop_column('trips', 'receiver_name')
