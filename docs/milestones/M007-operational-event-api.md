# Milestone 7 — Operational Event API

---

## Overview

This milestone exposes the Operational Event Service through a REST API layer.

Eight endpoints are registered under `/api/v1/events`. The router is
intentionally thin — it validates requests, delegates to the service, maps
exceptions to HTTP status codes, and returns response schemas. No business
logic lives in the router.

---

## Objective

The service layer (Milestone 6) existed but had no HTTP entry point. This
milestone adds the FastAPI router that allows other systems and the future
frontend to submit, query, and annotate Operational Events over HTTP.

---

## Endpoints

| Method | Path | Status | Description |
|---|---|---|---|
| `POST` | `/api/v1/events` | 201 | Submit a new Operational Event |
| `GET` | `/api/v1/events` | 200 | Paginated list of all events |
| `GET` | `/api/v1/events/{event_id}` | 200 | Single event by UUID |
| `GET` | `/api/v1/events/entity/{entity_type}/{entity_id}` | 200 | Events for a specific fleet entity |
| `GET` | `/api/v1/events/type/{event_type}` | 200 | Events filtered by EventType |
| `GET` | `/api/v1/events/status/{verification_status}` | 200 | Events filtered by VerificationStatus |
| `PATCH` | `/api/v1/events/{event_id}/notes` | 200 | Update event annotation |
| `PATCH` | `/api/v1/events/{event_id}/metadata` | 200 | Replace event metadata JSONB |

### Pagination

All list endpoints accept `?limit=50&offset=0` query parameters.

- `limit`: integer 1–200, default 50
- `offset`: integer ≥ 0, default 0

### Path Parameters

| Parameter | Type | Source |
|---|---|---|
| `event_id` | UUID | `uuid.UUID` — validated by FastAPI |
| `entity_type` | `EntityType` enum | Validated automatically against the enum |
| `event_type` | `EventType` enum | Validated automatically against the enum |
| `verification_status` | `VerificationStatus` enum | Validated automatically against the enum |

### Exception → HTTP Mapping

| Service Exception | HTTP Status | Detail |
|---|---|---|
| `EventNotFound` | 404 Not Found | `"Operational event '{id}' not found."` |
| `EventWriteError` | 500 Internal Server Error | `"Event write error: {detail}"` |

---

## Request Flow

```
HTTP Request
    │
    ▼
FastAPI (Pydantic validation — automatic)
    │
    ▼
Router Function
    │  Depends(get_event_service)
    ▼
OperationalEventService
    │
    ▼
OperationalEventRepository
    │
    ▼
PostgreSQL — operational_events
    │
    ▼
OperationalEventResponse (Pydantic)
    │
    ▼
HTTP Response (JSON)
```

The router never touches the database or repository. The only object it
instantiates is the service (via the `get_event_service` dependency).

---

## Route Ordering (Important)

FastAPI matches routes in definition order. The static-prefix routes:

```
GET /api/v1/events/entity/{entity_type}/{entity_id}
GET /api/v1/events/type/{event_type}
GET /api/v1/events/status/{verification_status}
```

are defined **before** the parameterised route:

```
GET /api/v1/events/{event_id}
```

This ensures FastAPI does not attempt to parse `entity`, `type`, or `status`
as UUID values.

---

## Files Created

| File | Purpose |
|---|---|
| `backend/routers/operational_events.py` | Router with 8 endpoints, DI factory, inline PATCH schemas, exception helper |

## Files Modified

| File | Change |
|---|---|
| `backend/main.py` | Added `operational_events_router` import and `app.include_router()` call |

No other files were modified. All existing routers and auth are unchanged.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   HTTP Client                       │
└──────────────────────────┬──────────────────────────┘
                           │  POST / GET / PATCH
┌──────────────────────────▼──────────────────────────┐
│        routers/operational_events.py                │  ← THIS milestone
│                                                     │
│  POST   /api/v1/events          → create_event()    │
│  GET    /api/v1/events          → list_events()     │
│  GET    /api/v1/events/{id}     → get_event()       │
│  GET    /api/v1/events/entity/… → list_by_entity()  │
│  GET    /api/v1/events/type/…   → list_by_type()    │
│  GET    /api/v1/events/status/… → list_by_status()  │
│  PATCH  /api/v1/events/{id}/notes    → update_notes()    │
│  PATCH  /api/v1/events/{id}/metadata → update_metadata() │
│                                                     │
│  Exception mapping:                                 │
│    EventNotFound   → HTTP 404                       │
│    EventWriteError → HTTP 500                       │
└──────────────────────────┬──────────────────────────┘
                           │  Depends(get_event_service)
┌──────────────────────────▼──────────────────────────┐
│        services/operational_event_service.py        │
└──────────────────────────┬──────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────┐
│        repositories/operational_event_repository.py │
└──────────────────────────┬──────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────┐
│        PostgreSQL — operational_events              │
└─────────────────────────────────────────────────────┘
```

---

## Current Limitations

- **No authentication guard** — the endpoints are currently public. A
  `Depends(get_current_user)` guard should be added when the access control
  policy for this API is decided.
- **No combined filters** — there is no single `GET /events` query that
  accepts entity + type + status + date range simultaneously. This requires
  a `EventQueryFilter` schema and a new repository method.
- **Extension hooks do nothing** — `_after_create`, `_before_status_change`,
  and `_on_metadata_update` in the service are still stubs.
- **No `PATCH /events/{id}` general update** — the `OperationalEventUpdate`
  schema (which combines `verification_status` + `notes` in one call) is
  wired in the service via `apply_update()` but not exposed as an endpoint yet.
  The two separate PATCH endpoints (`/notes`, `/metadata`) cover current needs.

---

## Future Integrations

| Module | How It Plugs In |
|---|---|
| **Authentication guard** | Add `current_user: User = Depends(get_current_user)` to endpoint signatures |
| **Event Dispatcher** | Fill `_after_create` stub in the service — no router changes needed |
| **Validation & Enrichment Engine** | Fill `_before_status_change` stub — no router changes needed |
| **Fleet Memory** | Triggered via `_after_create` hook — no router changes needed |

---

## Next Milestone

**Milestone 8 — Event Dispatcher / Validation & Enrichment Engine**

Implement:
- Wire the `_after_create` hook to dispatch newly created events for processing.
- Wire the `_before_status_change` hook to enforce the `VerificationStatus`
  state machine.
- Begin the Validation & Enrichment Engine that reads the PENDING queue and
  advances events through the verification lifecycle.
