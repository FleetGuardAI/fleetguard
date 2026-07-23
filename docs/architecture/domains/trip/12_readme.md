# Trip Management Domain

**Bounded Context**: `Trip`
**Architecture Style**: Event-Driven, CQRS, Domain-Driven Design (DDD)

## Introduction
Welcome to the Trip Management Domain. This subsystem is the authoritative source of truth for the physical movement of vehicles in FleetGuard. 

Unlike traditional CRUD microservices, this domain exposes **no mutation APIs**. Its state is derived entirely by listening to FleetGuard `OperationalEvents` (such as engine ignition and GPS telemetry). 

## Quick Links

- [01. Overview](./01_overview.md): Domain purpose and bounded context boundaries.
- [02. Domain Model](./02_domain_model.md): Detailed breakdown of Aggregates, Entities, and Value Objects.
- [03. Event Flow](./03_event_flow.md): Sequence diagrams detailing how telematics events become Trips.
- [04. Lifecycle](./04_lifecycle.md): State diagrams detailing all valid state transitions.
- [05. API Reference](./05_api_reference.md): Documentation on the Read-Only REST API.
- [06. Queries & Projections](./06_queries_and_projections.md): Explanation of CQRS and Read Models.
- [07. Event Handler](./07_event_handler.md): How Kafka messages are routed into Domain logic.
- [08. Repository](./08_repository.md): Persistence abstractions and transaction boundaries.
- [09. Testing Strategy](./09_testing_strategy.md): How to unit and integration test this domain.
- [10. Extension Guide](./10_extension_guide.md): Rules for adding features without breaking boundaries.
- [11. Architecture Decisions (ADR)](./11_architecture_decisions.md): Historical record of *why* this system is designed this way.

## Development Guide
1. **Never** add a `POST /trips` endpoint. State changes must originate from Operational Events.
2. **Never** import models from other domains (`Vehicle`, `Driver`). Reference them purely by string or UUID.
3. Keep the `TripAggregate` completely free of database ORM logic or web frameworks.
