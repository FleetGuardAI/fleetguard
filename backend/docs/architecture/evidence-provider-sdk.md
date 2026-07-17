# Evidence Provider SDK Architecture

The FleetGuard Evidence Provider SDK enables rapid, standardized integration of diverse data sources (OCR pipelines, GPS hardware, telematics APIs, etc.) into the FleetGuard Operational Event lifecycle, without requiring any modifications to the core `EvidenceOrchestrator`.

## Design Philosophy

- **Decoupled Architecture**: Providers are pure adapters. They communicate with external systems and translate the raw data into standard FleetGuard schemas.
- **Stateless Operation**: Providers perform *no* database writes. The persistence of evidence is completely managed by the central orchestrator to guarantee transactional consistency and schema enforcement.
- **Unified Interface**: All providers implement the exact same `BaseEvidenceProvider` plugin interface, ensuring the registry can scale to dozens of plugins without bloated switch statements.

## The SDK Contract

### 1. The Request (`EvidenceRequest`)
Every provider receives an `EvidenceRequest` containing:
- The `OperationalEvent` triggering the flow.
- A `context` dictionary holding system state.
- Provider-specific dynamic `configuration`.
- `attachments` (like document metadata).

### 2. The Result (`EvidenceResult`)
Providers must return an `EvidenceResult` containing:
- `status`: `COMPLETED`, `FAILED`, or `TIMED_OUT`.
- `evidence_type`: The category of the data (e.g. `OCR_EXTRACTION`, `GPS_PING`).
- `raw_data`: The schema-less raw dictionary representing the actual evidence (never a database ID).
- `confidence`: Heuristic accuracy rating.

### 3. The Plugin Lifecycle
To build a new Evidence Provider, developers implement `BaseEvidenceProvider`:
1. `initialize()`: Prepare internal clients or connections.
2. `health()`: Ensure the provider's external dependency is reachable.
3. `validate_configuration(config)`: Verify any dynamic configuration.
4. `applies_to(request)`: Synchronously evaluate if the provider should collect evidence for the given request.
5. `collect(request)`: The core async data collection method. Executes external I/O and returns the `EvidenceResult`.
6. `shutdown()`: Clean up resources.

## Registration & Execution Flow

1. **Registration**: At startup, `main.py` instantiates providers (e.g., `OCREvidenceProvider`) and registers them in the `EvidenceProviderRegistry`.
2. **Orchestration**: When an event (e.g., `DOCUMENT_UPLOADED`) arrives:
    - The `EvidenceOrchestrator` constructs the `EvidenceRequest`.
    - It iterates over the registry, asking each provider `applies_to(request)`.
    - It runs `collect(request)` concurrently for all applicable providers, wrapped in a strict timeout.
3. **Persistence**: The orchestrator receives the returned `EvidenceResult` payloads, passes the `raw_data` to the `EvidenceService` for secure database persistence, retrieves the generated `evidence_id`, and attaches it to the final `EvidencePackage`.
