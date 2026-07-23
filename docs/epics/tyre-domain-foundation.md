# Epic: Tyre Domain Foundation

## Overview
The Tyre Domain Foundation establishes an independent Business Domain responsible for managing the complete lifecycle of individual tyres. Tyres are treated as independently tracked business assets, distinct from vehicles and maintenance operations.

## Responsibilities
- Track the lifecycle of tyre events from registration through retirement.
- Maintain independent identity, specifications, and purchase metadata for each tyre.
- Track current vehicle association, position, and status dynamically.
- Maintain a materialized history (`TyreLifecycleRecord`) of significant lifecycle transitions (Installations, Rotations, Repairs, Retreads, and Retirements) for efficient querying without parsing raw operational event logs.

## Entities
- **Tyre**: The Aggregate Root (`tyres` table) capturing physical specifications, current vehicle/position assignment, and status.
- **Tyre Lifecycle Record**: The child entity (`tyre_lifecycle_records` table) capturing the timestamped sequence of major lifecycle operations.
- **Tyre Events**: `TyreRegistered`, `TyreInstalled`, `TyreRemoved`, `TyreRotated`, `TyreRepaired`, `TyreRetreaded`, `TyreRetired`.

## Relationships
- **Tyre-to-Vehicle**: A tyre can belong to a vehicle (when installed) or exist independently (when in storage, repair, or retired).
- **Lifecycle-to-Tyre**: A lifecycle record always belongs to exactly one Tyre.

## Architecture
This domain adheres strictly to the Event-Driven Architecture constraints:
1. **No Write REST APIs**: All state mutations must arrive as verified Operational Events.
2. **Domain Entry Point**: The `TyreService.apply_verified_event(event)` is the only path that alters the domain state in the database.
3. **Read-Only API**: Thin REST routes simply map DB models to Pydantic schemas.

## Files Created
- `models/tyre_domain.py`: The `Tyre` and `TyreLifecycleRecord` ORM entities.
- `schemas/tyre_domain.py`: The `TyreResponse` schema and associated internal Value Objects.
- `repositories/tyre_repository.py`: Isolated data-access operations.
- `services/tyre_service.py`: Business logic and Operational Event handlers.
- `routers/tyre_domain.py`: The `GET` endpoints for tyre state.
- `migrations/versions/..._tyre_domain_foundation.py`: Alembic script initializing the database tables.

## Future Milestones
- **TPMS Integration**: Flowing sensor pressure alerts and real-time metrics.
- **Predictive Tyre Wear**: Machine-learning integrations generating analytics on tyre lifespan based on mileage from the Trip Domain and telematics.
