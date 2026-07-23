# Route Intelligence Domain

## Overview
The Route Intelligence Domain evaluates trip compliance, route adherence, and operational journey behavior. It consumes planned route data and actual trip execution telemetry to determine whether a vehicle adhered to its permitted path and schedule without unauthorized stops or geofence breaches.

This domain operates purely deterministically, fitting into the 5-Tier Intelligence Architecture without requiring modifications to the core orchestrator or decision engines.

## 1. Evidence
The Route domain consumes the following immutable evidence types:
- `PlannedRouteEvidence`: The expected trip schedule and coordinate track.
- `TripExecutionEvidence`: The actual GPS telemetry track and recorded stops.
- `GeofenceEventEvidence`: Logs of enter/exit events at restricted geofences.
- `ApprovedStopEvidence`: The list of explicitly authorized stopping locations for the trip.

## 2. Checks
Checks calculate objective, deterministic facts from the Evidence layer.

- **RouteDeviationCheck** (`route.deviation`): Calculates the maximum physical deviation distance of any point on the actual route from the planned route.
- **TripDelayCheck** (`route.trip_delay`): Calculates the delay between the actual end time and the planned arrival window.
- **UnauthorizedStopCheck** (`route.unauthorized_stop`): Determines whether the vehicle stopped for an extended duration at locations not in the `ApprovedStopEvidence`.
- **GeofenceViolationCheck** (`route.geofence_violation`): Identifies if the vehicle entered prohibited geofence areas.
- **ExcessiveDetourCheck** (`route.excessive_detour`): Compares the total driven distance to the planned route distance and measures the percentage variance.

## 3. Assessments
The Check results are aggregated by the Assessment layer into factual findings.

- **TripComplianceAssessment** (`route.trip_compliance_assessment`): Consumes all Route Checks and produces categorized operational compliance findings (e.g., `route.unauthorized_stop_detected`).

## 4. Domain Risk
The findings are mapped to a discrete business risk level (LOW, MEDIUM, HIGH, CRITICAL).

- **TripComplianceRiskEngine** (`route.trip_compliance_risk`):
  - **CRITICAL**: If a restricted geofence breach or an unauthorized stop is detected.
  - **HIGH**: If a significant route deviation or excessive detour is detected.
  - **MEDIUM**: If a trip delay is detected without other severe violations.
  - **LOW**: If all compliance checks pass.

## 5. Decision Engine
The Risk Profile is converted into an actionable global recommendation.

- **TripComplianceDecisionEngine** (`route.trip_compliance_decision`):
  - LOW risk -> **APPROVE**
  - MEDIUM risk -> **APPROVE_WITH_REVIEW**
  - HIGH risk -> **REVIEW_REQUIRED**
  - CRITICAL risk -> **REJECT**
