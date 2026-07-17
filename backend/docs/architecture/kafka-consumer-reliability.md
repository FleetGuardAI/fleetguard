# Kafka Consumer Reliability

## Consumer Architecture

FleetGuard operates multiple independent consumers (Validation, Processing, Evidence) subscribing to the operational events stream. 

To improve isolation, fault containment, and operational simplicity, we strictly enforce a **1-to-1 relationship** between a `KafkaConsumerRunner` and an `EventSubscriber`.

If an event needs to fan-out to multiple independent systems, Kafka topics and consumer groups provide the fan-out mechanism. The backend does not use an in-process subscriber list to replicate events.

## Offset Lifecycle & Commit Timing

The core mandate of the consumer is to guarantee **At-Least-Once** processing.
- `enable_auto_commit` is strictly disabled.
- The Kafka offset is committed **only** when the subscriber finishes its `handle()` method entirely without raising any unhandled exceptions.

## Failure Handling

### 1. Poison Pills (Deserialization Errors)
If an incoming message cannot be deserialized, it triggers the `_handle_poison_pill()` extension point. Currently, this prevents the offset from committing and purposefully stalls the consumer partition, safeguarding against silent data drops. In the future, this will route the poison pill directly to the Dead Letter Queue (DLQ).

### 2. Processing Failures
If the subscriber throws an exception (e.g. database disconnect, logic bug), it triggers `_handle_processing_failure()`. Like poison pills, this purposefully stalls the consumer. In the future, this will trigger an Exponential Backoff Retry policy before moving the event to the DLQ.

### 3. Graceful Shutdown
When the application signals shutdown, the consumer clears its running flag. It safely processes the in-flight message, commits the offset if successful, and aborts polling, preventing data corruption or hanging threads.
