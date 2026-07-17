# Processing Engine Architecture

## Overview
The **Processing Engine** is an Infrastructure Service responsible for coordinating the execution of validated Operational Events across FleetGuard's Business Domains.

Crucially, the Processing Engine is **not** a Business Domain. It owns no business logic, does not collect evidence, and does not validate data. It solely provides deterministic routing and execution orchestration.

## Responsibilities
- Subscribe exclusively to `VALIDATION_SUCCEEDED` Operational Events.
- Extract the original event ID from the payload and load the pristine original Operational Event from the database.
- Determine which Business Domains should process the event using the `DomainRouter`.
- Sequentially invoke each target domain's `apply_verified_event(...)` interface.
- Track execution state persistently in `ProcessingRecord`.
- Emit a new `PROCESSING_COMPLETED` or `PROCESSING_FAILED` Operational Event, detailing the outcome without mutating any previous events.

## Domain Routing
The `DomainRouter` explicitly maps specific `EventType` constants to Business Domain services.

This declarative routing solves the 1-to-N problem by allowing a single event (like `FUEL_FILLED`) to deterministically invoke multiple domains (like `FuelService`, then `ExpenseService`).

```python
# Example routing configuration
router.register(EventType.FUEL_FILLED, lambda db: FuelService(db))
router.register(EventType.FUEL_FILLED, lambda db: ExpenseService(db))
```

## Generated Events
To strictly maintain the invariant **"Persist Event -> Publish Event"** without mutating historical data, the Processing Engine emits:

- `PROCESSING_COMPLETED`: Emitted when all targeted domains successfully process the event.
- `PROCESSING_FAILED`: Emitted if any targeted domain fails.

### ProcessingResult Payload
The payload for processing events uses the `ProcessingResult` schema, providing granular observability:
- `processed_domains`: All domains that were intended to be invoked.
- `successful_domains`: Domains that completed successfully.
- `failed_domains`: Domains that threw an exception.
- `skipped_domains`: Domains that were not invoked because a preceding domain failed in the sequence.
- `processing_status`: The overall status (`COMPLETED` or `FAILED`).
- `processing_time_ms`: Execution time in milliseconds.

## Future Extensions
Adding a new Business Domain to an existing event is simply a matter of registering it in `DomainRouter`. Since the Processing Engine sequentially executes domains, they run in the order they are registered. Any failure immediately skips subsequent domains to prevent partial corruption.
