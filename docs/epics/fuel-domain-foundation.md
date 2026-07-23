# Epic: Fuel Domain Foundation

## Overview
The Fuel Domain Foundation establishes the first pure Business Domain in FleetGuard. It takes verified operational events (which are the single source of truth in the system) and maps them into business state. It owns all business rules regarding fuel level changes, historical fuel data, and current vehicle fuel states.

## Domain Responsibilities
- Maintain the authoritative state of a vehicle's fuel level (`FuelState`).
- Keep a historical ledger of fuel adjustments and fills (`FuelTransaction`).
- Provide READ-ONLY APIs for the presentation layer to query fuel information.
- Translate domain-agnostic `OperationalEvents` into business-specific value objects (`FuelFill`, `FuelAdjustment`) via its service entry point.

## Entities
- **FuelState**: Database table tracking the latest known fuel level of a truck, and the origin (event, sensor, manual) of that state.
- **FuelTransaction**: Database table serving as an append-only ledger for all fuel changes.
- **FuelFill & FuelAdjustment**: Value objects (Pydantic schemas) used internally to structure the business data parsed from an Operational Event.

## Relationships
- A `FuelState` is 1-to-1 with a `Truck`.
- A `FuelTransaction` is N-to-1 with a `Truck`.
- The Fuel Domain translates `OperationalEvent` instances into state, tracking the `origin_id` pointing back to the `OperationalEvent.id` for full audit traceability.

## Architecture
This domain adheres to the Event-Driven Architecture constraints:
1. It does **not** expose write REST APIs (e.g., `POST /api/v1/fuel/fill` is intentionally omitted).
2. All writes must go through the platform's standard Event → Validation → Evidence → Processing pipeline.
3. The domain entry point is `FuelService.apply_verified_event(event)`.

## Files Created
- `models/fuel_domain.py`: `FuelState`, `FuelTransaction`
- `schemas/fuel_domain.py`: Response schemas and Internal Value Objects
- `repositories/fuel_repository.py`: `FuelRepository` for DB interactions
- `services/fuel_service.py`: `FuelService` implementing `apply_verified_event`
- `routers/fuel_domain.py`: Read-only REST endpoints

## Current Limitations
- Calculations like mileage, efficiency, and fuel theft detection are excluded from this milestone.
- Forecasting, AI integration, and Fleet Memory are not yet implemented.
- The `FuelService.apply_verified_event` relies on the downstream Processing Engine (not yet fully wired) to be invoked asynchronously.

## Future Milestones
- **Fuel Inventory & Fuel History**: Exposing more complex views and inventory management.
- **Theft Detection & Efficiency**: Implementing advanced business logic for detecting rapid fuel drops.
- **Processing Engine Integration**: Automatically wiring `apply_verified_event` into a background worker queue or Pub/Sub topic to process validated events at scale.
