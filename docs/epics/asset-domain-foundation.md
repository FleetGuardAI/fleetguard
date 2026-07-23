# Epic: Asset Domain Foundation

## Overview
The Asset Domain Foundation establishes an independent Business Domain responsible for managing the complete lifecycle of physical hardware assets used by the fleet (e.g., GPS devices, dash cameras, IoT gateways, fuel sensors). Assets are treated as independently tracked business entities, distinct from vehicles and maintenance operations.

## Responsibilities
- Track the lifecycle of hardware assets from registration through retirement.
- Maintain independent identity, specifications, and purchase/warranty metadata for each asset.
- Track current vehicle association, installation status, and operational status dynamically.
- Maintain a materialized history (`AssetHistory`) of significant lifecycle transitions (Installations, Calibrations, Repairs, Replacements, and Retirements) for efficient querying without parsing raw operational event logs.

## Entities
- **Asset**: The Aggregate Root (`assets` table) capturing physical specifications, current vehicle/position assignment, and operational status.
- **Asset History**: The child entity (`asset_history_records` table) capturing the timestamped sequence of major lifecycle operations.
- **Asset Events**: `AssetRegistered`, `AssetInstalled`, `AssetRemoved`, `AssetCalibrated`, `AssetRepaired`, `AssetReplaced`, `AssetRetired`.

## Relationships
- **Asset-to-Vehicle**: An asset can belong to a vehicle (when installed) or exist independently (when in storage, repair, or retired).
- **History-to-Asset**: A history record always belongs to exactly one Asset.

## Architecture
This domain adheres strictly to the Event-Driven Architecture constraints:
1. **No Write REST APIs**: All state mutations must arrive as verified Operational Events.
2. **Domain Entry Point**: The `AssetService.apply_verified_event(event)` is the only path that alters the domain state in the database.
3. **Read-Only API**: Thin REST routes simply map DB models to Pydantic schemas.

## Files Created
- `models/asset_domain.py`: The `Asset` and `AssetHistory` ORM entities.
- `schemas/asset_domain.py`: The `AssetResponse` schema and associated internal Value Objects.
- `repositories/asset_repository.py`: Isolated data-access operations.
- `services/asset_service.py`: Business logic and Operational Event handlers.
- `routers/asset_domain.py`: The `GET` endpoints for asset state.
- `migrations/versions/..._asset_domain_foundation.py`: Alembic script initializing the database tables.

## Future Milestones
- **Telemetry Integration**: Processing streams of real-time telemetry from installed IoT devices and GPS units.
- **Hardware Communication Layer**: Managing low-level MQTT connections to configure devices dynamically.
