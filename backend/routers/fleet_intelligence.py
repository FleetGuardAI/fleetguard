"""
FleetGuard — Fleet Intelligence API Router
Exposes the Fleet Intelligence Engine to the frontend dashboard.
"""

from fastapi import APIRouter, Depends
from infrastructure.uow import AbstractUnitOfWork
from database import get_read_uow
from services.fleet_intelligence_service import FleetIntelligenceService
from schemas.fleet_intelligence import (
    FleetHealthResponse, FleetHealthOverview, FleetAnomaliesResponse,
    FuelEfficiencyAnalysis, MaintenancePrioritiesResponse,
    TripPerformanceAnalysis, DataQualityResponse
)
from models.user import User
from services.auth_service import get_current_user
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import random

from infrastructure.intelligence.fuel_domain.financial.summary_service import FleetFinancialIntelligenceService

class OwnerScores(BaseModel):
    fleet_score: int
    driver_score: int
    truck_score: int
    maintenance_score: int


router = APIRouter(prefix="/intelligence", tags=["Fleet Intelligence"])


@router.get("/fleet-health", response_model=FleetHealthResponse)
async def get_fleet_health(
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user)
) -> FleetHealthResponse:
    """
    Retrieve the current Fleet Health Report deterministically computed by 
    the Fleet Intelligence Engine based on operational events.
    """
    service = FleetIntelligenceService(uow)
    return await service.get_fleet_health(company_id=current_user.company_id)


@router.get("/owner/scores", response_model=OwnerScores)
async def get_owner_scores(
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user)
) -> OwnerScores:
    """
    Retrieve deterministically calculated 0-100 scores for the Owner Dashboard.
    It bases the scores off the Fleet Intelligence domain risk statistics.
    """
    service = FleetIntelligenceService(uow)
    health = await service.get_fleet_health(company_id=current_user.company_id)
    
    if health.vehicle_count == 0:
        return OwnerScores(
            fleet_score=0,
            driver_score=0,
            truck_score=0,
            maintenance_score=0
        )

    # Calculate simple 0-100 scores from risk counts
    # The more medium/high/critical counts, the lower the score.
    def calculate_domain_score(domain_stats):
        deductions = (
            domain_stats.low_count * 1 +
            domain_stats.medium_count * 5 +
            domain_stats.high_count * 10 +
            domain_stats.critical_count * 20
        )
        score = 100 - deductions
        return max(0, min(100, score))
        
    driver_score = calculate_domain_score(health.domain_statistics.driver)
    truck_score = calculate_domain_score(health.domain_statistics.fuel) # Assuming fuel/asset impacts truck score
    maintenance_score = calculate_domain_score(health.domain_statistics.maintenance)
    
    fleet_score = int((driver_score + truck_score + maintenance_score) / 3)
    
    return OwnerScores(
        fleet_score=fleet_score,
        driver_score=driver_score,
        truck_score=truck_score,
        maintenance_score=maintenance_score
    )

class InsightCard(BaseModel):
    id: str
    type: str
    title: str
    primaryValue: str
    secondaryValue: str
    trend: str
    status: str
    description: str

class OperationsInsightsResponse(BaseModel):
    insights: List[InsightCard]

@router.get("/operations/insights", response_model=OperationsInsightsResponse)
async def get_operations_insights(
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user)
) -> OperationsInsightsResponse:
    """
    Normalized Operations Engine data mapping.
    Converts various domain intelligence into standardized insight cards.
    """
    insights = []
    
    # 1. Fuel Intelligence (Efficiency / Leakage)
    fuel_service = FleetFinancialIntelligenceService()
    now = datetime.now(timezone.utc)
    try:
        fuel_summary = await fuel_service.get_fleet_summary(
            uow=uow,
            fleet_id=current_user.company_id,
            period_start=now - timedelta(days=30),
            period_end=now
        )
        
        if fuel_summary.total_estimated_exposure > 0:
            insights.append(InsightCard(
                id="fuel_exposure",
                type="efficiency",
                title="Fuel Leakage Risk",
                primaryValue=f"₹{fuel_summary.total_estimated_exposure:,.0f}",
                secondaryValue=f"Across {fuel_summary.affected_trucks} vehicles",
                trend=f"{int(fuel_summary.total_excess_fuel_liters)}L excess",
                status="Critical" if fuel_summary.total_estimated_exposure > 5000 else "Attention",
                description="Estimated financial exposure"
            ))
    except Exception as e:
        pass # If fuel fails, we still return other insights
        
    # 2. Maintenance Intelligence
    health_service = FleetIntelligenceService(uow)
    health = await health_service.get_fleet_health(company_id=current_user.company_id)
    
    active_critical = health.domain_statistics.maintenance.critical_count
    if active_critical > 0:
         insights.append(InsightCard(
            id="maintenance_risk",
            type="maintenance",
            title="Maintenance Risk",
            primaryValue=f"{active_critical} Vehicles",
            secondaryValue="Require immediate service",
            trend="",
            status="Critical",
            description="Active critical alerts"
        ))
         
    active_driver_issues = health.domain_statistics.driver.medium_count + health.domain_statistics.driver.high_count + health.domain_statistics.driver.critical_count
    if active_driver_issues > 0:
        insights.append(InsightCard(
            id="driver_risk",
            type="performance",
            title="Driver Compliance",
            primaryValue=f"{active_driver_issues} Alerts",
            secondaryValue="Driver-related operational flags",
            trend="",
            status="Attention",
            description="Requires review"
        ))

    return OperationsInsightsResponse(insights=insights)


# ==============================================================================
# EVIDENCE-GROUNDED FLEET INTELLIGENCE ENDPOINTS (P3)
# ==============================================================================

@router.get("/overview", response_model=FleetHealthOverview)
async def get_fleet_health_overview(
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user)
) -> FleetHealthOverview:
    """
    Authoritative fleet overview: telemetry freshness (fresh/stale/unavailable),
    maintenance schedules (overdue/due soon/up to date), trip delays, and priority findings.
    """
    service = FleetIntelligenceService(uow)
    return await service.get_fleet_health_overview(company_id=current_user.company_id)


@router.get("/anomalies", response_model=FleetAnomaliesResponse)
async def get_fleet_anomalies(
    category: Optional[str] = None,
    min_severity: Optional[str] = None,
    limit: int = 20,
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user)
) -> FleetAnomaliesResponse:
    """
    Retrieves ranked operational anomalies and threshold violations across fuel,
    maintenance, trips, and telemetry with supporting evidence and recommended next steps.
    """
    service = FleetIntelligenceService(uow)
    return await service.get_fleet_anomalies(
        company_id=current_user.company_id,
        category=category,
        min_severity=min_severity,
        limit=min(limit, 50)
    )


@router.get("/fuel-efficiency", response_model=FuelEfficiencyAnalysis)
async def analyze_fuel_efficiency(
    vehicle_id: Optional[int] = None,
    period_days: int = 30,
    compare_previous: bool = True,
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user)
) -> FuelEfficiencyAnalysis:
    """
    Analyzes fleet and vehicle fuel expenditure and consumption (km/L and L/100km).
    Compares period-over-period spend and detects unusual consumption spikes against baselines.
    """
    service = FleetIntelligenceService(uow)
    return await service.analyze_fuel_efficiency(
        company_id=current_user.company_id,
        vehicle_id=vehicle_id,
        period_days=min(max(period_days, 1), 90),
        compare_previous=compare_previous
    )


@router.get("/maintenance-priorities", response_model=MaintenancePrioritiesResponse)
async def get_maintenance_priorities(
    status_filter: Optional[str] = None,
    limit: int = 15,
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user)
) -> MaintenancePrioritiesResponse:
    """
    Identifies vehicles with overdue or upcoming maintenance, chronic repeated maintenance issues,
    and odometer discrepancies with actionable next steps.
    """
    service = FleetIntelligenceService(uow)
    return await service.get_maintenance_priorities(
        company_id=current_user.company_id,
        status_filter=status_filter,
        limit=min(limit, 50)
    )


@router.get("/trip-performance", response_model=TripPerformanceAnalysis)
async def analyze_trip_performance(
    trip_id: Optional[int] = None,
    status: Optional[str] = None,
    days: int = 30,
    limit: int = 15,
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user)
) -> TripPerformanceAnalysis:
    """
    Audits operational trip records for departure delays, en-route delivery delays,
    route distance deviations (>15%), and unclosed trips.
    """
    service = FleetIntelligenceService(uow)
    return await service.analyze_trip_performance(
        company_id=current_user.company_id,
        trip_id=trip_id,
        status=status,
        days=min(max(days, 1), 90),
        limit=min(limit, 50)
    )


@router.get("/data-quality", response_model=DataQualityResponse)
async def get_data_quality_findings(
    limit: int = 20,
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user)
) -> DataQualityResponse:
    """
    Audits fleet data completeness and instrumentation issues: missing GPS tracking,
    stale telemetry, missing/zero odometers, and unlogged trip mileage.
    """
    service = FleetIntelligenceService(uow)
    return await service.get_data_quality_findings(
        company_id=current_user.company_id,
        limit=min(limit, 50)
    )
