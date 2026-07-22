# Trip Management Domain

The Trip Management Domain is the authoritative source of truth for vehicle movement in FleetGuard.

## Architecture

This domain strictly follows FleetGuard's Event-Driven Architecture.
Trip is an **Event-Sourced Subsystem**. It exposes **NO REST API endpoints for mutation** (`POST /trips/start` does not exist).
The trip lifecycle is deterministically driven by immutable Operational Events via the `TripEventHandler`.

### Scope
- **In Scope:** Movement tracking (origin, destination, distance, duration).
- **Out of Scope:** Vehicle logic, Driver Assignment logic, Device mapping, or intelligence processing.

### Aggregate Design
`TripAggregate` enforces invariants around the lifecycle transitions.

```mermaid
stateDiagram-v2
    [*] --> CREATED: IGNITION_STARTED
    CREATED --> IN_PROGRESS: start()
    IN_PROGRESS --> PAUSED: pause()
    PAUSED --> IN_PROGRESS: resume()
    IN_PROGRESS --> COMPLETED: IGNITION_STOPPED
    IN_PROGRESS --> CANCELLED: cancel()
    CREATED --> CANCELLED: cancel()
    COMPLETED --> [*]
    CANCELLED --> [*]
```

### Event Flow

```mermaid
sequenceDiagram
    participant Telematics
    participant Gateway
    participant EventProcessor
    participant TripEventHandler
    participant TripAggregate
    
    Telematics->>Gateway: Engine On
    Gateway->>EventProcessor: OperationalEvent(IGNITION_STARTED)
    EventProcessor->>TripEventHandler: handle_event()
    TripEventHandler->>TripAggregate: start_trip()
    TripAggregate-->>EventBus: DomainEvent(TripStarted)
```

## Components
- **Aggregate**: `TripAggregate`
- **Event Handler**: `TripEventHandler`
- **Service**: `TripService`
- **Query Layer**: `TripQueryService`
- **Repository**: `BaseTripRepository` (with `InMemoryTripRepository`)

## Events
The domain emits the following Domain Events:
- `TripCreated`
- `TripStarted`
- `TripPaused`
- `TripResumed`
- `TripCompleted`
- `TripCancelled`
