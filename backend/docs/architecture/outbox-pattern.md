# Transactional Outbox Pattern

## Why the Outbox Pattern Exists

In a distributed Event-Driven Architecture, ensuring that state changes in the database and the corresponding events published to the message broker (Kafka) are perfectly synchronized is a fundamental challenge. 

Prior to this implementation, the `OperationalEventService` would synchronously publish events to Kafka immediately after persisting them to the database. This created a dual-write problem:
- If the database commit succeeds, but the application crashes before publishing to Kafka, the event is permanently lost from the message bus.
- If the application publishes to Kafka first, but the database commit fails (e.g., due to a constraint violation), phantom events enter the messaging system.

The **Transactional Outbox Pattern** solves this by avoiding distributed transactions (2PC). Instead, the intent to publish is recorded in the *same database transaction* as the domain state change.

## Transaction Flow

FleetGuard utilizes a unified `SqlAlchemyUnitOfWork` to encapsulate business transactions.

When a new Operational Event is created:
1. `OperationalEventService` persists the `OperationalEvent` via the UnitOfWork.
2. Immediately after, it creates an `OutboxEvent` record via `uow.repositories.outbox.create_event()`.
3. The `ProcessingEngine` or Router issues a single `await uow.commit()`.

Because both records reside in the same SQL database, they are guaranteed to either commit together or rollback together. Nothing is published to Kafka at this stage.

## Publishing Flow

The responsibility for actual delivery to Kafka is offloaded to the **Outbox Publisher**, which runs asynchronously in the background.

1. **Polling Loop:** The `OutboxWorkerRunner` wakes up every configurable interval (default: `OUTBOX_POLL_INTERVAL_MS`).
2. **Locking (Batching):** It fetches a deterministic batch of `PENDING` outbox events, ordered by `created_at` ASC, and immediately marks them as `PUBLISHING` within a tight transaction.
3. **Dispatch:** For each event, the Publisher attempts to send it to the `KafkaEventBus`.
4. **Completion:** Upon successful Kafka acknowledgment, the event is marked as `PUBLISHED`. 

## Failure Recovery & Retry Strategy

If a transient failure occurs while communicating with Kafka:
- The event's status is reverted from `PUBLISHING` back to `PENDING`.
- `retry_count` is incremented.
- `last_error` is recorded for debugging.

The background worker will automatically pick up the event again on its next polling cycle.

*Note: Dead Letter Queues (DLQ) and permanent failure limits (moving events to `FAILED`) will be implemented in a subsequent epic.*
