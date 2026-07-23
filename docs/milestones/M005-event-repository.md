# Milestone 5 — Operational Event Repository

---

## Overview

This milestone introduces the repository layer to FleetGuard by implementing
`OperationalEventRepository` — the first data-access class in the project.

The repository provides a clean, reusable, fully-typed interface for all
database operations on the `operational_events` table. It sits between the
service layer and SQLAlchemy, so no future service or router will write raw
SQL queries against this table.

No business logic, routers, or APIs were created.

---

## Objective

The `OperationalEvent` domain model and database migration existed, but
nothing could write to or read from the table yet. This milestone:

- Establishes the `repositories/` package as a new project-level layer.
- Implements all read, write, and update operations needed by future services.
- Introduces domain-level exceptions (`EventNotFoundError`,
  `EventPersistenceError`) that are decoupled from HTTP.
- Preserves the existing `services/` and `routers/` code without modification.

---

## Repository Responsibilities

The repository layer owns **only** the following concerns:

| Concern | Owned By |
|---|---|
| Translate queries into SQLAlchemy statements | Repository ✓ |
| Execute statements against the `AsyncSession` | Repository ✓ |
| Raise domain-level exceptions | Repository ✓ |
| Structured logging of write operations | Repository ✓ |
| Business / validation logic | Service layer ✗ |
| HTTP error responses | Router layer ✗ |
| Pydantic schema conversion | Router / Service ✗ |

---

## Repository Methods

### Write

| Method | Description |
|---|---|
| `create_event(event)` | Persist a fully constructed `OperationalEvent` instance. Flushes and refreshes to populate server-generated fields. |
| `update_event_notes(event_id, notes)` | Replace the `notes` field. Accepts `None` to clear. |
| `update_event_metadata(event_id, event_metadata)` | Replace the `event_metadata` JSONB field. Intended for the Validation & Enrichment Engine. |
| `update_verification_status(event_id, status)` | Advance the `verification_status` field. State-machine enforcement is the service layer's responsibility. |

### Read

| Method | Description |
|---|---|
| `get_event_by_id(event_id)` | Fetch a single event by UUID. Raises `EventNotFoundError` if absent. |
| `list_events(limit, offset)` | All events, paginated, ordered by `occurred_at` DESC. |
| `list_events_by_entity(entity_type, entity_id, limit, offset)` | All events for a specific entity (e.g. vehicle `MH12AB1234`). Uses composite index. |
| `list_events_by_type(event_type, limit, offset)` | All events of a given `EventType` (e.g. `FUEL_FILLED`). Uses `event_type` index. |
| `list_events_by_verification_status(status, limit, offset)` | Events in a given `VerificationStatus` state (e.g. PENDING queue). Uses `verification_status` index. |

### Domain Exceptions

| Exception | Raised When |
|---|---|
| `EventNotFoundError` | An event UUID does not exist in the database. |
| `EventPersistenceError` | A database write fails due to constraint violation or unexpected error. |

> **These are not HTTP exceptions.** The router layer is responsible for
> mapping them to appropriate HTTP status codes (404, 409, 500).

---

## Files Created

| File | Purpose |
|---|---|
| `backend/repositories/__init__.py` | Repositories package — exports `OperationalEventRepository` |
| `backend/repositories/operational_event_repository.py` | Full repository implementation with 9 async methods and 2 domain exceptions |

---

## Files Modified

None. All existing files — models, schemas, services, routers, authentication — are unchanged.

---

## Architecture

The repository layer slots between the service layer and the database:

```
┌─────────────────────────────────────────┐
│              Router Layer               │  ← FastAPI endpoints
│  (translates HTTP ↔ service calls)      │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│             Service Layer               │  ← (next milestone)
│  (business logic, orchestration)        │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│           Repository Layer              │  ← THIS milestone
│  OperationalEventRepository             │
│  EventNotFoundError                     │
│  EventPersistenceError                  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         SQLAlchemy AsyncSession         │
│         (injected via get_db)           │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         PostgreSQL Database             │
│         operational_events table        │
└─────────────────────────────────────────┘
```

### Dependency Injection

The repository follows the same pattern as the rest of the project. The
`AsyncSession` is injected via FastAPI's `Depends(get_db)`:

```python
@router.post("/events")
async def submit_event(db: AsyncSession = Depends(get_db)):
    repo = OperationalEventRepository(db)
    event = await repo.create_event(...)
```

### SQLAlchemy 2.x Style

All queries use `select()` / `execute()` / `scalars().all()`. The legacy
`session.query()` API is never used.

---

## Current Limitations

- **No soft delete** — the project has no soft-delete convention, so
  `delete_event()` was intentionally omitted per the specification.
  Hard deletion should be added only when a deliberate design decision is made.
- **No advanced filtering** — `list_events()` supports only pagination.
  Combined filters (e.g. entity + status + date range) are not yet implemented.
  These belong in a future `EventQueryFilter` pattern.
- **No JSONB payload querying** — the `payload` and `event_metadata` JSONB
  columns are not queried against in this milestone. GIN indexes and JSON
  path queries will be needed when the Event Processor begins filtering on
  payload fields.
- **Not yet connected to a router** — the repository exists but no API
  endpoint exposes it yet.
- **Session transaction management** — the repository flushes but does not
  commit. Commit is the responsibility of the `get_db` dependency
  (on successful exit) or the service layer. This is intentional.

---

## Next Milestone

**Milestone 6 — Operational Event Service and Router**

Implement:
- `OperationalEventService` — orchestrates `OperationalEventRepository`
  calls, enforces the `VerificationStatus` state machine, converts ORM
  instances to Pydantic response schemas.
- `POST /api/v1/events` — submit a new operational event.
- `GET /api/v1/events/{id}` — retrieve a single event by UUID.
- `GET /api/v1/events` — paginated event list with optional filters.
- `PATCH /api/v1/events/{id}` — update `notes` or `verification_status`.
