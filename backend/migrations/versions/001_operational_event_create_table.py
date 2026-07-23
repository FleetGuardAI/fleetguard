"""
FleetGuard — Alembic Migration
Revision  : 001
Created   : 2026-07-14
Feature   : Operational Event Store — Initial table creation

Creates the `operational_events` table as part of FleetGuard's
Event-Driven Architecture foundation.

PostgreSQL types used
---------------------
• UUID                          — primary key (uuid-ossp extension or gen_random_uuid())
• TIMESTAMP WITH TIME ZONE      — occurred_at, recorded_at, created_at, updated_at
• JSONB                         — payload, event_metadata (indexed, queryable)
• Native ENUM types             — event_type, entity_type, capture_method,
                                  verification_status

Indexes created
---------------
• ix_operational_events_id              — PK (implicit)
• ix_operational_events_event_type      — filter by event type
• ix_operational_events_entity_type     — filter by entity domain
• ix_operational_events_entity_id       — filter by specific entity
• ix_operational_events_occurred_at     — time-range queries
• ix_operational_events_verification_status — filter pending/disputed events
• ix_operational_events_created_at      — audit / chronological queries
• ix_operational_events_entity          — composite (entity_type, entity_id)
                                          for "all events for vehicle X" queries

Rollback
--------
Drops all indexes, the table, and the four enum types — in reverse order.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from alembic import op

# ---------------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------------
revision: str = "001_operational_event"
down_revision: str | None = None   # First migration — no parent
branch_labels: str | None = None
depends_on: str | None = None


# ---------------------------------------------------------------------------
# Enum type definitions
# These are created as NAMED TYPES in the PostgreSQL schema so they can be
# reused across tables in future milestones.
# ---------------------------------------------------------------------------

_event_type_enum = sa.Enum(
    "FUEL_FILLED",
    "FUEL_ALERT_TRIGGERED",
    "TRIP_STARTED",
    "TRIP_ENDED",
    "TRIP_PAUSED",
    "TRIP_RESUMED",
    "VEHICLE_ASSIGNED",
    "VEHICLE_UNASSIGNED",
    "VEHICLE_STATUS_CHANGED",
    "DRIVER_ASSIGNED",
    "DRIVER_UNASSIGNED",
    "DRIVER_STATUS_CHANGED",
    "MAINTENANCE_COMPLETED",
    "MAINTENANCE_SCHEDULED",
    "MAINTENANCE_OVERDUE",
    "TYRE_REPLACED",
    "TYRE_PRESSURE_ALERT",
    "EXPENSE_ADDED",
    "EXPENSE_APPROVED",
    "EXPENSE_REJECTED",
    "INSURANCE_EXPIRY_ALERT",
    "PERMIT_EXPIRY_ALERT",
    "DOCUMENT_UPLOADED",
    "SYSTEM_SYNC",
    name="event_type",
    create_type=False,   # We CREATE it manually below for clarity
)

_entity_type_enum = sa.Enum(
    "VEHICLE",
    "DRIVER",
    "TRIP",
    "ROUTE",
    "EXPENSE",
    "MAINTENANCE",
    "TYRE",
    "DOCUMENT",
    "SYSTEM",
    name="entity_type",
    create_type=False,
)

_capture_method_enum = sa.Enum(
    "WHATSAPP_BOT",
    "TELEMATICS",
    "MANUAL_ENTRY",
    "API_INTEGRATION",
    "SYSTEM_GENERATED",
    name="capture_method",
    create_type=False,
)

_verification_status_enum = sa.Enum(
    "PENDING",
    "VERIFIED",
    "DISPUTED",
    "REJECTED",
    name="verification_status",
    create_type=False,
)


# ---------------------------------------------------------------------------
# Upgrade
# ---------------------------------------------------------------------------

def upgrade() -> None:
    """
    Create the operational_events table and all supporting types/indexes.

    Order:
        1. Create ENUM types (must exist before the table references them)
        2. Create the table
        3. Create non-PK indexes
    """

    # 1. Create PostgreSQL ENUM types
    #    Using raw SQL gives us full control and avoids dialect detection issues.
    op.execute("""
        CREATE TYPE event_type AS ENUM (
            'FUEL_FILLED',
            'FUEL_ALERT_TRIGGERED',
            'TRIP_STARTED',
            'TRIP_ENDED',
            'TRIP_PAUSED',
            'TRIP_RESUMED',
            'VEHICLE_ASSIGNED',
            'VEHICLE_UNASSIGNED',
            'VEHICLE_STATUS_CHANGED',
            'DRIVER_ASSIGNED',
            'DRIVER_UNASSIGNED',
            'DRIVER_STATUS_CHANGED',
            'MAINTENANCE_COMPLETED',
            'MAINTENANCE_SCHEDULED',
            'MAINTENANCE_OVERDUE',
            'TYRE_REPLACED',
            'TYRE_PRESSURE_ALERT',
            'EXPENSE_ADDED',
            'EXPENSE_APPROVED',
            'EXPENSE_REJECTED',
            'INSURANCE_EXPIRY_ALERT',
            'PERMIT_EXPIRY_ALERT',
            'DOCUMENT_UPLOADED',
            'SYSTEM_SYNC'
        )
    """)

    op.execute("""
        CREATE TYPE entity_type AS ENUM (
            'VEHICLE',
            'DRIVER',
            'TRIP',
            'ROUTE',
            'EXPENSE',
            'MAINTENANCE',
            'TYRE',
            'DOCUMENT',
            'SYSTEM'
        )
    """)

    op.execute("""
        CREATE TYPE capture_method AS ENUM (
            'WHATSAPP_BOT',
            'TELEMATICS',
            'MANUAL_ENTRY',
            'API_INTEGRATION',
            'SYSTEM_GENERATED'
        )
    """)

    op.execute("""
        CREATE TYPE verification_status AS ENUM (
            'PENDING',
            'VERIFIED',
            'DISPUTED',
            'REJECTED'
        )
    """)

    # 2. Create the table
    op.create_table(
        "operational_events",

        # --- Primary Key ---
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
            comment="Globally unique event identifier (UUID v4).",
        ),

        # --- Event Classification ---
        sa.Column(
            "event_type",
            sa.Enum(name="event_type", create_type=False),
            nullable=False,
            comment="What happened — drives processing logic in downstream consumers.",
        ),
        sa.Column(
            "entity_type",
            sa.Enum(name="entity_type", create_type=False),
            nullable=False,
            comment="The primary fleet entity domain this event concerns.",
        ),
        sa.Column(
            "entity_id",
            sa.String(255),
            nullable=False,
            comment=(
                "Identifier of the specific entity (vehicle plate, driver UUID, etc.). "
                "String type to accommodate heterogeneous entity key formats."
            ),
        ),

        # --- Temporal ---
        sa.Column(
            "occurred_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            comment=(
                "Wall-clock time when the event occurred in the physical world. "
                "For offline-captured events this precedes recorded_at."
            ),
        ),
        sa.Column(
            "recorded_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="UTC timestamp when this event was received and stored by the platform.",
        ),

        # --- Capture & Verification ---
        sa.Column(
            "capture_method",
            sa.Enum(name="capture_method", create_type=False),
            nullable=False,
            comment="Channel through which this event entered the system.",
        ),
        sa.Column(
            "verification_status",
            sa.Enum(name="verification_status", create_type=False),
            nullable=False,
            server_default="PENDING",
            comment="Validation lifecycle state — updated by the Validation & Enrichment Engine.",
        ),

        # --- Actor ---
        sa.Column(
            "created_by",
            sa.String(255),
            nullable=True,
            comment=(
                "ID of the user or system service that submitted this event. "
                "NULL for fully automated / system-generated events."
            ),
        ),

        # --- Schemaless Payloads (JSONB for PostgreSQL indexing) ---
        sa.Column(
            "payload",
            JSONB,
            nullable=True,
            comment=(
                "Event-specific data bag. Schema is owned by the producing service "
                "and documented in the Event Catalogue."
            ),
        ),
        sa.Column(
            "event_metadata",
            JSONB,
            nullable=True,
            comment=(
                "Operational metadata: source IP, device ID, app version, "
                "correlation IDs, retry counts. Not business data."
            ),
        ),

        # --- Annotation ---
        sa.Column(
            "notes",
            sa.Text,
            nullable=True,
            comment="Free-text annotation added by a fleet manager during review.",
        ),

        # --- Audit Timestamps ---
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="Row insert timestamp — managed by the database.",
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="Row last-modified timestamp — managed by the database.",
        ),
    )

    # 3. Create non-PK indexes
    #    The PK column (id) is already indexed implicitly by PostgreSQL.

    op.create_index(
        "ix_operational_events_event_type",
        "operational_events",
        ["event_type"],
    )
    op.create_index(
        "ix_operational_events_entity_type",
        "operational_events",
        ["entity_type"],
    )
    op.create_index(
        "ix_operational_events_entity_id",
        "operational_events",
        ["entity_id"],
    )
    op.create_index(
        "ix_operational_events_occurred_at",
        "operational_events",
        ["occurred_at"],
    )
    op.create_index(
        "ix_operational_events_verification_status",
        "operational_events",
        ["verification_status"],
    )
    op.create_index(
        "ix_operational_events_created_at",
        "operational_events",
        ["created_at"],
    )

    # Composite index: supports "all events for entity X of type Y" queries
    # Example query: WHERE entity_type = 'VEHICLE' AND entity_id = 'MH12AB1234'
    op.create_index(
        "ix_operational_events_entity",
        "operational_events",
        ["entity_type", "entity_id"],
    )


# ---------------------------------------------------------------------------
# Downgrade
# ---------------------------------------------------------------------------

def downgrade() -> None:
    """
    Drop all indexes, the table, and the enum types — in reverse order.

    ENUM types must be dropped AFTER the table that references them.
    """

    # 1. Drop indexes (before the table)
    op.drop_index("ix_operational_events_entity",              table_name="operational_events")
    op.drop_index("ix_operational_events_created_at",          table_name="operational_events")
    op.drop_index("ix_operational_events_verification_status", table_name="operational_events")
    op.drop_index("ix_operational_events_occurred_at",         table_name="operational_events")
    op.drop_index("ix_operational_events_entity_id",           table_name="operational_events")
    op.drop_index("ix_operational_events_entity_type",         table_name="operational_events")
    op.drop_index("ix_operational_events_event_type",          table_name="operational_events")

    # 2. Drop the table
    op.drop_table("operational_events")

    # 3. Drop enum types (must come after the table is gone)
    op.execute("DROP TYPE IF EXISTS verification_status")
    op.execute("DROP TYPE IF EXISTS capture_method")
    op.execute("DROP TYPE IF EXISTS entity_type")
    op.execute("DROP TYPE IF EXISTS event_type")
