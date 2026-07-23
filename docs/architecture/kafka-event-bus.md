# Kafka Event Bus

## Why Kafka Was Introduced
FleetGuard's Event-Driven Architecture initially utilized an in-process, synchronous `EventDispatcher`. While sufficient for early development, this coupled event production directly to event processing within the same HTTP request lifecycle. 

As FleetGuard scales, components like the `ValidationEngine` and `ProcessingEngine` require true asynchronous execution. Apache Kafka was introduced to:
1. Provide a robust, scalable pub/sub transport layer.
2. Decouple the write path (Operational Events) from downstream processing.
3. Allow independent scaling and isolation of background workers.
4. Guarantee message delivery even if a downstream consumer fails or restarts.

## Architecture
The new Event Bus is designed as a pluggable infrastructure layer. It replaces the legacy `EventDispatcher` without altering the core `EventSubscriber` contract or any Business Domain logic.

### Abstractions
- **`EventBus` Interface**: Abstract base class defining `publish(topic, event)`, `start()`, and `stop()`.
- **`KafkaEventBus`**: The `AIOKafkaProducer` implementation of `EventBus`.
- **`KafkaConsumerRunner`**: An infrastructure wrapper that polls Kafka and delegates to a local `SubscriberRegistry`.
- **`SubscriberRegistry`**: A local registry inside each consumer that maps incoming Kafka events to standard `EventSubscriber`s (e.g., `ValidationEngine`, `ProcessingEngineSubscriber`).

## Publishing Flow
1. An HTTP request calls `OperationalEventService.create_event(...)`.
2. The event is persisted to the database in `PENDING` state.
3. `_after_create` serializes the `OperationalEventResponse` using `EventSerializer`.
4. `KafkaEventBus.publish` sends the event to the `operational-events` topic using the `event_id` as the partition key.
5. The HTTP request completes, returning the `PENDING` event to the user in a fraction of the time.

## Consumer Flow
1. Independent `KafkaConsumerRunner` tasks (e.g., `validation-group`, `processing-group`) poll the `operational-events` topic.
2. Upon receiving a message, the runner deserializes it back into an `OperationalEventResponse`.
3. The runner checks its `SubscriberRegistry` for any subscribers interested in the specific `event_type`.
4. The event is delegated to `EventSubscriber.handle(event)`.
5. Only after successful execution (or graceful failure handling) does the consumer commit its offset.

## Serialization
The serialization layer is independent of the Business Domains and wraps the canonical event in a versioned envelope:
```json
{
  "event_id": "uuid",
  "event_type": "TRIP_STARTED",
  "entity_type": "TRIP",
  "entity_id": "uuid",
  "timestamp": "ISO-8601",
  "version": "1.0",
  "payload": { ... OperationalEventResponse ... },
  "metadata": { "source": "fleetguard-core" }
}
```

## Future Scalability (Event Chaining)
The `EventBus` design is generic (`publish(topic, event)`). While this milestone focuses solely on Operational Events, future architecture iterations can introduce derived topics (e.g., `validation-completed`, `evidence-created`) using the exact same transport infrastructure. This ensures the architecture is future-proof for advanced event chaining, Dead Letter Queues, and Analytics pipelines.
