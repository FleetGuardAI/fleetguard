# Trip Management Domain: Queries and Projections

## CQRS Strategy
Command Query Responsibility Segregation (CQRS) is heavily employed in the Trip domain. 
- **Commands** (creating, starting, pausing) are strictly executed by the `TripAggregate` via the internal `TripService`, triggered solely by Operational Events. 
- **Queries** (listing active trips, fetching metrics) are handled completely independently by the `TripQueryService`.

### Why CQRS?
1. **Performance:** A fleet operations dashboard rendering 1,000 active trips does not need the heavy domain validations used during a trip lifecycle mutation. Querying read models is orders of magnitude faster.
2. **Coupling:** The frontend UI can evolve its data requirements (e.g., grouping trips by region) without forcing changes onto the core `TripAggregate`.

## Projection Models
Projections are flat, read-optimized `pydantic` models representing subsets of Trip data.

### `TripSummary`
Base projection omitting deep coordinates and metadata to optimize payload sizes.

### `ActiveTripSummary`
A specialized projection that inherently filters for `TripStatus.IN_PROGRESS`.

### `DriverTripSummary`
A projection optimized for Driver App UIs, surfacing only trips associated with a specific `driver_assignment_id`.

## Read Model Generation
In the current implementation, read models are derived synchronously from the primary `TripRepository` in memory. As the system scales to millions of trips, CQRS allows us to eventually persist these projections into a separate, denormalized read-database (e.g., Elasticsearch or a specific Postgres materialized view) by subscribing to the `TripDomainEvents` emitted by the Aggregate.
