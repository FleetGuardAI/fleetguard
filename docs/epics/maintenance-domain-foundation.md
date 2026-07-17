# Epic: Maintenance Domain Foundation

## Overview
The Maintenance Domain Foundation is a brand-new Business Domain inside FleetGuard. It serves as the authoritative source of truth for tracking vehicle maintenance lifecycles, capturing both high-level maintenance records and granular maintenance tasks.

## Responsibilities
- Track the lifecycle of maintenance events from creation, scheduling, start, and completion.
- Maintain a structured list of individual maintenance tasks (e.g., oil change, tyre rotation) performed during a maintenance session.
- Track workshop and service provider assignments contextually for future extensibility.
- Consume and apply Operational Events sequentially to evolve maintenance state.

## Entities
- **Maintenance Record**: The Aggregate Root (`maintenance_records` table) capturing overall status, categorization (Preventive, Corrective, etc.), and timing.
- **Maintenance Task**: The child entity (`maintenance_tasks` table) representing specific operations, statuses, and notes belonging to a record.
- **Maintenance Events**: `MaintenanceCreated`, `MaintenanceScheduled`, `MaintenanceStarted`, `MaintenanceCompleted`, `MaintenanceCancelled`, `MaintenanceTaskAdded`, `MaintenanceTaskCompleted`.

## Relationships
- **Maintenance-to-Vehicle**: A maintenance record always belongs to exactly one Vehicle.
- **Task-to-Record**: A task always belongs to exactly one Maintenance Record.

## Architecture
This domain adheres strictly to the Event-Driven Architecture constraints:
1. **No Write REST APIs**: All state mutations must arrive as verified Operational Events.
2. **Domain Entry Point**: The `MaintenanceService.apply_verified_event(event)` is the only path that alters the domain state in the database.
3. **Read-Only API**: Thin REST routes simply map DB models to Pydantic schemas.

## Files Created
- `models/maintenance_domain.py`: The `MaintenanceRecord` and `MaintenanceTask` ORM entities.
- `schemas/maintenance_domain.py`: The `MaintenanceRecordResponse` schema and associated internal Value Objects.
- `repositories/maintenance_repository.py`: Isolated data-access operations.
- `services/maintenance_service.py`: Business logic and Operational Event handlers.
- `routers/maintenance_domain.py`: The `GET` endpoints for maintenance state.
- `migrations/versions/..._maintenance_domain_foundation.py`: Alembic script initializing the database tables.

## Future Milestones
- **Workshop/Provider Domains**: Refactoring the string `workshop` and `service_provider` fields into their own independent authoritative domains.
- **Predictive Maintenance**: Adding machine-learning triggers based on telematics data.
- **Tyre Lifecycle Integration**: Expanding the tyre-specific events to flow into a dedicated Tyre Domain.
