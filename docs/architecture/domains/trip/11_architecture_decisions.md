# Trip Management Domain: Architecture Decisions (ADR)

## 1. Why Trip is Event-Driven
Trips represent physical realities happening on the road. In an enterprise system, physical realities cannot be managed by simple CRUD APIs, because an API relies on a human or proxy choosing to invoke it correctly. An Event-Driven Architecture ensures that when telematics hardware records an engine turning on, the software *reacts* and derives the Trip state autonomously.

## 2. Why Operational Events are the Source of Truth
We separate the "raw fact" (Operational Event: Ignition Started) from the "business interpretation" (Domain Entity: Trip In Progress). By making Operational Events the ultimate source of truth, we can replay history to regenerate corrupted trip data, or implement entirely new Intelligence rules retroactively. 

## 3. Why Lifecycle APIs do NOT exist
Exposing a `POST /trips/start` API alongside an event-driven processor creates a dangerous dual-write scenario. If a driver clicks "Start" on a tablet (invoking the API), but the vehicle's engine is off, which state is correct? 
By entirely eliminating mutation APIs, we force all clients (even frontend tablets) to submit an `OperationalEvent Create` request. The event stream remains the single bottleneck and single source of truth.

## 4. Why CQRS was chosen
The rules governing a valid trip transition are complex (Aggregate). The data required to render a UI dashboard of 5,000 trucks is flat and wide (Read Model). Using the same ORM model for both guarantees performance bottlenecks. CQRS completely separates them.

## 5. Why the Event Handler exists
The Aggregate contains pure business logic and does not know what Kafka or an Operational Event is. The Event Handler acts as the Anti-Corruption Layer, translating raw infrastructure bytes into typed Python domain commands.

## 6. Why the Aggregate does not receive HTTP requests
Aggregates are pure domain components. Receiving an HTTP request implies knowledge of headers, status codes, and JSON serialization. The `TripService` (and API Router) shield the Aggregate from web infrastructure, ensuring the core domain is testable in total isolation.
