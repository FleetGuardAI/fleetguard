# FleetGuard Idempotency Framework

## Why Idempotency is Required
FleetGuard utilizes an Event-Driven Architecture powered by Apache Kafka. Kafka guarantees **At-Least-Once delivery**. This means that in various failure scenarios (such as a database timeout, a consumer pod crash before an offset is committed, or a partition rebalance), the consumer may receive the exact same Operational Event more than once.

Without idempotency, a Business Domain receiving a duplicate `FUEL_FILLED` event would create duplicate `FuelLog` entries and duplicate `Expense` records, leading to severe financial inflation and data corruption.

## Duplicate Detection Strategy
FleetGuard handles idempotency at the orchestration layer (the `ProcessingEngine`) rather than pushing this responsibility into every Business Domain. 

This guarantees:
1. **Consistency**: All domains share the exact same robust duplicate-detection logic.
2. **Clean Architecture**: Business Domains remain entirely ignorant of Kafka semantics, retries, and deduplication. They simply expose `apply_verified_event(event)`.

### How Duplicate Events are Skipped
The `ProcessingService` wraps the entire domain execution block within an atomic database transaction using an injected `AsyncSession`. 

For each domain target:
1. The `ProcessingService` queries the `IdempotencyService` to check if a `ProcessedEvent` record already exists for the tuple `(operational_event_id, domain_name)`.
2. If the record exists, the event is immediately skipped, logged as an `Idempotency Skip`, and execution moves to the next domain.
3. If the record does not exist, the `ProcessingService` invokes `domain.apply_verified_event()`.
4. Immediately after (within the exact same database session), it calls `IdempotencyService.mark_processed()` to stage the `ProcessedEvent` insertion.

### Atomic Guarantees
Because both the Business Domain's state mutations and the `IdempotencyService`'s `mark_processed()` operation share the same `AsyncSession`, they are committed to the database atomically in `await db.commit()`. 

- **Success**: The business data is saved and the event is permanently marked as processed. If Kafka redelivers, the `has_processed()` check will return `True`.
- **Failure**: If the Business Domain crashes or encounters a database error (e.g. `IntegrityError`), the orchestrator triggers an `await db.rollback()`. Neither the business data nor the `ProcessedEvent` is saved. When Kafka redelivers, it will safely attempt execution again.

## Failure Scenarios Handled
- **Kafka Redelivery**: Caught by the DB query. Execution skipped.
- **Consumer Restart**: Offset lost, event redelivered. Caught by the DB query. Execution skipped.
- **Application Crash mid-processing**: Transaction is orphaned and automatically rolled back by the database. No partial state is saved.
- **Network Retry**: Caught by unique constraint on the database if a race condition occurs.
