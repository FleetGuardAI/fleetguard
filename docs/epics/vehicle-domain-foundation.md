# Epic: Vehicle Domain Foundation

## Overview
The Vehicle Domain Foundation transforms the legacy `Truck` bounded context into the authoritative **Vehicle Domain**. This domain owns all core identity and specification data for vehicles within the FleetGuard ecosystem. Like the Fuel Domain, it strictly adheres to the Event-Driven Architecture, relying on Operational Events as the single source of truth for all business state changes.

## Domain Responsibilities
- Maintain authoritative state of a vehicle's identity (Registration/License Plate, VIN, Engine Number).
- Track vehicle specifications (Make, Model, Year, Capacity).
- Track business status (Active, Inactive, Maintenance) and ownership info.
- Handle state mutation via verified Operational Events (e.g., `VEHICLE_ASSIGNED`, `VEHICLE_UPDATED`, `VEHICLE_STATUS_CHANGED`).

## Entities
- **Vehicle**: Database table (`vehicles`) tracking the latest known identity and specifications.
- **VehicleRegistered, VehicleUpdated, VehicleStatusChanged**: Internal Value Objects used as schemas to map incoming event payloads.

## Relationships
- **Vehicle-to-Fuel**: Vehicles are associated with `FuelState` and `FuelTransaction`.
- **Vehicle-to-Tickets**: Vehicles have a one-to-many relationship with `Ticket`.
- All legacy references to `Truck` have been structurally migrated to `Vehicle`, preserving data integrity and existing primary keys.

## Architecture
This domain adheres to the Event-Driven Architecture constraints:
1. It exposes **no write REST APIs** (the legacy `/trucks` CRUD endpoints have been removed).
2. All updates to vehicle identity or status must arrive via the platform's standard Event → Validation → Evidence → Processing pipeline.
3. The domain entry point is `VehicleService.apply_verified_event(event)`.

## Files Created / Modified
- `models/vehicle_domain.py`: `Vehicle` entity (replaced `truck.py`).
- `schemas/vehicle_domain.py`: Response schemas and Internal Value Objects (replaced `truck.py`).
- `repositories/vehicle_repository.py`: DB interactions for vehicles.
- `services/vehicle_service.py`: Implementing `apply_verified_event`.
- `routers/vehicle_domain.py`: Read-only REST endpoints.
- `migrations/versions/..._rename_truck_to_vehicle.py`: Alembic migration to safely rename tables and columns preserving all data.

## Future Milestones
- **Processing Engine Integration**: Automatically wiring `apply_verified_event` into a background worker queue or Pub/Sub topic to process validated events at scale.
- **Driver Domain Foundation**: Establishing the relationships and assignment logic between the incoming Driver Domain and this Vehicle Domain.
