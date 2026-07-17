# Expense Domain Foundation

## Overview
The Expense Domain is the authoritative source of truth for all financial records generated from fleet operations. It acts purely as a financial projection ledger and does not own any operational state. This domain follows the strict read-only / event-driven architecture established by previous domains (Vehicle, Driver, Trip, Maintenance, Tyre, Asset).

## Responsibilities
- **Expense Recording**: Create financial records based on verified operational events.
- **Financial Status**: Track the status of expenses (e.g., `RECORDED`, `CANCELLED`).
- **Read APIs**: Provide read-only endpoints for downstream systems, dashboards, and analytical consumers.

## Aggregate Root
**`Expense`** is the Aggregate Root.
- Represents a single financial transaction.
- Contains all required financial properties (`amount`, `currency`, `category`, `status`, `expense_date`).
- References related operational entities (like `vehicle_id`, `driver_id`, `trip_id`, `maintenance_id`) via foreign keys, but does not own them. 
- Deep relationships via ORM are omitted in favor of explicit IDs to decouple the Expense Domain from the rest of the system.

## Relationships
The Expense Domain maintains loose coupling by referencing external entities:
- `Vehicle` (Optional)
- `Driver` (Optional)
- `Trip` (Optional)
- `MaintenanceRecord` (Optional)

## Architecture
The Expense Domain strictly adheres to the established Event-Driven Architecture:
- **Models**: Defines the `Expense` aggregate root and the enum states.
- **Repository**: Handles all read/write persistence for Expenses.
- **Service**: Implements `apply_verified_event()`, listening specifically to `EXPENSE_RECORDED`, `EXPENSE_UPDATED`, and `EXPENSE_CANCELLED` events.
- **Router**: Exposes thin, read-only `GET` endpoints (`/expenses`, `/vehicles/{id}/expenses`, etc.).
- **Write Path**: Zero `POST`/`PATCH` endpoints exist. The only way to mutate the Expense database is by publishing an `OperationalEvent`.

## Legacy Integration Strategy
Currently, driver-submitted expenses are tracked via the legacy `Ticket` model (handled by `routers/tickets.py`). To avoid Duplicate Database Ownership during this foundational milestone, we applied a strategic bridge:
- `Ticket` is now reclassified as a "Submission Workflow / Inbox".
- When a `Ticket` is approved via the legacy API, the router emits an `EXPENSE_RECORDED` Operational Event.
- The Processing Engine routes this event to the `ExpenseService`, which creates the authoritative `Expense` ledger record.
- In a future milestone (Architecture Cleanup), the legacy Ticket implementation can be fully deprecated.

## Files Created
- `models/expense_domain.py`
- `repositories/expense_repository.py`
- `schemas/expense_domain.py`
- `services/expense_service.py`
- `routers/expense_domain.py`
- `migrations/versions/20260716_1621_8569eb5c85cd_expense_domain_foundation.py`
- Modified: `models/__init__.py`, `schemas/__init__.py`, `main.py`, `processing/domain_router.py`, `routers/tickets.py`

## Future Extensions
- **Architecture Cleanup**: Full deprecation of `Ticket` in favor of direct driver interactions via operational events (e.g., `EXPENSE_REQUESTED`).
- **External Integration**: Export endpoints for accounting software (e.g., Xero, QuickBooks).
- **Advanced Filtering**: Filtering APIs by amount threshold, time ranges, and custom tags.
