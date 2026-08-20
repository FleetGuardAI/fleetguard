# Milestone 2H — Generic Intelligence Architecture Audit & V1 Revalidation

## 1. Executive Summary
An exhaustive architectural audit of the FleetGuard generic intelligence pipeline (Milestones 2D-2G) was performed. The generic mathematical core is completely isolated from domain-specific (Fuel) logic and operates successfully on purely agnostic contracts. The event-driven architecture is functionally intact. However, we identified a critical transaction boundary coupling issue between domain handlers, query amplification risks, and legacy intelligence code duplication. The architecture is graded as **V2 READY WITH CONDITIONS**.

---

## 2. Current Architecture
The current architecture strictly adheres to the intended production-compatible design:
`OperationalEvent → Kafka → Consumer → Orchestrator → HandlerRegistry → Fuel Handler → Generic Baseline/Anomaly/Financial/ContributingFactor Engines → Owner API`.
The implementation validates that the generic engines process data cleanly through `MetricObservation` contracts without any direct database coupling.

---

## 3. Duplicate Intelligence Architectures
A repository-wide scan revealed the following duplicate architectures:
*   **A. Active production intelligence:** `FleetIntelligenceService` — Currently wraps the event builder to generate real-time fleet health.
*   **B. Legacy intelligence:** `PredictionService` — Contains static mathematical formulas for Fuel Theft, Driver Safety Scoring, Breakdown Risk (BRI), and Tyre Wear.
*   **C. Duplicate intelligence:** `TripIntelligenceService` — Dynamically computes efficiency scores, profitability, and anomalies for trips on-the-fly rather than utilizing persisted generic intelligence metrics.
*   **E. Presentation-only logic:** Frontend math calculations (detailed in section 17).

*Note: CopilotService securely delegates intelligence logic to FleetIntelligenceService and TripIntelligenceService.*

---

## 4. Operations vs Intelligence Boundary
The boundary is strictly maintained.
*   **Operations Engine (`operational_event_service.py`, `trip_service.py`):** Strictly handles receiving operational input, validation, persisting operational events, and maintaining operational state.
*   **Intelligence Engine (`core/*`):** Handles calculating baselines, detecting anomalies, calculating financial exposure, and ranking contributing evidence.
**Result:** No intelligence logic has accidentally leaked into the Operations Engine.

---

## 5. Generic Core Purity
The `infrastructure/intelligence/core/` directory is genuinely generic.
*   `baseline.py` and `anomaly.py` operate on pure `float` values and `MetricObservation` contracts.
*   `financial.py` generically enforces non-negative constraints and validates mathematical soundness.
*   No SQLAlchemy ORM dependencies, fuel queries, or domain-specific logic exist within the generic core.

---

## 6. Fuel Domain Isolation
Fuel-specific implementation is strictly isolated inside `infrastructure/intelligence/fuel_domain/`.
The `FuelIntelligenceHandler` orchestrates the domain by fetching raw data via the `FuelIntelligenceDataLayer` and bridging the gap between Fuel entities and the generic core engines. No fuel pricing or odometer logic leaked into the core.

---

## 7. Route Extensibility Assessment
**Extensible without core modifications.** 
To add Route Intelligence, the following is required:
1.  New `RouteIntelligenceHandler`
2.  New Route Data Providers
3.  Registration in `HandlerRegistry`
The existing `GenericBaselineEngine`, `GenericAnomalyEngine`, and `GenericContributingFactorEngine` will mathematically process route observations out-of-the-box.

---

## 8. Driver Extensibility Assessment
**Extensible without core modifications.**
Driver Intelligence (e.g., Driver Risk Score) can be added precisely like Route Intelligence by implementing a `DriverIntelligenceHandler`. The core mathematical engines remain untouched.

---

## 9. Event Routing
The `GenericIntelligenceOrchestrator` properly queries the `HandlerRegistry` using `event_type`.
*   Multiple handler support is functional.
*   Unsupported events safely bypass processing.
*   **Finding:** `TRIP_COMPLETED` can safely trigger multiple domain handlers routing-wise, but they are coupled by the transaction context (see Section 10).

---

## 10. Transaction Boundaries
**Audit finding:** The orchestrator maintains a single `UnitOfWork` per event across all domain handlers. 
**Consequence:** If `TRIP_COMPLETED` triggers Fuel, Route, and Driver intelligence, and Driver Intelligence raises an exception, the entire transaction rolls back. This drops the successfully calculated Fuel and Route intelligence, violating domain isolation at the persistence level.
**Classification: P1 (Should fix before V2).** We must isolate transactions per domain handler so a failure in Driver does not block Fuel.

---

## 11. Idempotency
The stack maintains idempotency seamlessly. `FuelIntelligenceHandler` successfully checks if an observation already exists using a deterministic `source_reference`. The risk of two domains processing the same event and colliding is mitigated as each domain generates unique reference IDs tied to its respective metrics.

---

## 12. Database Generalization
Database tables remain Fuel-named (e.g., `DerivedFuelMetric`, `FuelAnomaly`, `FuelFinancialImpact`).
**Classification: SHOULD EVENTUALLY GENERALIZE.**
These tables are structurally sound for generic data, but renaming them now is cosmetic and unnecessary. We recommend keeping them for compatibility, or simply mapping Route/Driver objects into them under a generic `entity_type` until a major database migration is warranted.

---

## 13. API Architecture
Current Owner Intelligence APIs (`/intelligence/fuel/...`) are heavily Fuel-specific.
**Recommendation:** To prevent creating `/route/` and `/driver/` duplicates, evolve to a generic `GET /intelligence/assets/{entity_id}/summary` endpoint that aggregates all intelligence (Fuel, Route, Driver) under a single payload structure.

---

## 14. Financial Impact Architecture
`GenericFinancialImpactResult` successfully abstracts `baseline_value`, `observed_value`, and `estimated_financial_exposure`. Legacy Fuel fields are encapsulated in `domain_context`. This structure is completely sufficient for Route and Driver financial impacts.

---

## 15. Contributing Factors Architecture
The `GenericContributingFactorEngine` deterministically ranks evidence (STRONG > MODERATE > WEAK > NO). It explicitly falls back to `UNKNOWN` when no supporting evidence exists. Future Route/Driver providers can easily implement the `BaseContributingFactorProvider` protocol.

---

## 16. Legacy Intelligence Assessment
*   `PredictionService`: Duplicates Breakdown Risk, Driver Safety Score, and Fuel Fraud via in-memory static mathematics. Should eventually migrate to Generic Intelligence.
*   `TripIntelligenceService`: Calculates anomalies and profitability on-the-fly. Should eventually be refactored to read from persisted generic `Anomaly` tables.
*   **Action:** Safely freeze these services. Do not migrate them in V2.

---

## 17. Frontend Duplication Audit
Searched `frontend/src` and identified:
*   **FRONTEND PRESENTATION:** `ArchitectureShowcase.jsx` contains hardcoded React calculations for `calculateBRI()`, `calculateDRS()`, and `calculateFuelFraud()`.
*   **FRONTEND PRESENTATION:** `TripIntelligence.jsx` receives backend scores but computes visual `variance_pct` mathematics for rendering bars.
No backend intelligence logic has been dangerously duplicated for core business processes; these are presentation/showcase functions.

---

## 18. End-to-End Traceability
Traceability is fully intact. An `OperationalEvent` is linked down the cascade via `source_reference` → `observation_reference` → `anomaly_reference` → `financial_impact_reference`. The chain is mathematically and structurally complete.

---

## 19. Performance Risks
**High Risk (N+1 / Query Amplification):** If a single `TRIP_COMPLETED` event triggers 3 handlers (Fuel, Route, Driver), each handler will independently query the database for the Trip context, Vehicle context, and raw telemetry data. This redundant data fetching must be optimized.

---

## 20. Security Risks
Tenant isolation is securely enforced at the API layer. `company_id=current_user.company_id` is validated against the requested vehicle/truck intelligence.

---

## 21. V1 Mathematical Validation
Ran `pytest tests/intelligence/`. 
**Result: 271 passed.**
Baseline mathematics, anomaly threshold logic, financial calculations, and idempotency behave identically to V1 expectations.

---

## 22. Critical Findings
*   **P1 — Transaction Isolation:** Single UoW couples domain successes. A failure in Driver intelligence will roll back successful Fuel intelligence.
*   **P1 — Query Amplification:** Multiple handlers processing the same event will redundantly query the database for the same context.
*   **P3 — Legacy Duplication:** `PredictionService` and `TripIntelligenceService` actively duplicate V2 pipeline calculations.

---

## 23. V2 Readiness Score
**Score: 85 / 100**
**Rating: V2 READY WITH CONDITIONS**

---

## 24. Final Recommendation
**YES.** FleetGuard should begin Route + Driver Intelligence immediately.
**Conditions:** The P1 Transaction Isolation issue must be resolved either at the start of V2 or during the orchestrator integration of the new Route/Driver handlers to prevent cross-domain pollution.

---

## 25. Proposed Milestone 2I
**Milestone 2I: Transaction Isolation & Route Intelligence Implementation**
1. Modify `GenericIntelligenceOrchestrator` to execute each Handler in an independent UnitOfWork transaction.
2. Implement `RouteIntelligenceHandler`, `RouteBaselineEngine`, and map to generic core.
3. Define Route Intelligence Data Providers (Duration, Distance Deviations).
