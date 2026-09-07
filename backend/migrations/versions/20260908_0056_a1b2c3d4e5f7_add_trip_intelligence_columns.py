"""add_trip_intelligence_columns

Revision ID: a1b2c3d4e5f7
Revises: d56fa17ce72e
Create Date: 2026-09-08 00:56:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, None] = 'd56fa17ce72e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Queryable intelligence fields ---
    op.add_column('trips', sa.Column(
        'expected_revenue', sa.Float(), nullable=True,
        comment='Expected revenue at time of intelligence evaluation'))
    op.add_column('trips', sa.Column(
        'expected_cost', sa.Float(), nullable=True,
        comment='Expected total cost at time of intelligence evaluation'))
    op.add_column('trips', sa.Column(
        'expected_profit', sa.Float(), nullable=True,
        comment='Expected profit at time of intelligence evaluation'))
    op.add_column('trips', sa.Column(
        'expected_margin', sa.Float(), nullable=True,
        comment='Expected profit margin percentage at dispatch'))
    op.add_column('trips', sa.Column(
        'recommendation_decision', sa.String(20), nullable=True,
        comment='TAKE, REVIEW, or AVOID'))
    op.add_column('trips', sa.Column(
        'recommendation_at', sa.DateTime(timezone=True), nullable=True,
        comment='When the intelligence evaluation was computed'))
    op.add_column('trips', sa.Column(
        'intelligence_version', sa.String(50), nullable=True,
        server_default='trip-intelligence-v1',
        comment='Version of the calculation engine that produced this prediction'))
    op.add_column('trips', sa.Column(
        'confidence_level', sa.String(20), nullable=True,
        comment='HIGH, MEDIUM, LOW, INSUFFICIENT'))
    op.add_column('trips', sa.Column(
        'risk_level', sa.String(20), nullable=True,
        comment='LOW, MEDIUM, HIGH'))
    op.add_column('trips', sa.Column(
        'recommendation_outcome', sa.String(30), nullable=True,
        comment='OUTPERFORMED, MET_EXPECTATION, UNDERPERFORMED, LOSS, INSUFFICIENT_DATA'))

    # --- Immutable JSONB snapshot ---
    op.add_column('trips', sa.Column(
        'intelligence_snapshot', JSONB(), nullable=True,
        comment='Immutable pre-trip intelligence calculation preserved at dispatch'))

    # --- Indexes for analytics / reporting ---
    op.create_index('ix_trips_recommendation_decision', 'trips', ['recommendation_decision'])
    op.create_index('ix_trips_confidence_level', 'trips', ['confidence_level'])
    op.create_index('ix_trips_risk_level', 'trips', ['risk_level'])


def downgrade() -> None:
    op.drop_index('ix_trips_risk_level', table_name='trips')
    op.drop_index('ix_trips_confidence_level', table_name='trips')
    op.drop_index('ix_trips_recommendation_decision', table_name='trips')

    op.drop_column('trips', 'intelligence_snapshot')
    op.drop_column('trips', 'recommendation_outcome')
    op.drop_column('trips', 'risk_level')
    op.drop_column('trips', 'confidence_level')
    op.drop_column('trips', 'intelligence_version')
    op.drop_column('trips', 'recommendation_at')
    op.drop_column('trips', 'recommendation_decision')
    op.drop_column('trips', 'expected_margin')
    op.drop_column('trips', 'expected_profit')
    op.drop_column('trips', 'expected_cost')
    op.drop_column('trips', 'expected_revenue')
