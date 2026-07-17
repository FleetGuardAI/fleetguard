# Retry Framework

The FleetGuard Retry Framework is a resilient, transport-agnostic mechanism designed to handle transient infrastructure failures across our asynchronous services, primarily utilized by the Kafka consumer pipelines.

## Principles

1. **Transient Failures Only**: The Retry Framework explicitly only retries errors classified as temporary infrastructure failures (e.g., Database deadlocks, Connection drops, Kafka disconnects). 
2. **Business Isolation**: Business rules and duplicate detection live in the `Business Domains` and the `Idempotency Framework`. The Retry Framework never retries validation errors or payload format issues (these escalate immediately).
3. **Transport Agnostic**: The `RetryExecutor` has zero knowledge of Kafka, HTTP, or gRPC. It simply executes a callable policy constraint.

## Architecture

- **`RetryContext`**: A living snapshot of the retry loop state (current attempt, max attempts, total sleep duration).
- **`ErrorClassifier`**: Evaluates `Exception` objects. The `DefaultErrorClassifier` explicitly whitelists transient errors like `SQLAlchemyError` and `TimeoutError`. Unknown exceptions default to non-retryable.
- **`RetryStrategy`**: Calculates sleep duration.
- **`RetryPolicy`**: Configuration grouping Strategy, Classifier, and Max Attempts.
- **`RetryExecutor`**: The core component that executes an async callable, catching errors, verifying classification, checking exhaustion, and awaiting the strategy delay before looping.

## Backoff Strategies

The framework supports multiple configurable delay strategies:
- **`FixedDelayStrategy`**: Pauses for a static `N` seconds.
- **`ExponentialBackoffStrategy`**: Doubles the delay on each attempt up to a cap.
- **`ExponentialBackoffWithJitterStrategy`** *(Default)*: Doubles the delay, but injects up to 50% randomized jitter. This is the default policy to prevent **thundering herds** across horizontally scaled consumers when a database recovers.

## Integration & Future DLQ

Currently, the `KafkaConsumerRunner` initializes the `RetryExecutor`. When `subscriber.handle(event)` throws an exception:
1. The executor verifies if it is retryable. If so, it sleeps locally. This correctly stalls the Kafka partition, preserving head-of-line blocking and message ordering guarantees.
2. The default policy is calibrated to 5 attempts capping at 30 seconds, guaranteeing the total sleep window comfortably fits within Kafka's default `max.poll.interval.ms` (5 minutes) to prevent rebalance thrashing.
3. If exhausted or non-retryable, the executor throws `RetriesExhaustedError` or `NonRetryableError`.
4. The consumer catches this, logs structured diagnostics, and eventually (in the next milestone) will route this direct to the **Dead Letter Queue (DLQ)**.
