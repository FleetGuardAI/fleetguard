# Milestone 2D — Generic Intelligence Core Implementation Report

## 1. Files Created
- `backend/infrastructure/intelligence/core/contracts.py`: Contains `MetricObservation` generic dataclass, `DirectionStrategy`, and `SeverityStrategy` interfaces.
- `backend/infrastructure/intelligence/core/baseline.py`: Contains `GenericBaselineEngine` with pure mathematical median calculation.
- `backend/infrastructure/intelligence/core/anomaly.py`: Contains `GenericAnomalyEngine` with pure mathematical relative deviation calculation.
- `backend/tests/intelligence/core/test_generic_baseline.py`: Unit tests for generic baseline logic.
- `backend/tests/intelligence/core/test_generic_anomaly.py`: Unit tests for generic anomaly logic.

## 2. Files Modified
- `backend/infrastructure/intelligence/fuel_domain/baseline/engine.py`: Adapted `FuelBaselineEngine` to compose `GenericBaselineEngine` instead of duplicating mathematical logic.
- `backend/infrastructure/intelligence/fuel_domain/anomaly/engine.py`: Adapted `FuelAnomalyEngine` to compose `GenericAnomalyEngine`, and introduced `FuelDirectionStrategy` and `FuelSeverityStrategy`.

## 3. Generic Contracts
- `MetricObservation` completely isolates the core from `DerivedFuelMetric` SQLAlchemy ORM.
- `DirectionStrategy` abstracts whether higher numbers are "better" or "worse".
- `SeverityStrategy` abstracts thresholds (e.g. at what deviation % is it a WARNING vs CRITICAL).

## 4. Generic Baseline Design
The `GenericBaselineEngine` is stateless and accepts a `List[MetricObservation]`. It enforces finite math (strips NaN/Infinity) and minimum sample constraints before calculating the median. It does not enforce domain constraints (like removing ESTIMATED data), leaving that to the domain wrapper.

## 5. Generic Anomaly Design
The `GenericAnomalyEngine` takes an `observed_value` and a `baseline_value`. It computes `(observed - baseline) / baseline * 100`, rounded to 4 decimals exactly as Fuel V1 did. It delegates to the injected strategies to determine direction and severity.

## 6. Fuel Adapter/Composition Design
- `FuelBaselineEngine` still performs the DB fetch and fuel-specific filtering (removing `MeasurementType.ESTIMATED` and low-quality data). It maps the filtered records to `MetricObservation` and calls the `GenericBaselineEngine`.
- `FuelAnomalyEngine` implements `FuelDirectionStrategy` (where positive deviation is an IMPROVEMENT) and `FuelSeverityStrategy` (reading thresholds from settings).

## 7. Mathematical Equivalence Results
The mathematical equivalence is verified by the Fuel regression tests.
Old Fuel Baseline = FuelBaselineEngine + GenericBaselineEngine
Old Fuel Anomaly = FuelAnomalyEngine + GenericAnomalyEngine
All deviations, severities, and baseline output results are mathematically identical to V1.

## 8. Generic Test Results
- **Generic Baseline**: 4/4 tests passed (Median calculation, minimum samples, invalid values like NaN/Inf, and outlier resistance).
- **Generic Anomaly**: 6/6 tests passed (Positive, Negative, Critical, Zero deviation, Invalid baseline, Invalid observation).

## 9. Existing Fuel Regression Results
- `tests/intelligence/test_fuel_baseline_engine.py`: 10/10 tests passed without modification.
- `tests/intelligence/test_fuel_anomaly_engine.py`: 14/14 tests passed without modification.

## 10. Full Regression Results
The complete `pytest tests/ -v` test suite ran successfully. All 30+ tests across `trip`, `routers`, and `intelligence` domains passed with zero failures.

## 11. Database Changes
**NONE.** Alembic migrations and database tables were deliberately left untouched to ensure safety.

## 12. Kafka Changes
**NONE.** The Outbox Consumer still listens on the same topics with the same consumer group.

## 13. API Changes
**NONE.** The Owner Dashboard APIs still output the exact same JSON.

## 14. Frontend Changes
**NONE.**

## 15. Backward Compatibility
The codebase has completely maintained backwards compatibility. No legacy imports, data shapes, or APIs were broken. V1 Fuel Intelligence continues to function identically.

## 16. Known Limitations
- The `FuelFinancialImpactEngine` is still not generalized. It will require a JSONB `domain_context` column migration in a future milestone.
- The `FuelIntelligenceOrchestrator` still hardcodes Fuel intelligence pathways. It must be refactored into a registry-pattern orchestrator in a future milestone.

## 17. Recommended Next Milestone
**Milestone 2E:** Generalize the `FuelIntelligenceOrchestrator` into a `GenericIntelligenceOrchestrator` that uses a Registry Pattern to dispatch events to Domain Handlers (e.g. `FuelHandler`), followed by generalizing `FuelFinancialImpact` to support JSONB contexts for Route and Driver.
