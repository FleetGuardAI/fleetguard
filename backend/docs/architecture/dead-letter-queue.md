# Dead Letter Queue (DLQ) Architecture

The FleetGuard Dead Letter Queue serves as a highly robust forensic isolation mechanism for messages that cannot be processed by our Kafka consumers. It acts as the final safety net after the Retry Framework exhausts all transient retries.

## Purpose

When a consumer encounters a poison pill (un-deserializable message) or a chronically failing event (exhausted retries), stalling the consumer partition forever halts the entire event pipeline. The DLQ prevents this by safely routing the broken message into an isolated topic, `fleetguard.dlq`, while preserving the exact state of the failure for human intervention.

## Failure Lifecycle

1. **Poison Pill (`_handle_poison_pill`)**: If the initial Kafka byte payload cannot be deserialized, a `DeadLetterMessage` is constructed with `FailureCategory.DESERIALIZATION`. The raw payload is preserved.
2. **Processing Failure (`_handle_processing_failure`)**: If the event is deserialized successfully but throws an unhandled exception during business/infrastructure logic (e.g. `SQLAlchemyError`), the `RetryExecutor` will attempt retries. Once retries are exhausted (or if the error is non-retryable), a `DeadLetterMessage` is constructed using the appropriate `FailureCategory` (e.g. `DATABASE`, `NETWORK`, `VALIDATION`).

## Publishing Guarantees

We strictly mandate that a Kafka consumer **never** commits an offset for a failed message until it has explicitly received acknowledgment that the message is safely stored in the DLQ topic.
- If publishing to the DLQ fails (e.g., Kafka is down entirely), the exception bubbles up, the offset is not committed, and the consumer stalls safely. Upon restart, it will organically fetch the same message again.

## Forensic DLQ Schema

The `DeadLetterMessage` schema is designed to require absolutely zero parsing to understand the failure context. It captures:
- **Origin Context**: Topic, partition, offset.
- **Payload**: The exact string payload, strictly un-truncated, preserving the true state of the event.
- **Categorization**: A `FailureCategory` enum enabling operational dashboards to sort failures by root cause (Database vs Validation) without regex parsing stack traces.
- **Traceability**: The full exception type, message, stringified stack trace, and the exact count of `retry_attempts` executed before failure.

## Replay Considerations

Currently, the DLQ strictly isolates messages. In future milestones, tooling will be built to subscribe to the DLQ topic and replay corrected messages back into the operational events pipeline using the forensic payload captured here.
