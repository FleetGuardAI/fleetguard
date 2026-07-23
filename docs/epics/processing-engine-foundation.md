# Epic: Processing Engine Foundation

## Overview
The Processing Engine Foundation introduces an orchestration layer that sits between the Event Dispatcher and the Business Domains. It is a **Platform Service** (not a Business Domain) responsible for executing Verified Operational Events across the relevant Business Domains while tracking execution status, logging, and catching domain-level exceptions.

## Architecture

This engine strictly adheres to the established event-driven architecture by utilizing the existing `EventDispatcher` → `EventSubscriber` pattern.

### 1. Processing Engine Subscriber
The entry point from the dispatcher. It subscribes to all events, filters out unverified ones (processing only `VERIFICATION_STATUS == VERIFIED`), opens an isolated database session, and delegates to the `ProcessingEngine`.

### 2. Processing Engine (Orchestrator)
The orchestrator that wraps execution. It manages the `ProcessingRecord` lifecycle (PENDING → PROCESSING → COMPLETED/FAILED), measures execution time, and ensures that a failure in one domain does not prevent execution in other domains.

### 3. Domain Router
A declarative registry that maps `EntityType` to one or more `DomainService` factories. This router guarantees the engine has zero knowledge of domain business rules and simply provides instances of the appropriate domain services for a given event.

### 4. Processing Record Model
A persistent SQL table (`processing_records`) storing the exact lifecycle of an event through the engine, including timestamped states and a JSON list of `domains_invoked` and `domains_failed` for easy auditability.

## Responsibilities Maintained
- **Orchestration Only:** The Processing Engine has zero business rules.
- **No Direct State Modification:** The engine does not mutate domain tables, it delegates exclusively to `apply_verified_event()`.
- **Easy Extensibility:** To onboard a new domain, we just add one line to the `DomainRouter`.

## Future Extensions
- **Retry Infrastructure:** Because `ProcessingRecord` tracks `FAILED` domains and exceptions, a future worker can easily re-run failed events without re-running successful domains.
- **Asynchronous Workers:** This foundation decouples the execution from the router, preparing the platform for a smooth migration to Celery, Kafka, or RabbitMQ by simply changing the `EventSubscriber` implementation.
