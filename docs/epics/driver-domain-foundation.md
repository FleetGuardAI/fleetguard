# Epic: Driver Domain Foundation

## Overview
The Driver Domain Foundation evolves the legacy `Driver` bounded context into a strict Domain-Driven architectural pattern. This domain serves as the authoritative source of truth for driver identity, licensing, contact information, and business status in FleetGuard. Crucially, it has been stripped of analytical and behavioral data (such as risk scores and historical expenses), which are deferred to future intelligence domains.

## Domain Responsibilities
- Maintain authoritative state of driver identity and employment status.
- Track licensing validity and contact numbers for communication routing.
- Provide canonical read models for other services.
- Prevent synchronous state mutations via legacy CRUD APIs.

## Entities
- **Driver**: Database table (`drivers`) tracking the core identity and business status.
- **DriverRegistered, DriverUpdated, DriverLicenseUpdated, DriverStatusChanged**: Internal Value Objects processing canonical payload changes.

## Relationships
- **Driver-to-Tickets**: Drivers submit `Tickets` (Expenses).
- All analytics relationships (Trips, Expense totals) are dynamically computed rather than statically owned by the Driver domain.

## Architecture
This domain adheres to the Event-Driven Architecture constraints:
1. **No Write REST APIs**: The legacy `/drivers` CRUD endpoints (including `POST` and `PATCH`) have been removed.
2. **Event-Driven Mutations**: State changes (hiring, firing, license renewals) must arrive as verified Operational Events.
3. **Domain Entry Point**: The `DriverService.apply_verified_event(event)` is the only path that alters the domain state in the database.

## Files Created / Modified
- `models/driver_domain.py`: `Driver` entity stripped of analytics.
- `schemas/driver_domain.py`: Response schemas and Value Objects.
- `repositories/driver_repository.py`: DB access layer.
- `services/driver_service.py`: Business logic and event handling.
- `routers/driver_domain.py`: Read-only REST endpoints.
- `migrations/versions/..._driver_domain_foundation.py`: Alembic migration dropping legacy fields and generating the new schema properties.

## Future Milestones
- **Driver Intelligence Domain**: Reintroducing Trust Score, Rating, and Driver Behavior analysis as a separate, downstream aggregate that consumes raw events.
- **Trip Domain Foundation**: Handling `total_trips` calculations.
