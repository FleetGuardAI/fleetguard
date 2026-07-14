# Overview

This milestone accomplished the creation of the foundational domain model for FleetGuard's Event-Driven Architecture. It introduced the ORM models, enumerations, and Pydantic schemas required to represent, validate, and store immutable operational events.

---

# Objective

The objective of this milestone was to establish the single source of truth for all platform operations. By defining a robust, schemaless event model, FleetGuard can securely record events (like fuel fills, trip starts, and driver assignments) before they are processed by downstream intelligence and validation engines.

---

# What Was Implemented

- **Models**: `OperationalEvent` (SQLAlchemy ORM model representing the event store)
- **Schemas**: 
  - `OperationalEventCreate` (Write path)
  - `OperationalEventUpdate` (Patch path for mutable fields)
  - `OperationalEventResponse` (Read path)
- **Enums**: 
  - `EventType` (Categorization of events e.g., FUEL_FILLED)
  - `EntityType` (Primary domain entity e.g., VEHICLE, DRIVER)
  - `CaptureMethod` (Source of the event e.g., WHATSAPP_BOT, TELEMATICS)
  - `VerificationStatus` (Lifecycle state e.g., PENDING, VERIFIED)

---

# Architecture

The Operational Event domain model sits at the very bottom of the Event-Driven Architecture. It acts as the data structure for the Operational Event Store. Every action in FleetGuard will be packaged as an `OperationalEventCreate` schema by upstream services, persisted as an `OperationalEvent` in the database, and subsequently read by downstream systems such as the Validation & Enrichment Engine, Event Processor, Fleet Memory, and the Fleet Intelligence Engine.

---

# Files Created

- `backend/models/operational_event.py`
- `backend/schemas/operational_event.py`

---

# Files Modified

- `backend/models/__init__.py` (Registered `OperationalEvent` model)
- `backend/schemas/__init__.py` (Exported Pydantic schemas)

---

# How It Works

1. **Ingestion Representation**: When a system or user performs an action, the data is encapsulated in an `OperationalEventCreate` schema. This schema explicitly defines the `event_type`, the `entity_type`, and contains a schemaless JSON `payload`.
2. **Persistence**: The data is mapped to the `OperationalEvent` SQLAlchemy model. The model automatically generates a UUID primary key and timestamp fields (`occurred_at`, `recorded_at`), and stores the record immutably in the database.
3. **Mutation**: Core event data is strictly immutable. Only the `verification_status` and `notes` fields can be altered over time, facilitated by the `OperationalEventUpdate` schema.
4. **Consumption**: Downstream systems retrieve the events utilizing the `OperationalEventResponse` schema for processing and analytics.

---

# Design Decisions

- **UUID Primary Keys**: Used `postgresql.UUID(as_uuid=True)` to ensure globally unique identifiers, making it safe for distributed event capture across multiple microservices.
- **JSON Payloads**: Utilized SQLAlchemy's `JSON` type for the event `payload` and `event_metadata`. This maps natively to JSONB in PostgreSQL for indexing performance while remaining compatible with the current SQLite development database.
- **Co-located Enums**: Placed all related Python `Enum` classes directly within the ORM model file to maintain a single source of truth and avoid circular dependencies.
- **Immutability by Design**: Designed the `OperationalEventUpdate` schema to exclusively expose `verification_status` and `notes`, enforcing the business rule that historical operational data cannot be altered.

---

# Current Limitations

- **No Active Endpoints**: No FastAPI routers or APIs have been implemented to receive or serve events.
- **No Business Logic**: There are no Service or Repository layers to handle the actual database insertion or querying.
- **No Payload Validation**: The `payload` field is currently a generic JSON object; strict validation rules per `event_type` are not enforced at this layer.
- **Downstream Consumers Missing**: The Validation & Enrichment Engine and Fleet Intelligence Engine that will consume these models do not yet exist.

---

# Next Milestone

The next milestone should implement the **Event Service and Repository**. This will involve building the business logic layer to securely write `OperationalEventCreate` objects into the database and building the FastAPI routers to expose standard REST endpoints for event ingestion.
