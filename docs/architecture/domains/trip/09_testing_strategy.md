# Trip Management Domain: Testing Strategy

The Trip Domain testing approach leverages the Test Pyramid, heavily weighting fast unit tests against the `TripAggregate` while utilizing isolated integration tests for the Event Handler.

## Unit Tests
Unit tests in this domain bypass the Event Handler and the Database. 
- **Aggregate Tests**: `test_trip_aggregate.py`. Ensure that `start_trip()` successfully transitions from `CREATED` to `IN_PROGRESS` and returns the correct `TripStarted` domain event. Verify that calling `pause_trip()` on a `COMPLETED` trip throws an `ImmutableTripError`.
- **Query Tests**: Ensure the CQRS projection logic correctly maps database rows to `pydantic` schemas without mutating state.

## Integration Tests (Event Handler)
`test_trip_domain.py` serves as a vertical integration test. 
1. Mocks an `OperationalEvent(IGNITION_STARTED)`.
2. Feeds it into `TripEventHandler.handle_event()`.
3. Verifies that the internal `TripService` executes.
4. Verifies the `InMemoryTripRepository` now contains an `IN_PROGRESS` trip.
5. Mocks an `OperationalEvent(IGNITION_STOPPED)`.
6. Verifies the trip ends up in a `COMPLETED` state.

This completely tests the event-driven business flow without requiring Kafka or PostgreSQL.

## Edge Cases and Failure Scenarios
Tests must explicitly cover:
- **Out of Order Events**: e.g., receiving `IGNITION_STOPPED` when there is no active trip. The system must degrade gracefully (log a warning, perhaps save a ghost state, but not crash).
- **Duplicate Events**: Processing `IGNITION_STARTED` twice in a row must not create two active trips for the same vehicle. Idempotency guarantees are tested here.
- **Repository Failures**: Mocking a database timeout to ensure the `TripEventHandler` bubbles the exception back to Kafka, invoking the retry mechanism.
