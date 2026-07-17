# Epic: Trip Domain Foundation

## Overview
The Trip Domain Foundation establishes a brand-new Business Domain inside FleetGuard. It serves as the authoritative source of truth for trip states, assignments, distances, and execution tracking.

## Responsibilities
- Maintain authoritative state of Trip identity and lifecycle.
- Track planned versus actual distances and execution timestamps.
- Manage logical associations between a trip, a vehicle, and a driver.
- Consume and apply Operational Events sequentially to evolve trip state.

## Entities
- **Trip**: Database table (`trips`) tracking the core lifecycle and assignments of a trip.
- **Trip Events**: `TripCreated`, `TripStarted`, `TripPaused`, `TripResumed`, `TripCompleted`, `TripCancelled`, `TripDriverAssigned`, `TripVehicleAssigned`.

## Relationships
- **Trip-to-Vehicle**: Belongs to one Vehicle.
- **Trip-to-Driver**: Belongs to one Driver.
- *Note:* The domain conceptually separates Assignment from Trip logic, although it consumes the assignment events. Assignment logic might be broken out into an independent Assignment Domain in future iterations.

## Architecture
This domain adheres strictly to the Event-Driven Architecture constraints:
1. **No Write REST APIs**: All state mutations must arrive as verified Operational Events.
2. **Domain Entry Point**: The `TripService.apply_verified_event(event)` is the only path that alters the domain state in the database.
3. **Read-Only API**: Thin REST routes simply map DB models to Pydantic schemas.

## Files Created
- `models/trip_domain.py`: The `Trip` ORM entity.
- `schemas/trip_domain.py`: The `TripResponse` schema and associated internal Value Objects.
- `repositories/trip_repository.py`: Isolated data-access operations.
- `services/trip_service.py`: Business logic and Operational Event handlers.
- `routers/trip_domain.py`: The `GET` endpoints for trip state.
- `migrations/versions/..._trip_domain_foundation.py`: Alembic script initializing the `trips` schema.

## Future Milestones
- **Assignment Domain**: Possible extraction of driver-vehicle-trip matchmaking logic.
- **GPS Tracking**: Realtime routing overlays on top of active trips.
- **Analytics/ETA Prediction**: Machine learning modules calculating dynamic ETAs over the trip's planned distance.
