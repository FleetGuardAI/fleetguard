"""driver_qualifications_and_cargo_capabilities

Revision ID: a1c2e3g4i5k6
Revises: f8b9c0d1e2f3
Create Date: 2026-10-23 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c2e3g4i5k6'
down_revision: Union[str, None] = 'f8b9c0d1e2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    target_schema = op.get_context().version_table_schema
    existing_tables = set(insp.get_table_names(schema=target_schema))

    # 1. Create driver_qualifications table
    if "driver_qualifications" not in existing_tables:
        op.create_table(
            "driver_qualifications",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("driver_id", sa.Integer(), sa.ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True),
            sa.Column("qualification_type", sa.String(length=50), nullable=False, default="DRIVING_LICENSE", index=True),
            sa.Column("license_class", sa.String(length=50), nullable=True, index=True),
            sa.Column("certificate_number", sa.String(length=100), nullable=False, index=True),
            sa.Column("issuing_authority", sa.String(length=150), nullable=True),
            sa.Column("issue_date", sa.Date(), nullable=True),
            sa.Column("expiry_date", sa.Date(), nullable=True, index=True),
            sa.Column("verification_status", sa.String(length=50), nullable=False, default="PENDING", index=True),
            sa.Column("verified_by", sa.String(length=255), nullable=True),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("rejection_reason", sa.String(length=500), nullable=True),
            sa.Column("evidence_url", sa.String(length=500), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )

    # 2. Add vehicle capability columns
    if "vehicles" in existing_tables:
        vehicle_cols = {col["name"] for col in insp.get_columns("vehicles", schema=target_schema)}
        if "vehicle_class" not in vehicle_cols:
            op.add_column("vehicles", sa.Column("vehicle_class", sa.String(length=50), nullable=True))
        if "payload_capacity_tonnes" not in vehicle_cols:
            op.add_column("vehicles", sa.Column("payload_capacity_tonnes", sa.Float(), nullable=True))
        if "gross_vehicle_weight_tonnes" not in vehicle_cols:
            op.add_column("vehicles", sa.Column("gross_vehicle_weight_tonnes", sa.Float(), nullable=True))
        if "supported_cargo_categories" not in vehicle_cols:
            op.add_column("vehicles", sa.Column("supported_cargo_categories", sa.JSON(), nullable=True))
        if "body_type" not in vehicle_cols:
            op.add_column("vehicles", sa.Column("body_type", sa.String(length=50), nullable=True))
        if "temperature_controlled" not in vehicle_cols:
            op.add_column("vehicles", sa.Column("temperature_controlled", sa.Boolean(), server_default="0", nullable=False))
        if "hazardous_certified" not in vehicle_cols:
            op.add_column("vehicles", sa.Column("hazardous_certified", sa.Boolean(), server_default="0", nullable=False))

    # 3. Add trip cargo requirement columns
    if "trips" in existing_tables:
        trip_cols = {col["name"] for col in insp.get_columns("trips", schema=target_schema)}
        if "cargo_category" not in trip_cols:
            op.add_column("trips", sa.Column("cargo_category", sa.String(length=50), server_default="GENERAL", nullable=True))
        if "required_vehicle_class" not in trip_cols:
            op.add_column("trips", sa.Column("required_vehicle_class", sa.String(length=50), nullable=True))
        if "required_driver_qualification" not in trip_cols:
            op.add_column("trips", sa.Column("required_driver_qualification", sa.String(length=50), nullable=True))
        if "cargo_temperature_required" not in trip_cols:
            op.add_column("trips", sa.Column("cargo_temperature_required", sa.Boolean(), server_default="0", nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    target_schema = op.get_context().version_table_schema
    existing_tables = set(insp.get_table_names(schema=target_schema))

    if "trips" in existing_tables:
        trip_cols = {col["name"] for col in insp.get_columns("trips", schema=target_schema)}
        for col_name in ["cargo_temperature_required", "required_driver_qualification", "required_vehicle_class", "cargo_category"]:
            if col_name in trip_cols:
                op.drop_column("trips", col_name)

    if "vehicles" in existing_tables:
        vehicle_cols = {col["name"] for col in insp.get_columns("vehicles", schema=target_schema)}
        for col_name in ["hazardous_certified", "temperature_controlled", "body_type", "supported_cargo_categories", "gross_vehicle_weight_tonnes", "payload_capacity_tonnes", "vehicle_class"]:
            if col_name in vehicle_cols:
                op.drop_column("vehicles", col_name)

    if "driver_qualifications" in existing_tables:
        op.drop_table("driver_qualifications")
