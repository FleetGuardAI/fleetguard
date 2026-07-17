# Milestone 6 — Operational Event Service

---

## Overview

This milestone implements `OperationalEventService` — the thin coordination
layer that sits between FastAPI routers (and all future fleet modules) and the
`OperationalEventRepository`.

Every module that needs to record or query Operational Events calls this
service. No module calls the repository directly.

No routers, APIs, event dispatchers, or validation logic were created.

---

## Objective

The repository layer (Milestone 5) provided raw database access but exposed
ORM types and domain exceptions that are not appropriate for callers.
This milestone bridges that gap by:

- Accepting Pydantic schemas as input and returning Pydantic schemas as output.
- Translating repository domain exceptions into service-level exceptions.
- Constructing ORM instances on behalf of callers.
- Providing explicit, named extension points for future integrations.

---

## Why a Service Layer Exists

| Without a service layer | With a service layer |
|---|---|
| Every router constructs ORM instances manually | Service owns ORM construction |
| Every router handles `EventNotFoundError`, `EventPersistenceError` | Service translates to `EventNotFound`, `EventWriteError` |
| Every router does `model_validate()` conversion | Service returns `OperationalEventResponse` directly |
| No single place to wire future integrations | Three named async hooks as extension points |

The service layer also makes the system **testable in isolation**: mock the
repository, test the service, without touching the database.

---

## Responsibilities

The service is **thin**. It only:

- Accepts `OperationalEventCreate` / `OperationalEventUpdate` schemas.
- Constructs `OperationalEvent` ORM instances.
- Delegates all persistence to `OperationalEventRepository`.
- Converts ORM instances to `OperationalEventResponse` schemas before returning.
- Translates repository exceptions into service exceptions.
- Calls named async extension-point hooks at defined lifecycle moments.

The service does **not**:

- Write SQL.
- Implement business intelligence.
- Validate event payloads.
- Dispatch events.
- Raise HTTP exceptions.

---

## Service Methods

### Write

| Method | Input | Output | Description |
|---|---|---|---|
| `create_event(payload)` | `OperationalEventCreate` | `OperationalEventResponse` | Persist a new event. Calls `_after_create` hook on success. |
| `update_notes(event_id, notes)` | `uuid.UUID`, `str \| None` | `OperationalEventResponse` | Update the annotation field. |
| `update_metadata(event_id, metadata)` | `uuid.UUID`, `dict` | `OperationalEventResponse` | Replace the JSONB metadata field. Calls `_on_metadata_update` hook. |
| `apply_update(event_id, update)` | `uuid.UUID`, `OperationalEventUpdate` | `OperationalEventResponse` | Apply a partial PATCH — handles `verification_status` and `notes`. Calls `_before_status_change` hook. |

### Read

| Method | Output | Description |
|---|---|---|
| `get_event(event_id)` | `OperationalEventResponse` | Single event by UUID. |
| `list_events(limit, offset)` | `Sequence[OperationalEventResponse]` | All events, paginated. |
| `list_events_by_entity(entity_type, entity_id, ...)` | `Sequence[OperationalEventResponse]` | All events for a specific entity. |
| `list_events_by_type(event_type, ...)` | `Sequence[OperationalEventResponse]` | All events of a given type. |
| `list_events_by_verification_status(status, ...)` | `Sequence[OperationalEventResponse]` | All events in a given verification state. |

### Service Exceptions

| Exception | Base | Raised When |
|---|---|---|
| `EventServiceError` | `Exception` | Base class — catch this to handle any service error. |
| `EventNotFound` | `EventServiceError` | Requested event UUID does not exist. |
| `EventWriteError` | `EventServiceError` | Persistence failed at the repository layer. |

> Routers map these to HTTP status codes. `EventNotFound` → 404.
> `EventWriteError` → 500.  No HTTP knowledge lives in the service.

---

## Extension Points (Future Integrations)

Three async stubs are wired at the correct lifecycle positions.
They currently `pass` with no side effects. Replace the bodies when the
corresponding modules are built.

| Hook | When Called | Future Use |
|---|---|---|
| `_after_create(event)` | After successful event persist | Event Dispatcher, Fleet Memory |
| `_before_status_change(event_id, new_status)` | Before `verification_status` write | Validation & Enrichment Engine — state machine guard |
| `_on_metadata_update(event)` | After `event_metadata` write | Validation Engine audit, Fleet Memory re-evaluation |

No structural changes to the service will be needed when these are wired —
only the bodies of the stubs change.

---

## Files Created

| File | Purpose |
|---|---|
| `backend/services/operational_event_service.py` | `OperationalEventService` class with 9 async methods, 3 extension-point stubs, and 3 service exceptions |

## Files Modified

| File | Change |
|---|---|
| `backend/services/__init__.py` | Added `OperationalEventService`, `EventServiceError`, `EventNotFound`, `EventWriteError` to package exports. Auth exports unchanged. |

---

## Architecture

```
┌─────────────────────────────────────────────┐
│             Router / External Module        │
│  (calls service, maps exceptions to HTTP)   │
└─────────────────┬───────────────────────────┘
                  │ OperationalEventCreate / uuid / VerificationStatus
┌─────────────────▼───────────────────────────┐
│         OperationalEventService             │  ← THIS milestone
│                                             │
│  create_event()    get_event()              │
│  update_notes()    list_events()            │
│  update_metadata() list_events_by_entity()  │
│  apply_update()    list_events_by_type()    │
│                    list_events_by_status()  │
│                                             │
│  _after_create()          ← hook (stub)     │
│  _before_status_change()  ← hook (stub)     │
│  _on_metadata_update()    ← hook (stub)     │
│                                             │
│  Returns: OperationalEventResponse          │
│  Raises:  EventNotFound / EventWriteError   │
└─────────────────┬───────────────────────────┘
                  │ OperationalEvent ORM / exceptions
┌─────────────────▼───────────────────────────┐
│       OperationalEventRepository            │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│         PostgreSQL — operational_events     │
└─────────────────────────────────────────────┘
```

---

## Current Limitations

- **No router** — the service has no HTTP entry point yet. Calling it requires
  direct instantiation in tests or the next milestone's router.
- **Extension hooks do nothing** — `_after_create`, `_before_status_change`,
  and `_on_metadata_update` are stubs. Events are not dispatched or processed
  downstream.
- **No state machine enforcement** — `_before_status_change` is a stub. Invalid
  `VerificationStatus` transitions (e.g. `VERIFIED → PENDING`) are not yet
  blocked.
- **No combined filters** — `list_events()` supports only pagination. Filtering
  by entity + type + status + date range in a single call is not yet supported.

---

## Future Integrations

| Module | Integration Point | What Changes |
|---|---|---|
| **Event Dispatcher** | `_after_create` stub | Publish the event to downstream queue/processor |
| **Fleet Memory** | `_after_create` stub | Update the digital twin for the entity |
| **Validation & Enrichment Engine** | `_before_status_change` stub | Enforce state machine; enrich event metadata |

---

## Next Milestone

**Milestone 7 — Operational Event Router and API**

Implement:
- `POST /api/v1/events` — submit a new operational event
- `GET /api/v1/events/{id}` — retrieve a single event by UUID
- `GET /api/v1/events` — paginated event list with optional query filters
- `PATCH /api/v1/events/{id}` — update `notes` or advance `verification_status`

The router maps `EventNotFound` → HTTP 404 and `EventWriteError` → HTTP 500.
No business logic enters the router.
