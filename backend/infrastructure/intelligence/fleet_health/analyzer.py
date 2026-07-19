"""
Fleet Intelligence Engine - Fleet Health Analyzer
"""

from typing import List, Dict, Any
from infrastructure.intelligence.domain_risk.models import RiskLevel
from infrastructure.intelligence.cross_domain.models import FleetInsight
from infrastructure.intelligence.fleet_health.models import (
    FleetHealthReport, FleetHealthStatus, FleetDomainStatistics, 
    DomainRiskCounts, VehicleIntelligenceContext, FleetFinding, FleetFindingSeverity
)


class FleetHealthAnalyzer:
    """
    Aggregates domain-level and cross-domain intelligence into a fleet-wide health report.
    Operates completely deterministically without recalculating domain risks or predictions.
    """

    def __init__(self, fleet_id: str):
        self.fleet_id = fleet_id

    def execute(self, vehicle_contexts: List[VehicleIntelligenceContext], fleet_insights: List[FleetInsight]) -> FleetHealthReport:
        """
        Executes aggregation logic across the provided vehicle contexts.
        """
        
        # 1. Aggregate Statistics
        counts = {
            "fuel": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
            "driver": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
            "maintenance": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
            "tyre": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
            "route": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
            "compliance": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
        }

        critical_vehicles = set()
        operational_vehicles = set()
        total_critical_risks = 0
        total_high_risks = 0
        
        for ctx in vehicle_contexts:
            has_critical = False
            has_high = False
            
            for profile in ctx.profiles:
                domain = profile.risk_engine_key.split(".")[0]
                risk = profile.risk_level.value
                
                if domain in counts and risk in counts[domain]:
                    counts[domain][risk] += 1
                
                if profile.risk_level == RiskLevel.CRITICAL:
                    has_critical = True
                    total_critical_risks += 1
                elif profile.risk_level == RiskLevel.HIGH:
                    has_high = True
                    total_high_risks += 1
                    
            if has_critical:
                critical_vehicles.add(ctx.vehicle_id)
            else:
                operational_vehicles.add(ctx.vehicle_id)

        # Build Domain Statistics
        stats = FleetDomainStatistics(
            fuel=DomainRiskCounts(
                low_count=counts["fuel"]["LOW"], medium_count=counts["fuel"]["MEDIUM"],
                high_count=counts["fuel"]["HIGH"], critical_count=counts["fuel"]["CRITICAL"]
            ),
            driver=DomainRiskCounts(
                low_count=counts["driver"]["LOW"], medium_count=counts["driver"]["MEDIUM"],
                high_count=counts["driver"]["HIGH"], critical_count=counts["driver"]["CRITICAL"]
            ),
            maintenance=DomainRiskCounts(
                low_count=counts["maintenance"]["LOW"], medium_count=counts["maintenance"]["MEDIUM"],
                high_count=counts["maintenance"]["HIGH"], critical_count=counts["maintenance"]["CRITICAL"]
            ),
            tyre=DomainRiskCounts(
                low_count=counts["tyre"]["LOW"], medium_count=counts["tyre"]["MEDIUM"],
                high_count=counts["tyre"]["HIGH"], critical_count=counts["tyre"]["CRITICAL"]
            ),
            route=DomainRiskCounts(
                low_count=counts["route"]["LOW"], medium_count=counts["route"]["MEDIUM"],
                high_count=counts["route"]["HIGH"], critical_count=counts["route"]["CRITICAL"]
            ),
            compliance=DomainRiskCounts(
                low_count=counts["compliance"]["LOW"], medium_count=counts["compliance"]["MEDIUM"],
                high_count=counts["compliance"]["HIGH"], critical_count=counts["compliance"]["CRITICAL"]
            )
        )

        # 2. Derive Fleet Status & Findings
        findings: List[FleetFinding] = []
        
        vehicle_count = len(vehicle_contexts)
        pct_critical = len(critical_vehicles) / vehicle_count if vehicle_count > 0 else 0
        
        if pct_critical > 0.15 or total_critical_risks >= 10:
            status = FleetHealthStatus.CRITICAL
        elif pct_critical > 0.05 or total_high_risks >= 15:
            status = FleetHealthStatus.POOR
        elif len(critical_vehicles) > 0 or total_high_risks > 5:
            status = FleetHealthStatus.FAIR
        elif total_high_risks > 0:
            status = FleetHealthStatus.GOOD
        else:
            status = FleetHealthStatus.EXCELLENT
            
        # 3. Generate Findings deterministically
        if vehicle_count == 0:
            findings.append(FleetFinding(
                finding_key="fleet.empty",
                severity=FleetFindingSeverity.INFO,
                summary="Fleet has no vehicles evaluated."
            ))
        else:
            if status == FleetHealthStatus.EXCELLENT:
                findings.append(FleetFinding(
                    finding_key="fleet.excellent",
                    severity=FleetFindingSeverity.INFO,
                    summary="Fleet is operating normally with no elevated risks."
                ))
            
            if len(critical_vehicles) > 0:
                findings.append(FleetFinding(
                    finding_key="fleet.critical_vehicles",
                    severity=FleetFindingSeverity.CRITICAL,
                    summary=f"{len(critical_vehicles)} vehicles require immediate attention.",
                    metadata={"critical_vehicle_count": len(critical_vehicles)}
                ))
                
            if counts["maintenance"]["HIGH"] > 0 or counts["maintenance"]["CRITICAL"] > 0:
                findings.append(FleetFinding(
                    finding_key="fleet.maintenance_risks",
                    severity=FleetFindingSeverity.WARNING,
                    summary="Maintenance risks are elevated across the fleet.",
                    metadata={"high_and_critical_count": counts["maintenance"]["HIGH"] + counts["maintenance"]["CRITICAL"]}
                ))
                
            if counts["compliance"]["HIGH"] > 0 or counts["compliance"]["CRITICAL"] > 0:
                issues = counts["compliance"]["HIGH"] + counts["compliance"]["CRITICAL"]
                findings.append(FleetFinding(
                    finding_key="fleet.compliance_issues",
                    severity=FleetFindingSeverity.WARNING,
                    summary=f"Compliance issues concentrated in {issues} vehicle domain checks.",
                    metadata={"compliance_issue_count": issues}
                ))

        # 4. Generate summary text from findings
        if not findings:
            summary_text = "Fleet evaluation complete."
        else:
            summary_text = " ".join([f.summary for f in findings])

        return FleetHealthReport(
            fleet_id=self.fleet_id,
            fleet_health_status=status,
            vehicle_count=vehicle_count,
            operational_vehicle_count=len(operational_vehicles),
            critical_vehicle_count=len(critical_vehicles),
            fleet_summary=summary_text,
            fleet_findings=findings,
            domain_statistics=stats,
            fleet_insights=fleet_insights
        )
