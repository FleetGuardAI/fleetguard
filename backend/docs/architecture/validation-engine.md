# Validation Engine Architecture

## Overview
The **Validation Engine** is an Infrastructure Service in FleetGuard responsible for determining the trustworthiness of an Operational Event. It operates solely by evaluating an `EvidencePackage` (prepared by the Evidence Orchestrator) against a suite of pluggable Validation Rules.

Crucially, the Validation Engine **does not gather evidence** and **owns no business logic**. It purely assesses data consistency, rule satisfaction, and evidence completeness to produce a trust decision.

## Responsibilities
- Listen to `EVIDENCE_PACKAGE_READY` Operational Events.
- Load the original Operational Event and its associated Evidence records from persistent storage.
- Execute all applicable **Validation Rules** concurrently or sequentially.
- Compute a final `ValidationResult` containing a verdict (`VERIFIED`, `REJECTED`, or `DISPUTED`).
- Emit a new Operational Event (`VALIDATION_SUCCEEDED`, `VALIDATION_FAILED`, or `VALIDATION_DISPUTED`) indicating the result.

## Evidence Evaluation Flow
1. The **Validation Consumer** receives an `EVIDENCE_PACKAGE_READY` event.
2. The **Validation Service** extracts the `EvidencePackage` from the payload and the original event ID (`entity_id`).
3. The Service fetches the original Operational Event and all its associated `Evidence` records from the database.
4. The **Validation Engine** determines which Validation Rules apply via the `ValidationRuleRegistry`.
5. The Engine calls `evaluate()` on each applicable rule.
6. Rule outcomes (`RuleResult`) are aggregated. If any rule fails, the event is REJECTED. If rules crash or evidence is missing, the event is DISPUTED. Otherwise, it is VERIFIED.
7. The Service creates a new Operational Event (e.g., `VALIDATION_SUCCEEDED`) containing the `ValidationResult` in its payload.

## Validation Rules
A Validation Rule (`BaseValidationRule`) is a stateless, single-responsibility evaluator.
- `applies_to(event, package)`: Determines if the rule should run.
- `evaluate(event, package, evidence_records)`: Performs the logic and returns a `RuleResult` (pass/fail, score, reasons).

Rules are decoupled from the engine and registered at startup in `main.py`.

## Generated Events
To strictly maintain the invariant **"Persist Event -> Publish Event"** without mutating historical data, the Validation Engine creates *new* Operational Events:
- `VALIDATION_SUCCEEDED`: Emitted when `verdict == VERIFIED`.
- `VALIDATION_FAILED`: Emitted when `verdict == REJECTED`.
- `VALIDATION_DISPUTED`: Emitted when `verdict == DISPUTED`.

Downstream systems (like the Processing Engine) will listen for these events to trigger business domain updates.

## Future Extension Strategy
To add a new validation constraint (e.g., checking if GPS coordinates match a known fueling station):
1. Create a new class extending `BaseValidationRule`.
2. Implement the evaluation logic using the provided `evidence_records`.
3. Register the rule in `main.py` via `ValidationRuleRegistry.register()`.
The engine will automatically include the new rule in its evaluation pipeline.
