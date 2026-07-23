# Milestone 8 — Event Dispatcher

---

## Overview

This milestone introduces the **Event Dispatcher** — FleetGuard's internal
pub/sub bus that delivers newly persisted Operational Events to registered
subscribers.

After an event is created, `_after_create` in the `OperationalEventService`
now calls `EventDispatcher.publish()`. Every registered subscriber whose
`event_filter` matches receives the event asynchronously.

No external message broker is used. The dispatcher is in-process.

---

## Architecture

```
POST /api/v1/events
        │
        ▼
OperationalEventService.create_event()
        │  persist via repository
        ▼
PostgreSQL — operational_events
        │  success
        ▼
_after_create(event)
        │  calls
        ▼
EventDispatcher.publish(event)
        │
        ├─── filter ──► Subscriber A  (event_filter = {FUEL_FILLED})
        │                  └─ handle(event) — receives FUEL_FILLED only
        │
        ├─── filter ──► Subscriber B  (event_filter = None)
        │                  └─ handle(event) — receives ALL events
        │
        └─── no match ─► Subscriber C  (event_filter = {TRIP_STARTED})
                           └─ not called for FUEL_FILLED
```

Subscriber exceptions are **caught and logged**. They do not propagate to
the caller or roll back the database transaction.

---

## Dispatcher Responsibilities

The `EventDispatcher`:

- Maintains an ordered list of registered `EventSubscriber` instances.
- Applies each subscriber's `event_filter` on every publish call.
- Awaits each matching subscriber's `handle()` method in registration order.
- Catches, logs, and swallows subscriber exceptions so one bad subscriber
  cannot affect others.
- Enforces unique subscriber names to allow targeted unregistration.
- Knows nothing about the fleet domain (vehicles, drivers, fuel, etc.).

---

## Subscriber Model

Every subscriber implements `EventSubscriber` (ABC):

| Attribute | Type | Required | Description |
|---|---|---|---|
| `name` | `str` | Yes | Unique identifier. Used for unregistration and logging. |
| `event_filter` | `frozenset[EventType] \| None` | No | Event types to receive. `None` = all. |
| `handle(event)` | `async` method | Yes | Called by dispatcher for each matching event. |

### Example

```python
from dispatchers import EventSubscriber
from models.operational_event import EventType

class FuelMonitorSubscriber(EventSubscriber):
    name = "fuel_monitor"
    event_filter = frozenset({EventType.FUEL_FILLED, EventType.FUEL_ALERT_TRIGGERED})

    async def handle(self, event: OperationalEventResponse) -> None:
        # React to fuel events — no HTTP, no domain logic here
        ...
```

---

## Dispatcher API

| Method | Description |
|---|---|
| `register_subscriber(subscriber)` | Add a subscriber. Raises `ValueError` on duplicate name. |
| `unregister_subscriber(name)` | Remove by name. Raises `KeyError` if not found. |
| `publish(event)` | Deliver to all matching subscribers. `async`. |
| `subscriber_names` | Property — list of registered names. |
| `len(dispatcher)` | Number of registered subscribers. |

---

## Files Created

| File | Purpose |
|---|---|
| `backend/dispatchers/__init__.py` | Package — exports `EventDispatcher`, `EventSubscriber` |
| `backend/dispatchers/event_dispatcher.py` | `EventDispatcher` — pub/sub bus implementation |
| `backend/dispatchers/event_subscriber.py` | `EventSubscriber` — ABC subscriber contract |

## Files Modified

| File | Change |
|---|---|
| `backend/services/operational_event_service.py` | `__init__` accepts `dispatcher=None`; `_after_create` now calls `dispatcher.publish()` |
| `backend/routers/operational_events.py` | `get_event_service` dependency injects `event_dispatcher` from `main` |
| `backend/main.py` | Creates `event_dispatcher` singleton; logs it at startup; documents subscriber registration point |

---

## Replacement Strategy (Future)

When FleetGuard requires an external message broker:

1. Create `KafkaEventDispatcher` (or `RedisEventDispatcher`) implementing the
   same `register_subscriber` / `publish` interface.
2. Swap the singleton in `main.py`:
   ```python
   event_dispatcher = KafkaEventDispatcher(broker_url=settings.KAFKA_URL)
   ```
3. No changes needed in `OperationalEventService`, the router, or any subscriber.

Subscribers that currently implement `EventSubscriber.handle()` become Kafka
consumers — the interface stays the same, only the transport changes.

---

## Current Limitations

- **No retry on subscriber failure** — if a subscriber raises, the event is
  silently dropped for that subscriber. A dead-letter queue or retry decorator
  should be added when reliability becomes a requirement.
- **No ordering guarantee** — subscribers are called in registration order,
  but no cross-subscriber ordering is enforced.
- **No buffering** — if the process restarts between event persist and
  dispatch, the event is not re-dispatched. Events are not lost from the
  database, but subscribers miss them.
- **No subscribers yet** — the dispatcher is wired but has zero subscribers
  registered at startup. Future milestones add Fleet Memory, Validation Engine,
  and Finding Engine subscribers.
- **In-process only** — this implementation cannot distribute events across
  multiple backend processes or services.

---

## Next Milestone

**Milestone 9 — Validation & Enrichment Engine (Subscriber)**

Implement:
- `ValidationSubscriber(EventSubscriber)` — subscribes to `PENDING` events.
- Validates the event payload against per-`event_type` rules.
- Advances `verification_status` to `VERIFIED` or `REJECTED` via the service.
- Register it in `main.py` at startup.
