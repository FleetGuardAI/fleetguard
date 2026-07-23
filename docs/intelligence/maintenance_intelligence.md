# Maintenance Intelligence

The **Maintenance Intelligence** domain evaluates the operational health of a vehicle based on maintenance history and service schedules. It validates compliance with maintenance policies without modifying the core framework architecture (Evidence, Executors, Orchestrator, Registries, or Decision Framework).

## Business Objective
Determine vehicle health and maintenance compliance deterministically. The output informs whether a vehicle is safe to operate, requires scheduled maintenance, or must be grounded due to critical safety component expiration.

## Maintenance Evidence Models
This domain consumes two distinct, immutable factual models:
- **`MaintenanceHistoryEvidence`**: Contains past operational facts (e.g., `vehicle_id`, `service_date`, `odometer_km`, `engine_hours`, `service_type`, `reported_component_failures`, `diagnostic_codes`).
- **`MaintenanceScheduleEvidence`**: Contains future expected maintenance facts (e.g., `vehicle_id`, `next_service_due_date`, `next_service_due_km`).

## Configuration
The `MaintenanceIntelligenceConfig` centralizes business thresholds:
- `service_interval_days`
- `service_interval_km`
- `engine_oil_interval_km`
- `brake_inspection_interval_days`
- `tyre_rotation_interval_km`
- `critical_overdue_grace_days`
- `repeated_failure_threshold_count`
- `repeated_failure_time_window_days`

## Pipeline Implementation

### 1. Checks
Individual checks evaluate the raw evidence and determine objective facts.
- **`MaintenanceServiceOverdueCheck`**: Determines whether scheduled service date is overdue (`next_service_due_date`).
- **`MaintenanceDistanceOverdueCheck`**: Determines whether the vehicle exceeded the configured service distance (`next_service_due_km`).
- **`MaintenanceTimeOverdueCheck`**: Determines whether the maintenance interval has expired based on `service_interval_days` from the last recorded service.
- **`RepeatedFailureCheck`**: Detects repeated failures of the same component within configurable limits (`repeated_failure_threshold_count` over `repeated_failure_time_window_days`).
- **`CriticalComponentDueCheck`**: Determines whether safety-critical maintenance is overdue (e.g., diagnostic codes starting with `CRIT_`).

### 2. Assessment
**`VehicleHealthAssessment`**
Consumes the check results and maps failures into factual findings such as:
- *Scheduled maintenance overdue.*
- *Vehicle exceeded maintenance mileage.*
- *Repeated component failures detected.*
- *Critical maintenance inspection required.*

### 3. Domain Risk
**`VehicleHealthRiskEngine`**
Consumes the assessment findings and deterministically maps them to a `RiskLevel`:
- **Critical Failure** -> `CRITICAL` risk.
- **0 violations** -> `LOW` risk.
- **1 violation** -> `MEDIUM` risk.
- **2+ violations** -> `HIGH` risk.

### 4. Global Decision
**`VehicleHealthDecisionEngine`**
Consumes the complete collection of `DomainRiskProfiles` and internally selects `maintenance.vehicle_health_risk`. It maps the risk level to a policy:
- `LOW` -> `APPROVE`
- `MEDIUM` -> `APPROVE_WITH_REVIEW`
- `HIGH` -> `REVIEW_REQUIRED`
- `CRITICAL` -> `REJECT`

## Explainability Chain
The domain fully preserves the explainability chain:
`Recommendation` -> `DomainRiskProfile` -> `AssessmentResult` -> `CheckResult` -> `Evidence`.

## Best Practices
- **No AI or Business Logic in Checks**: Checks must remain stateless, deterministic, and pure.
- **Single Responsibility Evidence**: Never mix future schedules with historical facts.
- **Do not modify risk in Decision**: Decision engines only translate risk into policy recommendations.
