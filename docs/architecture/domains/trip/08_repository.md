# Trip Management Domain: Repository

The Trip domain utilizes the Repository pattern to isolate business logic from database infrastructure.

## Interfaces
`BaseTripRepository` defines the contract for persisting the Trip Aggregate.
- `create(trip: Trip)`
- `update(trip: Trip)`
- `find_by_id(trip_id: UUID) -> Optional[Trip]`
- `find_active_trip_for_vehicle(vehicle_id: str) -> Optional[Trip]`

## InMemory Implementation
`InMemoryTripRepository` stores trips in a standard Python dictionary. This is used extensively for rapid unit testing and local development, guaranteeing that domain logic remains totally decoupled from SQL syntax.

## Future SQL Implementation (Milestone)
When transitioning to production, a `PostgresTripRepository` will implement the `BaseTripRepository` interface.
- It will utilize SQLAlchemy's async `AsyncSession`.
- Due to CQRS, we will likely implement specific `SQLTripQueryRepository` components that bypass ORM overhead and execute raw SQL queries to populate projection models directly.

## Transaction Boundaries
A repository operation saves exactly **one Aggregate per transaction**.
The Event Handler opens a Unit of Work (UoW), extracts the Aggregate, invokes business logic, saves the Aggregate, and commits the transaction. Updating a Trip and updating a Driver Assignment simultaneously must never occur within the same repository transaction boundary.
