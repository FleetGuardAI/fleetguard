# FleetGuard Architecture Document

This document provides a comprehensive reverse-engineered architectural overview of the FleetGuard software system, based exactly on the current state of the codebase.

---

## 1. Overall Architecture

FleetGuard implements a composite architecture drawing heavily from **Domain-Driven Design (DDD)**, **Event-Driven Architecture (EDA)**, and **Clean/Layered Architecture**.

- **Domain-Driven Design (DDD)**: Business logic is encapsulated in isolated aggregates within the `domain` layer (e.g., `domain/vehicle`, `domain/driver`). Aggregates enforce strict invariants (e.g., `VehicleAggregate`, `DriverAggregate`). Each domain owns its models, exceptions, repositories, and logic. 
- **Event-Driven Architecture (EDA)**: The system communicates state changes via immutable Domain Events (e.g., `DriverRegistered`, `VehicleActivated`). The Fleet Intelligence Engine (FIE) consumes `OperationalEvents` from a Kafka event bus (via `infrastructure/events/bus.py` and `kafka_consumer.py`), decoupling data ingestion from intelligence processing.
- **CQRS (Command Query Responsibility Segregation)**: In newer domains (like `driver` and `vehicle`), read operations are segregated from write operations. The `aggregate.py` handles write logic (commands), while a `queries.py` and `projections.py` (e.g., `DriverSummary`) handle read requests for the API/UI.
- **Repository Pattern**: Data access is abstracted behind interfaces (e.g., `BaseVehicleRepository`, `InMemoryDriverRepository`). Currently, many implementations are `InMemory` stubs, but they enforce strict contracts (e.g., append-only rules in `infrastructure/audit/repository.py`).
- **Layered Architecture**: The system separates concerns primarily into `domain/` (core business rules) and `infrastructure/` (external concerns like Kafka, Google Maps, Audit, Notification, and the FIE).

---

## 2. Complete Folder Structure

```text
backend/
├── domain/                      - Core business aggregates and entities
│   ├── device_registry/         - Manages GPS trackers and Fuel sensors mapping to assets
│   ├── document_interpretation/ - Orchestrates OCR and NLP parsing of raw documents
│   ├── driver/                  - Canonical source of truth for driver identity & lifecycle
│   └── vehicle/                 - Canonical source of truth for vehicle identity & lifecycle
├── infrastructure/              - External concerns, integrations, and cross-cutting engines
│   ├── attachments/             - Attachment Framework (Storage, URLs, Metadata)
│   ├── audit/                   - Audit & Activity Framework (Immutable, append-only history)
│   ├── communication/           - Communication Gateway (WhatsApp, SMS, Email abstractions)
│   ├── documents/               - Document Intelligence (Parsing policies, classification)
│   ├── events/                  - Kafka Event Bus, DLQ, Outbox, Serialization
│   ├── evidence/                - Intelligence Evidence generation and linking
│   ├── fuel/                    - Fuel Sensor Gateway (Ingests and normalizes fuel telemetry)
│   ├── gps/                     - GPS Gateway (Ingests and normalizes GPS telemetry)
│   ├── idempotency/             - Deduplication tracking for distributed processing
│   ├── intelligence/            - Fleet Intelligence Engine (FIE - Risk, Checks, Assessments)
│   ├── maps/                    - Maps Service (Reverse Geocoding, Distance, ETA)
│   ├── notifications/           - Notification dispatcher and channels
│   ├── ocr/                     - OCR integrations (Google Cloud Vision/Tesseract stubs)
│   ├── processing/              - Domain Router (Routes operational events to correct FIE domains)
│   ├── scheduler/               - Job Queue, Workers, and Cron job definitions
│   └── validation/              - Rule evaluation and context factories
├── models/                      - Legacy ORM models (SQLAlchemy placeholder definitions)
├── repositories/                - Legacy generic repositories (moving to domain-specific)
├── routers/                     - Legacy API routes
├── schemas/                     - Legacy Pydantic schemas
├── services/                    - Legacy orchestration services
├── tests/                       - Comprehensive test suite mirroring domain/infrastructure
└── migrations/                  - Alembic database migrations
```

---

## 3. Domain Inventory

### Vehicle Management
- **Responsibility**: Canonical source of vehicle identity, specifications, configuration, and lifecycles.
- **Aggregate Root**: `VehicleAggregate`
- **Status**: Complete
- **Models**: `Vehicle`, `VehicleSpecification`, `VehicleConfiguration`
- **Value Objects**: `RegistrationNumber`, `VIN`, `EngineNumber`, `ChassisNumber`
- **Events**: `VehicleRegistered`, `VehicleActivated`, `VehicleRetired`, `VehicleConfigurationChanged`, etc.
- **Components**: `repository.py`, `service.py`, `queries.py`, `projections.py`, `api.py`

### Driver Management
- **Responsibility**: Canonical source of driver identity, employment, and licensing.
- **Aggregate Root**: `DriverAggregate`
- **Status**: Complete
- **Models**: `Driver`, `DriverProfile`, `DriverPreferences`
- **Value Objects**: `EmployeeCode`, `PhoneNumber`, `EmailAddress`, `DriverLicence`
- **Events**: `DriverRegistered`, `DriverSuspended`, `DriverLicenceUpdated`, etc.
- **Components**: `repository.py`, `service.py`, `queries.py`, `projections.py`, `api.py`

### Device Registry & Mapping
- **Responsibility**: Central registry for GPS and fuel sensors, mapping them to canonical assets.
- **Status**: Complete (Framework implemented)

### Document Interpretation
- **Responsibility**: Coordinates extracting structured data from raw attachments via OCR.
- **Status**: Complete (Framework implemented)

### Partial / Placeholder Legacy Domains (found in `models/`)
- **Trip**: Planned (Models exist: `trip_domain.py`)
- **Fuel**: Planned (Models exist: `fuel_domain.py`, `fuel_log.py`)
- **Maintenance**: Planned (Models exist: `maintenance_domain.py`)
- **Tyre**: Planned (Models exist: `tyre_domain.py`)
- **Expense**: Planned (Models exist: `expense_domain.py`)
- **Asset**: Planned (Models exist: `asset_domain.py`)
- **User / Organization**: Placeholder (Models exist: `user.py`, `company.py`)

---

## 4. Infrastructure Inventory

- **Communication Gateway** (`infrastructure/communication`): Abstract factory for sending multi-channel messages (WhatsApp, Email, SMS). Extensible via base channel classes.
- **Attachment Framework** (`infrastructure/attachments`): Manages uploading, securing, and generating presigned URLs for media files.
- **GPS Gateway** (`infrastructure/gps`): Standardizes raw vendor telemetry into normalized `GPSPosition` models.
- **Fuel Gateway** (`infrastructure/fuel`): Normalizes raw hardware fuel readings, preserving unit types (litres, ADC, percentage).
- **Maps Service** (`infrastructure/maps`): Generic wrapper over Google Maps APIs (ETA, Geocoding).
- **Notification Service** (`infrastructure/notifications`): Dispatcher for domain-agnostic system notifications.
- **Scheduler** (`infrastructure/scheduler`): Background worker engine using in-memory queues and delayed execution patterns.
- **Audit** (`infrastructure/audit`): Strictly append-only repository. Logs immutable `AuditRecord`s tied together by `correlation_id`s.
- **Events** (`infrastructure/events`): Kafka integration, Outbox publisher pattern, Dead Letter Queue (DLQ), and JSON serialization.

---

## 5. Intelligence Architecture (FIE)

The **Fleet Intelligence Engine (FIE)** is the central nervous system located at `infrastructure/intelligence/`.

**Pipeline Flow:**
1. **Event Ingestion**: `infrastructure/events/kafka_consumer.py` ingests `OperationalEvent`s (e.g., GPS ticks, Fuel logs).
2. **Domain Router** (`infrastructure/processing/domain_router.py`): Examines the event type and routes it to specific Intelligence Domains (Route, Fuel, Tyre, Maintenance, Driver, Compliance).
3. **Checks** (`checks/`): Simple Boolean logic evaluators (e.g., `RouteDeviationCheck`). Generates `Evidence`.
4. **Assessments** (`assessments/`): Aggregates multiple `Evidence` items to determine a severity score.
5. **Domain Risk Engine** (`domain_risk/`): Calculates a 0-100 normalized risk score for a specific domain based on the Assessments.
6. **Cross-Domain Analyzers** (`cross_domain/`): Complex evaluators looking at multiple domains at once (e.g., `RouteFuelAnalyzer` comparing route steepness to fuel burn rate).
7. **Global Decision & Fleet Health**: Rolls up all Domain Risks into a single global entity health score.
8. **Orchestrator** (`orchestrator/`): Coordinates this entire asynchronous DAG.

---

## 6. Event Flow

**Example: Hardware GPS Pipeline**
```
Vendor Webhook (Payload)
↓
GPS Gateway (Normalizes to GPSPosition)
↓
Event Pipeline (Emits PositionRecorded OperationalEvent)
↓
Kafka Consumer (Picks up PositionRecorded)
↓
Domain Router (Routes to Route Domain)
↓
Overspeed Check (Evaluates speed vs Map Service limit)
↓ (Generates Evidence if violated)
Route Assessment (Calculates severity of violation)
↓
Route Risk Engine (Increases Route Risk Score)
↓
Global Decision Engine (Updates Vehicle Health)
```

**Example: Document Receipt Pipeline**
```
Upload via Attachment Framework
↓
Document Interpretation (OCR + NLP)
↓
Document Processed OperationalEvent
↓
Kafka Consumer
↓
Compliance Domain Router
↓
Expiry Check (Validates document expiry date)
```

---

## 7. Data Flow

- **Telemetry (GPS/Fuel)**: High-frequency data enters via Infrastructure Gateways, normalizes, fires an `OperationalEvent`, and drops into the Intelligence Engine. It does NOT hit Domain aggregates directly.
- **Business Entities (Vehicle/Driver)**: CRUD operations flow through `api.py` -> `service.py` -> `aggregate.py` -> `repository.py`. Read operations bypass aggregates via `queries.py` to `projections.py`.
- **Background Jobs**: Handled by `infrastructure/scheduler`. Jobs are queued in an `InMemoryJobQueue` and processed asynchronously by `JobWorker`.

---

## 8. Package-by-Package Analysis

- **`domain/vehicle`**: Canonical Vehicle ownership. Uses CQRS and Aggregates. Dependent only on Pydantic/Standard lib. Consumed (in the future) by FIE and Trips.
- **`domain/driver`**: Canonical Driver ownership. Mirrors Vehicle architecture.
- **`infrastructure/audit`**: Enforces system-wide immutability. Consumed by Services to record historical facts.
- **`infrastructure/events`**: Handles distributed messaging. Utilizes the Outbox pattern to guarantee at-least-once delivery.
- **`models/` (Legacy)**: Contains SQLAlchemy ORM models (`Base.metadata`). Currently tightly coupled, acting as placeholders awaiting DDD refactoring.

---

## 9. API Inventory

Currently, the APIs are simulated as internal controller classes (`api.py`) rather than actual FastAPI `@router` definitions, ready to be wired up to an HTTP framework.

**Vehicle API (`domain/vehicle/api.py`)**
- `register_vehicle(RegisterVehicleRequest) -> VehicleResponse`
- `get_vehicle(vehicle_id) -> VehicleResponse`
- `list_organization_vehicles(organization_id) -> List[VehicleResponse]`
- `activate_vehicle(vehicle_id, StateChangeRequest) -> VehicleResponse`

**Driver API (`domain/driver/api.py`)**
- `register_driver(RegisterDriverRequest) -> DriverSummary`
- `get_driver(driver_id) -> DriverSummary`
- `list_organization_drivers(organization_id) -> List[DriverSummary]`
- `suspend_driver(driver_id, StateChangeRequest) -> DriverSummary`

---

## 10. Database Architecture

While actual database implementation is currently stubbed to `InMemory` in the new domains, the legacy ORM models (`models/`) reveal the relational structure:
- **`User`**, **`Company`**: Core multi-tenancy.
- **`Vehicle`**, **`Driver`**: Asset ownership (Currently duplicated in legacy models, being transitioned to the DDD layers).
- **`OperationalEvent`**, **`OutboxEvent`**: Event storage.
- **`Ticket`**: Issue tracking.
- **Immutability Rules**: Event logs, outbox tables, and audit tables are strictly append-only. Repositories in the new domains explicitly omit `delete()` methods.

---

## 11. Domain Events

Generated by Aggregates to signal state changes:
- `VehicleRegistered`: Signals a new canonical vehicle exists.
- `VehicleActivated`: Signals a vehicle is ready for trips.
- `DriverSuspended`: Used to immediately halt assignments.
- `DriverLicenceUpdated`: Triggers compliance re-evaluations.

*Note: Domain Events (internal to bounded contexts) are distinct from Operational Events (system-wide FIE triggers).*

---

## 12. Background Jobs

Handled by `infrastructure/scheduler/`:
- **Trigger**: One-off (`execute_at`) or recurring (`cron_expression`).
- **Handler**: `JobExecutor` protocol.
- **Retry Policy**: Defined per job (`max_retries`, `backoff_strategy`).
- **Queue**: Abstracted `BaseJobQueue` (Currently `InMemoryJobQueue`).
- **Worker**: `JobWorker` pulls from the queue and updates `append-only` `JobExecution` logs.

---

## 13. External Integrations

- **Google Maps** (`infrastructure/maps`): Abstracted via `MapsProvider`.
- **WhatsApp/SMS/Email** (`infrastructure/communication`): Abstracted via `BaseChannel`.
- **OCR** (`infrastructure/ocr`): Abstracted via `OCRProvider` (implementing boundaries for Google Cloud Vision / Tesseract).
- **GPS/Fuel Providers**: Handled via abstract Gateways ensuring no vendor lock-in.

---

## 14. Security Architecture

- **Authentication/Authorization**: Stubs exist in the legacy models (`auth_session.py`, `password_reset_token.py`) but are not currently enforced in the new DDD domains.
- **Middleware**: Expected to handle multi-tenancy (`organization_id` injection), though not explicitly coded in the current DDD routes.
- **Immutability**: True security is maintained via the **Audit Framework**, providing non-repudiable logs of all critical actions.

---

## 15. Design Patterns Used

- **Aggregate Root**: `VehicleAggregate` protects invariants.
- **Value Object**: `RegistrationNumber` and `DriverLicence` self-validate.
- **CQRS**: `DriverQueryService` separates read paths from the `DriverAggregate` write path.
- **Repository**: `BaseVehicleRepository` abstracts database engines.
- **Factory**: `ContextFactory` (in `infrastructure/validation`) builds execution contexts.
- **Outbox Pattern**: `OutboxPublisher` guarantees event delivery to Kafka.

---

## 16. Dependency Graph

- `domain/` is at the core. It depends on nothing outside itself.
- `infrastructure/` depends on standard libraries and external SDKs.
- `infrastructure/intelligence` depends heavily on `infrastructure/events` for trigger mechanics.
- The `api.py` layers depend on `services` and `queries`.
- *Note*: There are currently no circular dependencies because `domain` strictly does not import from `infrastructure`.

---

## 17. Architecture Decision Record

- **Why DDD?** FleetGuard operates in a complex domain. Separating business rules (aggregates) from technical details (ORMs, Kafka) ensures the system can pivot without rewriting business logic.
- **Why Event-Driven Intelligence?** Real-time GPS/Fuel ingestion at high volumes would bottleneck CRUD APIs. By firing `OperationalEvents` onto Kafka, the FIE can scale horizontally and process risk assessments independently of the API serving the frontend.
- **Why CQRS in Domains?** Creating a full aggregate just to render a dropdown list of active drivers in the UI is highly inefficient. Projections (`DriverSummary`) allow lightning-fast dashboard loads.

---

## 18. Missing Pieces

*Based strictly on existing code:*
- **Databases**: All new DDD repositories (`InMemoryVehicleRepository`, `InMemoryDriverRepository`, `InMemoryAuditRepository`) are strictly in-memory dictionaries. SQLAlchemy implementations are missing for the new domains.
- **Routing Framework**: APIs are standard Python classes (`api.py`). FastApi `@app.get` decorators and middleware are missing.
- **Assignments**: The Assignment domain (mapping Drivers to Vehicles to Trips) does not exist yet.
- **External API Integrations**: Google Maps, WhatsApp, and OCR providers are defined as Abstract Base Classes but lack the concrete HTTP implementation logic.

---

## 19. Technical Debt

- **Legacy ORM Models**: `backend/models/` contains a giant web of tightly-coupled SQLAlchemy tables (`trip_domain.py`, `fuel_domain.py`) that violate the new DDD boundaries. They need to be deleted or migrated into their respective domain's `repository` layers.
- **Missing Auth**: Security boundaries are missing from the `api.py` layers.

---

## 20. Testing Coverage

- **What is tested**: Core framework logic. Aggregates (preventing invalid state transitions), duplicate uniqueness checks in Services, Value Object regex validation, and Intelligence DAG pipelines (Checks, Assessments, Cross-Domain logic).
- **What is missing**: Infrastructure boundary tests (Kafka producers/consumers, mock HTTP requests for maps/communication).
- **Organization**: Tests strictly mirror the `backend/` folder structure (e.g., `tests/vehicle`, `tests/intelligence`).

---

## 21. Final Architecture Map

```text
                             +-----------------------+
                             |    REST / HTTP API    |
                             +-----------+-----------+
                                         |
                       +-----------------v-----------------+
                       |         Domain Services           | (CQRS Split)
                       |  (VehicleService, DriverService)  |
                       +---------+---------------+---------+
                                 |               |
                         COMMAND |               | QUERY
                                 |               |
                       +---------v-------+ +-----v-----------+
                       | Aggregate Roots | | Query Services  |
                       | (Write Models)  | | (Projections)   |
                       +---------+-------+ +-----+-----------+
                                 |               |
                       +---------v---------------v---------+
                       |        Domain Repositories        |
                       +-----------------+-----------------+
                                         |
+-------------------+          +---------v---------+
| External Systems  |          |   Database/ORM    |
| (Maps, OCR, SMS)  <----------+ (InMemory stubs)  |
+-------------------+          +-------------------+
                                         |
                                         | (Outbox)
+-------------------+          +---------v---------+          +-----------------------+
| Hardware Gateways |          | Kafka Event Bus   |          |  Audit Framework      |
| (GPS, Fuel)       +----------> (Operational /    +----------> (Immutable History)   |
+-------------------+          |  Domain Events)   |          +-----------------------+
                               +---------+---------+
                                         |
                               +---------v---------+
                               | Fleet Intelligence|
                               | Engine (FIE)      |
                               +-------------------+
```
