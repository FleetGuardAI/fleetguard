# Evidence Orchestrator Architecture

## Overview
The **Evidence Orchestrator** is an Infrastructure Service responsible for coordinating the collection of corroborating data (evidence) for Operational Events. It acts as the bridge between Operational Events ingestion and the Validation Engine.

Crucially, the Evidence Orchestrator **does not validate evidence** and **owns no business logic**. Its sole responsibility is to trigger providers, aggregate their outputs into an `EvidencePackage`, and declare that package ready for evaluation.

## Responsibilities
- Listen to specific Operational Events (e.g., `FUEL_FILLED`, `DOCUMENT_UPLOADED`).
- Identify applicable **Evidence Providers** dynamically using an `EvidenceProviderRegistry`.
- Execute all applicable providers concurrently.
- Enforce provider timeouts.
- Construct the final `EvidencePackage` summarizing the collection effort.
- Emit an `EVIDENCE_PACKAGE_READY` Operational Event.

## Evidence Collection Flow
1. An Operational Event is created in a `PENDING` state and published to Kafka.
2. The Evidence Orchestrator (a Kafka consumer) picks up the event.
3. The Orchestrator queries the `EvidenceProviderRegistry` via `get_applicable_providers(event)`.
4. Applicable providers are triggered concurrently using `asyncio.gather`.
5. Providers run their specific logic (e.g., calling OCR endpoints, querying GPS gateways). They save successful data as `Evidence` records in the database.
6. The Orchestrator aggregates the results (`COMPLETED`, `FAILED`, `TIMED_OUT`) using the `EvidencePackageBuilder`.
7. The Orchestrator creates an `EVIDENCE_PACKAGE_READY` Operational Event and publishes it to unblock the Validation Engine.

## Evidence Package Structure
The resulting `EvidencePackage` is passed as the payload of the `EVIDENCE_PACKAGE_READY` event. It contains:
- `event_id`: The UUID of the parent Operational Event.
- `expected_providers`: List of providers triggered.
- `completed_providers`: List of providers that successfully collected evidence.
- `failed_providers`: List of providers that encountered an internal error.
- `timed_out_providers`: List of providers that exceeded their execution window.
- `collected_evidence`: List of `Evidence` UUIDs successfully persisted to the database.
- `collection_status`: `COMPLETED`, `PARTIAL`, or `FAILED`.

## Provider Registration
Providers must implement the `BaseEvidenceProvider` interface, which requires:
- `name`: A unique string identifier.
- `applies_to(event)`: A fast check to determine if the provider should run for this event.
- `provide_evidence(event)`: The core logic returning a `ProviderResult`.

Providers are registered at application startup in `main.py` via the `EvidenceProviderRegistry`.

## Failure Handling
The Orchestrator implements a strict timeout mechanism (`asyncio.wait_for`).
- **Timeouts**: If a provider exceeds the configured window (e.g., 10 seconds), the task is cancelled, and the provider is appended to `timed_out_providers`.
- **Exceptions**: If a provider raises an unhandled exception, it is caught by the Orchestrator, logged, and the provider is appended to `failed_providers`.
- The Orchestrator itself **never crashes** due to a provider failure. It completes the collection cycle and emits a `PARTIAL` or `FAILED` `EvidencePackage`. The Validation Engine decides if partial evidence is sufficient to verify the event.

## Future Extension Strategy
Adding new evidence sources (e.g., a GPS Telemetry provider) requires zero modifications to the Orchestrator. You simply:
1. Create a new class implementing `BaseEvidenceProvider`.
2. Register it with the `EvidenceProviderRegistry` in `main.py`.
The Orchestrator will automatically trigger it for applicable events.
