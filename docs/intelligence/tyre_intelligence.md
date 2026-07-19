# Tyre Intelligence

The **Tyre Intelligence** domain evaluates the operational health and safety of vehicle tyres based on inspection records, pressure readings, tread measurements, and wear patterns. It determines tyre compliance and safety without modifying the core intelligence framework.

## Business Objective
Determine tyre health deterministically. The output informs whether a vehicle's tyres are safe to operate, require maintenance, or must be replaced immediately.

## Tyre Evidence Models
This domain consumes two distinct, immutable factual models:
- **`TyreInspectionEvidence`**: Contains physical inspection facts (`tyre_position`, `inspection_date`, `tread_depth_mm`, `tyre_installation_date`, `wear_pattern`, `observed_damage_severity`).
- **`TyrePressureEvidence`**: Contains pressure reading facts (`tyre_position`, `reading_date`, `tyre_pressure_psi`, `recommended_pressure_psi`).
- **`TyreReplacementEvidence`**: Contains historical replacement facts.

## Configuration
The `TyreIntelligenceConfig` centralizes business thresholds:
- `minimum_tread_depth_mm`
- `maximum_pressure_deviation_psi`
- `maximum_tyre_age_days`
- `critical_damage_types`

## Pipeline Implementation

### 1. Checks
Individual checks evaluate raw evidence and determine objective facts.
- **`TyrePressureCheck`**: Evaluates whether pressure deviation exceeds `maximum_pressure_deviation_psi`.
- **`TyreTreadDepthCheck`**: Evaluates whether tread depth is above `minimum_tread_depth_mm`.
- **`TyreAgeCheck`**: Computes tyre age (`inspection_date` - `tyre_installation_date`) and checks against `maximum_tyre_age_days`.
- **`TyreWearPatternCheck`**: Evaluates the wear pattern. Passes if `NORMAL`, otherwise identifies the abnormal pattern (e.g., `UNEVEN`, `CUPPING`).
- **`TyreDamageCheck`**: Evaluates whether damage severity falls into the `critical_damage_types`.

### 2. Assessment
**`TyreHealthAssessment`**
Consumes the check results and maps failures into factual findings such as:
- *Abnormal tyre pressure detected.*
- *Tyre tread depth is below minimum safe limits.*
- *Tyre has exceeded maximum safe age.*
- *Abnormal tyre wear pattern detected.*
- *Critical tyre damage identified during inspection.*

### 3. Domain Risk
**`TyreHealthRiskEngine`**
Consumes the assessment findings and deterministically maps them to a `RiskLevel`:
- **Safety Critical Finding** (tread, damage, age) -> `CRITICAL` risk.
- **0 violations** -> `LOW` risk.
- **1 non-critical violation** -> `MEDIUM` risk.
- **2+ non-critical violations** -> `HIGH` risk.

### 4. Global Decision
**`TyreHealthDecisionEngine`**
Consumes the complete collection of `DomainRiskProfiles` and internally selects `tyre.health_risk`. It maps the risk level to a policy:
- `LOW` -> `APPROVE`
- `MEDIUM` -> `APPROVE_WITH_REVIEW`
- `HIGH` -> `REVIEW_REQUIRED`
- `CRITICAL` -> `REJECT`

## Explainability Chain
The domain fully preserves the explainability chain:
`Recommendation` -> `DomainRiskProfile` -> `AssessmentResult` -> `CheckResult` -> `Evidence`.

## Best Practices
- **No AI or Business Logic in Checks**: Checks must remain stateless, deterministic, and pure.
- **Immutable Findings**: Wear patterns and damage must be explicitly enumerated.
- **Do not modify risk in Decision**: Decision engines only translate risk into policy recommendations.
