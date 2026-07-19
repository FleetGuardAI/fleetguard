# Fleet Health Intelligence

## Architecture Overview
The Fleet Health Intelligence layer is the macroscopic aggregator of the Fleet Intelligence Engine. It consumes the intelligence evaluated for each individual vehicle and synthesizes it into fleet-wide operational insights.

It operates strictly as a read-only aggregation layer.

### Scope and Boundaries
**Fleet Health Intelligence DOES NOT:**
- Recalculate domain risks or evaluate individual checks.
- Modify existing intelligence or cross-domain insights.
- Output business policy or arbitrary scoring metrics (e.g., scoring systems without explicit configuration).
- Expose presentation layer logic (dashboards, web reporting, rendering).

**Fleet Health Intelligence DOES:**
- Consume immutable `DomainRiskProfiles` and `FleetInsights`.
- Group intelligence logically into a `VehicleIntelligenceContext` for analysis.
- Produce a completely deterministic, immutable `FleetHealthReport` and structured `FleetFinding` objects.
- Generate deterministic, human-readable summaries derived explicitly from those findings.

## Execution Lifecycle
1. **Intelligence Generation**: The core Orchestrator evaluates all 6 intelligence domains (Fuel, Driver, Tyre, Maintenance, Route, Compliance) for every vehicle in a given scope.
2. **Cross-Domain Synthesis**: The Cross-Domain Executor evaluates correlations between risks.
3. **Context Wrapping**: Individual `DomainRiskProfiles` are grouped by `vehicle_id` into `VehicleIntelligenceContext` objects.
4. **Fleet Health Aggregation**: The `FleetHealthAnalyzer` consumes the list of vehicle contexts and cross-domain insights.
5. **Output**: Returns an immutable `FleetHealthReport`.

## FleetHealthReport Model
The report contains exact statistics regarding the operational readiness of the fleet:
- `fleet_health_status`: `EXCELLENT`, `GOOD`, `FAIR`, `POOR`, `CRITICAL`.
- `vehicle_count`: Total vehicles evaluated.
- `operational_vehicle_count`: Count of vehicles with no `CRITICAL` risks.
- `critical_vehicle_count`: Count of vehicles carrying at least one `CRITICAL` risk.
- `fleet_summary`: A human-readable text block generated completely deterministically from the findings.
- `fleet_findings`: A list of `FleetFinding` objects representing structured assertions about the fleet (e.g. `fleet.critical_vehicles`).
- `domain_statistics`: Detailed risk distribution matrix (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`) across every intelligence domain.
- `fleet_insights`: The retained list of all Cross-Domain `FleetInsights` applicable to the scope.

## Scoring Methodology and Aggregation Rules

### Vehicle-Level Aggregation
A single vehicle is considered "Critical" if *any* of its `DomainRiskProfiles` evaluate to `CRITICAL`. Otherwise, it is "Operational". 

### Fleet Status Mapping
The global `FleetHealthStatus` is calculated deterministically based on thresholds of high and critical risks across the entire fleet scope:
1. **CRITICAL**: If > 15% of vehicles are critical, or the total count of critical risks >= 10.
2. **POOR**: If > 5% of vehicles are critical, or the total count of high risks >= 15.
3. **FAIR**: If any critical vehicles exist, or the total count of high risks > 5.
4. **GOOD**: If any high risks exist (but no criticals).
5. **EXCELLENT**: If the fleet possesses only low or medium risks.

### Fleet Findings and Summary
Findings are deterministically generated based on the statistics matrix:
- **Empty Fleet**: "Fleet has no vehicles evaluated."
- **Excellent**: "Fleet is operating normally with no elevated risks."
- **Critical Vehicles**: "X vehicles require immediate attention." (Warning: `fleet.critical_vehicles`)
- **Maintenance Concentration**: "Maintenance risks are elevated across the fleet." (Warning: `fleet.maintenance_risks`)
- **Compliance Concentration**: "Compliance issues concentrated in X vehicle domain checks." (Warning: `fleet.compliance_issues`)

The `fleet_summary` concatenates these findings sequentially, guaranteeing that the text output perfectly matches the structured `FleetFinding` data.

## Extension Guide
To extend the Fleet Health Intelligence layer:
1. Add new domain metrics to `FleetDomainStatistics` when integrating a brand new intelligence dimension.
2. Update the aggregation loop inside `FleetHealthAnalyzer.execute()` to populate the new statistics.
3. Append any new deterministic finding rules (e.g. `fleet.weather_risks`) to the finding generation block.
4. Do not include rendering logic, UI markup, or HTML in this layer.

## Best Practices & Anti-Patterns
- **DO** rely solely on the explicit structured risk models (`DomainRiskProfile`).
- **DO NOT** attempt to load raw `Evidence` or `CheckResult` objects inside the Fleet Health layer.
- **DO NOT** embed business weighting scores (`fleet_health_score=83`) unless explicitly requested and configured by a defined mathematical policy.
- **DO NOT** format the report for web export (e.g., adding JSON/HTML layouts). That is the responsibility of the presentation layer.
