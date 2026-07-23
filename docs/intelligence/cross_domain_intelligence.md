# Cross-Domain Intelligence

## Architecture Overview
The Cross-Domain Intelligence layer operates at the final tier of the Fleet Intelligence Engine architecture. It executes strictly **after** all individual Domain Risk Engines have computed their `DomainRiskProfiles`. 

Its primary responsibility is to synthesize these isolated profiles to discover deterministic, operational relationships spanning multiple domains.

### Scope and Boundaries
**Cross-Domain Intelligence DOES NOT:**
- Calculate or modify domain risks.
- Modify or produce Global Decisions (e.g., APPROVE/REJECT).
- Replace domain-specific intelligence.
- Access databases, external APIs, Evidence, Checks, or Assessments directly.

**Cross-Domain Intelligence DOES:**
- Consume immutable `DomainRiskProfiles`.
- Produce immutable `FleetInsights`.
- Preserve full explainability back to the source domains.

## Execution Lifecycle
1. **Domain Execution:** The orchestrator executes all domains (Fuel, Driver, Maintenance, Tyre, Route, Compliance).
2. **Profile Collection:** The orchestrator collects the resulting `DomainRiskProfiles`.
3. **Cross-Domain Execution:** The orchestrator passes the profiles to the `CrossDomainExecutor`.
4. **Analyzer Invocation:** The executor iterates through the `CrossDomainRegistry` and deterministically executes each registered `BaseCrossDomainAnalyzer`.
5. **Aggregation:** The executor aggregates discovered `FleetInsights` into a `FleetInsightCollection`, isolating any analyzer failures to prevent pipeline termination.

## FleetInsight Model
A `FleetInsight` is an immutable, strictly typed representation of an operational insight:
- `insight_type`: The nature of the insight (e.g., `CORRELATION`, `DEPENDENCY`, `OPERATIONAL_PATTERN`, `COMPLIANCE_PATTERN`).
- `insight_strength`: The confidence or severity (`LOW`, `MEDIUM`, `HIGH`).
- `summary`: Human-readable explanation.
- `supporting_profiles`: References to the specific `DomainRiskProfile` objects that triggered the insight (preserves explainability).

## Concrete Analyzers

### Fuel & Driver Correlation (`cross.fuel_driver`)
- **Consumes**: `fuel.transaction_risk`, `driver.behaviour_risk`
- **Logic**: Identifies if high fuel risk coincides with high driver behaviour risk.
- **Insight**: "Elevated driver behaviour risk coincides with increased fuel risk."

### Fuel & Tyre Correlation (`cross.fuel_tyre`)
- **Consumes**: `fuel.transaction_risk`, `tyre.health_risk`
- **Logic**: Identifies if high fuel risk coincides with critical tyre health risk.
- **Insight**: "Poor tyre condition may contribute to reduced fuel efficiency."

### Driver & Tyre Correlation (`cross.driver_tyre`)
- **Consumes**: `driver.behaviour_risk`, `tyre.health_risk`
- **Logic**: Identifies if high driver behaviour risk correlates with tyre wear issues.
- **Insight**: "Aggressive driving behaviour may contribute to accelerated tyre wear."

### Maintenance & Compliance Correlation (`cross.maintenance_compliance`)
- **Consumes**: `maintenance.vehicle_health_risk`, `compliance.vehicle_risk`
- **Logic**: Identifies if a vehicle requires maintenance while approaching regulatory non-compliance.
- **Insight**: "Vehicle requires maintenance while approaching regulatory non-compliance."

### Route & Compliance Correlation (`cross.route_compliance`)
- **Consumes**: `route.trip_compliance_risk`, `compliance.vehicle_risk`
- **Logic**: Identifies if a vehicle with compliance issues enters regulated/restricted operational areas.
- **Insight**: "Vehicle entered regulated operational areas while compliance risk is elevated."

### Route & Fuel Correlation (`cross.route_fuel`)
- **Consumes**: `fuel.transaction_risk`, `route.trip_compliance_risk`
- **Logic**: Identifies if route deviations correlate with excessive fuel usage.
- **Insight**: "Route deviations may contribute to increased fuel consumption."

## Best Practices & Anti-Patterns
- **DO** rely solely on the `risk_level` and `findings` exposed by the `DomainRiskProfile`.
- **DO NOT** attempt to re-calculate risk or perform math on raw telemetry.
- **DO NOT** allow an analyzer to throw an unhandled exception that stops execution (though the `CrossDomainExecutor` isolates failures anyway, it's best practice to return an empty list).
- **DO NOT** modify the `DomainRiskProfile` objects passed into the analyzer; they are frozen and immutable.
