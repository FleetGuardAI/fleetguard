"""
FleetGuard — Fleet Intelligence API Router
Exposes the Fleet Intelligence Engine to the frontend dashboard.
"""

from fastapi import APIRouter, Depends
from infrastructure.uow import AbstractUnitOfWork
from database import get_read_uow
from services.fleet_intelligence_service import FleetIntelligenceService
from schemas.fleet_intelligence import FleetHealthResponse
from models.user import User
from services.auth_service import get_current_user
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
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
    now = datetime.utcnow()
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
