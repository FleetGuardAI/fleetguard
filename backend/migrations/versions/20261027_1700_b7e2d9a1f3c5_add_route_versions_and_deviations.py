"""add_route_versions_and_deviations

Revision ID: b7e2d9a1f3c5
Revises: 5df0285937a9
Create Date: 2026-10-27 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e2d9a1f3c5'
down_revision: Union[str, None] = '5df0285937a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    target_schema = op.get_context().version_table_schema
    existing_tables = set(insp.get_table_names(schema=target_schema))

    # 1. Create route_versions table
    if "route_versions" not in existing_tables:
        op.create_table(
            "route_versions",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("version_number", sa.Integer(), nullable=False, default=1),
            sa.Column("route_type", sa.String(length=50), nullable=False, default="RECOMMENDED"),
            sa.Column("status", sa.String(length=50), nullable=False, default="PLANNED", index=True),
            sa.Column("origin_lat", sa.Float(), nullable=False),
            sa.Column("origin_lng", sa.Float(), nullable=False),
            sa.Column("origin_address", sa.String(length=500), nullable=True),
            sa.Column("destination_lat", sa.Float(), nullable=False),
            sa.Column("destination_lng", sa.Float(), nullable=False),
            sa.Column("destination_address", sa.String(length=500), nullable=True),
            sa.Column("polyline", sa.Text(), nullable=False),
            sa.Column("distance_km", sa.Float(), nullable=False),
            sa.Column("duration_hours", sa.Float(), nullable=False),
            sa.Column("duration_seconds", sa.Integer(), nullable=True),
            sa.Column("fuel_liters_estimate", sa.Float(), nullable=True),
            sa.Column("fuel_cost_estimate", sa.Float(), nullable=True),
            sa.Column("toll_cost_estimate", sa.Float(), nullable=True),
            sa.Column("total_cost_estimate", sa.Float(), nullable=True),
            sa.Column("currency", sa.String(length=10), nullable=False, default="INR"),
            sa.Column("vehicle_mileage_used", sa.Float(), nullable=True),
            sa.Column("fuel_price_used", sa.Float(), nullable=True),
            sa.Column("routing_provider", sa.String(length=50), nullable=False, default="google"),
            sa.Column("selection_reason", sa.String(length=500), nullable=True),
            sa.Column("reason_for_change", sa.String(length=500), nullable=True),
            sa.Column("approved_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_route_versions_trip_v", "route_versions", ["trip_id", "version_number"])
        op.create_index("ix_route_versions_company", "route_versions", ["company_id"])

    # 2. Create route_deviation_events table
    if "route_deviation_events" not in existing_tables:
        op.create_table(
            "route_deviation_events",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("event_id", sa.String(length=100), unique=True, index=True, nullable=False),
            sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("driver_id", sa.Integer(), sa.ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("vehicle_id", sa.Integer(), sa.ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("route_version_id", sa.Integer(), sa.ForeignKey("route_versions.id", ondelete="SET NULL"), nullable=True, index=True),
            sa.Column("status", sa.String(length=50), nullable=False, default="SUSPECTED", index=True),
            sa.Column("severity", sa.String(length=20), nullable=False, default="MEDIUM"),
            sa.Column("distance_from_route_meters", sa.Float(), nullable=False),
            sa.Column("max_distance_meters", sa.Float(), nullable=False),
            sa.Column("last_latitude", sa.Float(), nullable=False),
            sa.Column("last_longitude", sa.Float(), nullable=False),
            sa.Column("gps_accuracy", sa.Float(), nullable=True),
            sa.Column("consecutive_outliers", sa.Integer(), nullable=False, default=1),
            sa.Column("first_detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("last_detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("driver_explanation_category", sa.String(length=50), nullable=True),
            sa.Column("driver_explanation_notes", sa.Text(), nullable=True),
            sa.Column("driver_reported_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("manager_notes", sa.Text(), nullable=True),
            sa.Column("acknowledged_by_user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_dev_events_company_status", "route_deviation_events", ["company_id", "status"])
        op.create_index("ix_dev_events_trip_status", "route_deviation_events", ["trip_id", "status"])

    # 3. Add approved_route_version_id and route_status to trips table
    if "trips" in existing_tables:
        trip_cols = {col["name"] for col in insp.get_columns("trips", schema=target_schema)}
        if "approved_route_version_id" not in trip_cols:
            op.add_column("trips", sa.Column("approved_route_version_id", sa.Integer(), sa.ForeignKey("route_versions.id", ondelete="SET NULL"), nullable=True))
            op.create_index("ix_trips_approved_route_v", "trips", ["approved_route_version_id"])
        if "route_status" not in trip_cols:
            op.add_column("trips", sa.Column("route_status", sa.String(length=50), nullable=True, server_default="PENDING"))


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    target_schema = op.get_context().version_table_schema
    existing_tables = set(insp.get_table_names(schema=target_schema))

    if "trips" in existing_tables:
        trip_cols = {col["name"] for col in insp.get_columns("trips", schema=target_schema)}
        if "approved_route_version_id" in trip_cols:
            op.drop_column("trips", "approved_route_version_id")
        if "route_status" in trip_cols:
            op.drop_column("trips", "route_status")

    if "route_deviation_events" in existing_tables:
        op.drop_table("route_deviation_events")

    if "route_versions" in existing_tables:
        op.drop_table("route_versions")

