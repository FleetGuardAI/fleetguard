# Fuel Transaction Intelligence

This document outlines the first concrete implementation of the Fleet Intelligence Engine for the **Fuel Domain**.

## Overview
The Fuel Transaction Intelligence pipeline evaluates a single fuel filling transaction to determine its business risk based purely on available evidence. The pipeline extends the 5-Tier intelligence architecture without modifying the underlying framework.

## Business Objective
Determine whether a fuel transaction appears legitimate by cross-referencing available physical facts:
- Does the receipt quantity match the telematics fuel sensor increase?
- Was the truck physically at the fuel station when the transaction occurred?
- Do the timestamps of the receipt, GPS, and CAN bus sensor align?
- Is it physically possible to fit the receipted fuel quantity into the vehicle's remaining tank capacity?

## Execution Flow

1. **Evidence Collection**: The pipeline ingests immutable `ReceiptEvidence`, `GPSEvidence`, `FuelSensorEvidence`, and `VehicleEvidence`.
2. **Checks**: Four isolated, deterministic checks execute concurrently.
3. **Assessment**: The `FuelTransactionIntegrityAssessment` groups check results into objective findings.
4. **Risk Profile**: The `FuelTransactionRiskEngine` quantifies business risk (LOW, HIGH, CRITICAL) based on the findings.
5. **Decision**: The `FuelDecisionEngine` dictates the final policy (APPROVE, REVIEW_REQUIRED, REJECT) based on the risk profile.

## Checks

### FuelQuantityCheck (`fuel.quantity_match`)
Compares the Receipt's reported quantity against the vehicle's CAN bus fuel sensor increase. Allows a configurable tolerance (e.g., `5.0L`).

### FuelLocationCheck (`fuel.location_match`)
Verifies the vehicle's GPS coordinates are within a configurable radius (e.g., `100.0m`) of the fuel station coordinates.

### FuelTimingCheck (`fuel.timing_match`)
Ensures the timestamps from the receipt, GPS, and fuel sensor fall within a permitted time window (e.g., `1800` seconds).

### FuelTankCapacityCheck (`fuel.tank_capacity`)
Verifies that the `Previous Fuel Level` + `Receipt Quantity` does not exceed the vehicle's max `Tank Capacity` (plus a small tolerance).

## Assessment Logic
**`FuelTransactionIntegrityAssessment` (`fuel.transaction_integrity`)**
Evaluates the execution results of the required checks. If any required check is missing (due to missing evidence) or fails due to an exception, the assessment yields `INCONCLUSIVE`. Otherwise, it maps check failures into specific "Integrity Mismatch" findings. If all checks pass, it yields an "Integrity OK" finding.

## Risk Logic
**`FuelTransactionRiskEngine` (`fuel.transaction_risk`)**
- **LOW Risk**: The assessment reports perfect integrity.
- **HIGH Risk**: The assessment detected exactly one integrity mismatch.
- **CRITICAL Risk**: The assessment detected multiple integrity mismatches.

## Recommendation Logic
**`FuelDecisionEngine` (`fuel.transaction_decision`)**
- **LOW Risk** ➡️ `APPROVE`
- **MEDIUM Risk** ➡️ `APPROVE_WITH_REVIEW`
- **HIGH Risk** ➡️ `REVIEW_REQUIRED`
- **CRITICAL Risk** ➡️ `REJECT`

## Explainability
The pipeline guarantees a mathematically unbroken traceability tree. A final `Recommendation` object natively embeds the `DomainRiskProfile`, which embeds the `AssessmentResult`, which embeds the `CheckResult`s, which contain the exact UUIDs of the raw `Evidence`. This provides 100% transparent context for every automated decision.

## Configuration
Business thresholds are decoupled from business logic via the `FuelIntelligenceConfig`:
- `quantity_tolerance_liters`
- `location_radius_meters`
- `timing_window_seconds`
- `tank_capacity_tolerance_liters`

## Testing Strategy
The Fuel Domain features extensive testing coverage:
- **Unit Tests**: Isolated testing of every Check, Assessment, Risk Engine, and Decision Engine (`tests/intelligence/fuel_domain/`).
- **Integration Tests**: End-to-end pipeline verification (`test_fuel_intelligence_pipeline.py`) simulating valid transactions, single mismatches, multiple mismatches, and missing evidence.

## Extension Guide
To add new logic to the fuel domain:
1. Define a new `BaseCheck` in `checks/`.
2. Add the check key to the `FuelTransactionIntegrityAssessment` required or optional checks.
3. Update unit tests.
4. Verify the end-to-end pipeline still passes.
