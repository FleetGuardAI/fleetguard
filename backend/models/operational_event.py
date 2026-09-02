"""
FleetGuard — Operational Event ORM Model

An Operational Event is an immutable record of something that happened
inside the fleet.  It is the single source of truth in FleetGuard's
Event-Driven Architecture.

Events are produced by every operational module (WhatsApp bot, telematics,
driver app, manual entry) and consumed by:

  Capture Layer
  ↓  Validation & Enrichment Engine
  ↓  Operational Event Store  ← this model
  ↓  Event Processor
  ↓  Fleet Memory
  ↓  Fleet Intelligence Engine

Design principles
-----------------
• Immutable at the business level — status transitions happen via new events,
  not in-place mutations.
• Schemaless payload (JSON) — different event types carry different data
  without requiring schema migrations for each new field.
• Fully tenant-aware via entity_id / created_by references.
• UUID primary key — safe for distributed capture across multiple services.

NOTE on JSONB vs JSON
---------------------
SQLAlchemy's JSON column maps to JSONB on PostgreSQL (the target production
database) and to TEXT-backed JSON on SQLite (current dev database).
When migrating to PostgreSQL, Alembic will handle the column type upgrade.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any, Optional

import sqlalchemy as sa
from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from database import Base


# ===========================================================================
# Enumerations
# ===========================================================================

class EventType(str, enum.Enum):
    """
    Catalogue of every recognised operational event type in FleetGuard.

    Naming convention: <DOMAIN>_<VERB> in SCREAMING_SNAKE_CASE.

    Extend this enum as new business processes are onboarded.
    Do NOT remove or rename existing values — that would break replayed
    event streams.
    """

    # --- Fuel ---
    FUEL_FILLED = "FUEL_FILLED"
    FUEL_DRAINED = "FUEL_DRAINED"
    FUEL_ALERT_TRIGGERED = "FUEL_ALERT_TRIGGERED"

    # --- Telematics ---
    POSITION_RECORDED = "POSITION_RECORDED"
    IGNITION_STARTED = "IGNITION_STARTED"
    IGNITION_STOPPED = "IGNITION_STOPPED"

    # --- Trip ---
    TRIP_CREATED = "TRIP_CREATED"
    TRIP_STARTED = "TRIP_STARTED"
    TRIP_PAUSED = "TRIP_PAUSED"
    TRIP_RESUMED = "TRIP_RESUMED"
    TRIP_COMPLETED = "TRIP_COMPLETED"
    TRIP_CANCELLED = "TRIP_CANCELLED"
    TRIP_DRIVER_ASSIGNED = "TRIP_DRIVER_ASSIGNED"
    TRIP_VEHICLE_ASSIGNED = "TRIP_VEHICLE_ASSIGNED"

    # --- Vehicle ---
    VEHICLE_REGISTERED = "VEHICLE_REGISTERED"
    VEHICLE_ASSIGNED = "VEHICLE_ASSIGNED"
    VEHICLE_UNASSIGNED = "VEHICLE_UNASSIGNED"
    VEHICLE_STATUS_CHANGED = "VEHICLE_STATUS_CHANGED"

    # --- Driver ---
    DRIVER_REGISTERED = "DRIVER_REGISTERED"
    DRIVER_ASSIGNED = "DRIVER_ASSIGNED"
    DRIVER_UNASSIGNED = "DRIVER_UNASSIGNED"
    DRIVER_STATUS_CHANGED = "DRIVER_STATUS_CHANGED"

    # --- Maintenance ---
    MAINTENANCE_CREATED = "MAINTENANCE_CREATED"
    MAINTENANCE_SCHEDULED = "MAINTENANCE_SCHEDULED"
    MAINTENANCE_STARTED = "MAINTENANCE_STARTED"
    MAINTENANCE_COMPLETED = "MAINTENANCE_COMPLETED"
    MAINTENANCE_CANCELLED = "MAINTENANCE_CANCELLED"
    MAINTENANCE_OVERDUE = "MAINTENANCE_OVERDUE"
    MAINTENANCE_TASK_ADDED = "MAINTENANCE_TASK_ADDED"
    MAINTENANCE_TASK_COMPLETED = "MAINTENANCE_TASK_COMPLETED"

    # --- Tyre ---
    TYRE_REGISTERED = "TYRE_REGISTERED"
    TYRE_INSTALLED = "TYRE_INSTALLED"
    TYRE_REMOVED = "TYRE_REMOVED"
    TYRE_ROTATED = "TYRE_ROTATED"
    TYRE_REPAIRED = "TYRE_REPAIRED"
    TYRE_RETREADED = "TYRE_RETREADED"
    TYRE_RETIRED = "TYRE_RETIRED"
    TYRE_REPLACED = "TYRE_REPLACED"
    TYRE_PRESSURE_ALERT = "TYRE_PRESSURE_ALERT"

    # --- Asset ---
    ASSET_REGISTERED = "ASSET_REGISTERED"
    ASSET_INSTALLED = "ASSET_INSTALLED"
    ASSET_REMOVED = "ASSET_REMOVED"
    ASSET_CALIBRATED = "ASSET_CALIBRATED"
    ASSET_REPAIRED = "ASSET_REPAIRED"
    ASSET_REPLACED = "ASSET_REPLACED"
    ASSET_RETIRED = "ASSET_RETIRED"

    # --- Expense ---
    EXPENSE_ADDED = "EXPENSE_ADDED"
    EXPENSE_APPROVED = "EXPENSE_APPROVED"
    EXPENSE_REJECTED = "EXPENSE_REJECTED"

    # --- Compliance ---
    INSURANCE_EXPIRY_ALERT = "INSURANCE_EXPIRY_ALERT"
    PERMIT_EXPIRY_ALERT = "PERMIT_EXPIRY_ALERT"
    # --- Documents & Evidence ---
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    EVIDENCE_PACKAGE_READY = "EVIDENCE_PACKAGE_READY"
    
    # --- Validation ---
    VALIDATION_SUCCEEDED = "VALIDATION_SUCCEEDED"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    VALIDATION_DISPUTED = "VALIDATION_DISPUTED"
    
    # --- Processing ---
    PROCESSING_COMPLETED = "PROCESSING_COMPLETED"
    PROCESSING_FAILED = "PROCESSING_FAILED"

    # --- System ---
    SYSTEM_SYNC = "SYSTEM_SYNC"


class EntityType(str, enum.Enum):
    """
    The type of the primary fleet entity that this event is about.

    Used to namespace entity_id so "42" as a VEHICLE is distinct from
    "42" as a DRIVER.
    """

    VEHICLE = "VEHICLE"
    DRIVER = "DRIVER"
    TRIP = "TRIP"
    ROUTE = "ROUTE"
    EXPENSE = "EXPENSE"
    MAINTENANCE = "MAINTENANCE"
    TYRE = "TYRE"
    DOCUMENT = "DOCUMENT"
    SYSTEM = "SYSTEM"
    ASSET = "ASSET"


class CaptureMethod(str, enum.Enum):
    """
    How the event was captured / entered into the system.

    Used by the Validation & Enrichment Engine to apply the correct
    validation rules and trust levels.
    """

    WHATSAPP_BOT = "WHATSAPP_BOT"       # Driver self-reported via WhatsApp
    TELEMATICS = "TELEMATICS"           # IoT / GPS gateway push
    MANUAL_ENTRY = "MANUAL_ENTRY"       # Fleet manager typed it in
    API_INTEGRATION = "API_INTEGRATION" # Third-party system webhook
    SYSTEM_GENERATED = "SYSTEM_GENERATED"  # Automated platform rule


class VerificationStatus(str, enum.Enum):
    """
    Lifecycle status of the event as it moves through verification.

    State machine (simplified):
        PENDING → VERIFIED
        PENDING → DISPUTED → VERIFIED | REJECTED
        PENDING → REJECTED
    """

    PENDING = "PENDING"         # Received, awaiting validation
    VERIFIED = "VERIFIED"       # Passed all validation checks
    DISPUTED = "DISPUTED"       # Flagged for human review
    REJECTED = "REJECTED"       # Failed validation; will not be processed


# ===========================================================================
# ORM Model
# ===========================================================================

class OperationalEvent(Base):
    """
    Immutable record of a single fleet operational event.

    Every meaningful thing that happens in the fleet — a fuel fill, a trip
    start, an expense submission — is captured here before any processing.

    This table is the Operational Event Store: the authoritative, append-only
    log of fleet activity.  Downstream systems (Event Processor, Fleet Memory,
    Fleet Intelligence Engine) read from this store; they do NOT write back.

    Columns
    -------
    id                  : UUID primary key — globally unique, safe for
                          distributed capture.
    event_type          : What happened (EventType enum).
    entity_type         : The domain entity this event is about
                          (EntityType enum).
    entity_id           : String ID of the entity (vehicle plate, driver ID,
                          trip ID, etc.).  String to accommodate UUID,
                          integer, or composite keys.
    occurred_at         : When the event happened in the physical world.
                          May differ from recorded_at (offline capture, etc.).
    recorded_at         : When the event was recorded in this system (UTC).
    capture_method      : How the event entered the system
                          (CaptureMethod enum).
    verification_status : Current validation state
                          (VerificationStatus enum).
    created_by          : ID of the user or system that submitted this event.
                          Nullable for system-generated events.
    payload             : JSON bag of event-specific data.
                          Schema is defined per event_type by the consuming
                          services — not enforced at the DB layer.
    event_metadata      : JSON bag of operational metadata — source IP,
                          device ID, app version, correlation IDs, etc.
                          Named event_metadata to avoid collision with
                          SQLAlchemy's reserved 'metadata' attribute.
    notes               : Optional free-text annotation by a fleet manager.
    created_at          : Row insert timestamp (managed by DB).
    updated_at          : Row last-update timestamp (managed by DB).
                          Only the mutable fields (verification_status, notes)
                          should ever change.
    """

    __tablename__ = "operational_events"

    # --- Primary Key ---
    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Globally unique event identifier (UUID v4).",
    )

    # --- Multi-Tenancy ---
    company_id: Mapped[int] = mapped_column(
        sa.Integer,
        sa.ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Tenant isolation boundary.",
    )

    # --- Event Classification ---
    event_type: Mapped[EventType] = mapped_column(
        Enum(EventType, native_enum=False, length=50),
        nullable=False,
        index=True,
        comment="What happened — drives processing logic in downstream consumers.",
    )
    entity_type: Mapped[EntityType] = mapped_column(
        Enum(EntityType, native_enum=False, length=50),
        nullable=False,
        index=True,
        comment="The primary fleet entity domain this event concerns.",
    )
    entity_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment=(
            "Identifier of the specific entity (vehicle plate, driver UUID, etc.). "
            "String type to accommodate heterogeneous entity key formats."
        ),
    )
    company_id: Mapped[int] = mapped_column(
        nullable=False,
        index=True,
        comment="Tenant isolation identifier",
    )

    # --- Temporal ---
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment=(
            "Wall-clock time when the event occurred in the physical world. "
            "For offline-captured events this precedes recorded_at."
        ),
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="UTC timestamp when this event was received and stored by the platform.",
    )

    # --- Capture & Verification ---
    capture_method: Mapped[CaptureMethod] = mapped_column(
        Enum(CaptureMethod, native_enum=False, length=50),
        nullable=False,
        comment="Channel through which this event entered the system.",
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, native_enum=False, length=50),
        nullable=False,
        default=VerificationStatus.PENDING,
        index=True,
        comment="Validation lifecycle state — updated by the Validation & Enrichment Engine.",
    )

    # --- Actor ---
    created_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment=(
            "ID of the user or system service that submitted this event. "
            "Null for fully automated / system-generated events."
        ),
    )

    # --- Schemaless Payload ---
    payload: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment=(
            "Event-specific data bag.  Schema is owned by the service "
            "producing this event_type and documented in the Event Catalogue. "
            "Maps to JSONB on PostgreSQL for indexing support."
        ),
    )
    event_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment=(
            "Operational metadata: source IP, device ID, app version, "
            "correlation IDs, retry counts, etc.  Not business data. "
            "Named event_metadata to avoid SQLAlchemy's reserved 'metadata'."
        ),
    )

    # --- Annotation ---
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Free-text annotation added by a fleet manager during review.",
    )

    # --- Audit Timestamps ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Row insert timestamp — managed by the database.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Row last-modified timestamp — managed by the database.",
    )

    def __repr__(self) -> str:
        return (
            f"<OperationalEvent("
            f"id={self.id}, "
            f"type={self.event_type.value}, "
            f"entity={self.entity_type.value}:{self.entity_id}, "
            f"status={self.verification_status.value}"
            f")>"
        )
