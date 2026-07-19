# Driver Behaviour Intelligence

The **Driver Behaviour Intelligence** domain evaluates a driver's operational driving session. It determines whether the driver's behaviour indicates safe, efficient, or risky operation using the 5-tier Fleet Intelligence Engine framework.

This domain implementation validates that the intelligence framework supports multiple independent domains (alongside Fuel) without requiring any modifications to the core executors or orchestrator.

## Business Objective
Evaluate operational driving behaviour (e.g. speeding, harsh acceleration, harsh braking, idling, and route deviation) during a single journey and produce a deterministic, explainable recommendation.

*Out of Scope: AI behaviour prediction, long-term driver ranking, fatigue detection, insurance scoring.*

## Driver Evidence
The domain consumes a raw `DrivingSessionEvidence` package representing immutable facts observed during the journey.

```python
class DrivingSessionEvidence(BaseEvidence):
    evidence_type: str = "DrivingSessionEvidence"
    telemetry_points: List[Dict[str, Any]]
    expected_route_polygon: Optional[List[Dict[str, float]]]
```

The Evidence layer strictly contains raw observations. It does not contain pre-computed values like `max_speed` or `idle_duration`.

## Pipeline Implementation

### 1. Checks
Individual checks evaluate the raw telemetry data and determine objective facts.
- **`DriverOverspeedCheck`** (`driver.overspeed`): Calculates maximum speed from telemetry and fails if it exceeds `max_speed_kmh`.
- **`HarshAccelerationCheck`** (`driver.harsh_acceleration`): Evaluates `acceleration_g` against `harsh_acceleration_g`.
- **`HarshBrakingCheck`** (`driver.harsh_braking`): Evaluates negative `acceleration_g` against `harsh_braking_g`.
- **`ExcessiveIdlingCheck`** (`driver.excessive_idling`): Calculates total idle duration (speed < 1.0 while engine is on) against `max_idle_seconds`.
- **`RouteComplianceCheck`** (`driver.route_compliance`): Ensures all telemetry coordinates fall within the `route_deviation_meters` tolerance from the expected route polygon.

### 2. Assessment
**`DriverBehaviourAssessment`** (`driver.behaviour_assessment`)
Consumes the check results and maps failures into factual findings, such as:
- *Excessive speeding detected.*
- *Aggressive driving behaviour observed.*
- *Excessive idle time detected.*
- *Route deviation observed.*

### 3. Domain Risk
**`DriverBehaviourRiskEngine`** (`driver.behaviour_risk`)
Consumes the assessment findings and deterministically maps them to a `RiskLevel`:
- **0 violations** -> `LOW` risk.
- **1 violation** -> `HIGH` risk.
- **2+ violations** -> `CRITICAL` risk.

### 4. Global Decision
**`DriverBehaviourDecisionEngine`** (`driver.behaviour_decision`)
Consumes the complete list of `DomainRiskProfiles` and internally selects the profile identified by `driver.behaviour_risk`. It maps the risk level to a final policy:
- `LOW` -> `APPROVE`
- `MEDIUM` -> `APPROVE_WITH_REVIEW`
- `HIGH` -> `REVIEW_REQUIRED`
- `CRITICAL` -> `REJECT`

## Configuration
The `DriverIntelligenceConfig` controls the thresholds for the domain without hardcoding business rules:
- `max_speed_kmh`
- `harsh_acceleration_g`
- `harsh_braking_g`
- `max_idle_seconds`
- `route_deviation_meters`

## Testing & Extension
The domain is fully covered by isolated unit tests and end-to-end trace preservation tests in `backend/tests/intelligence/driver_domain/`.

To add a new driver check (e.g. `SeatbeltCheck`):
1. Add the check class to `checks/`.
2. Update `DriverBehaviourAssessment.required_checks()` to consume it.
3. Define the finding mapping in the assessment.
4. The pipeline handles execution automatically.
