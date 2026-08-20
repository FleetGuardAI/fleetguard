from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from infrastructure.uow import AbstractUnitOfWork
from database import get_read_uow
from models.user import User
from services.auth_service import get_current_user

from infrastructure.intelligence.fuel_domain.financial.summary_service import FleetFinancialIntelligenceService
from infrastructure.intelligence.fuel_domain.financial.summary_schemas import FleetFinancialIntelligenceSummary
from infrastructure.intelligence.fuel_domain.financial.truck_service import TruckFinancialIntelligenceService
from infrastructure.intelligence.fuel_domain.financial.truck_schemas import TruckIntelligenceDetailResponse

router = APIRouter(prefix="/intelligence/fuel", tags=["Fuel Intelligence"])

@router.get("/summary", response_model=FleetFinancialIntelligenceSummary)
async def get_fuel_summary(
    period_start: datetime,
    period_end: datetime,
    top_n: int = Query(5, ge=1, le=50),
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve fleet-level fuel financial intelligence summary.
    Estimated financial exposure derived from observed fuel-efficiency deviation 
    and historically aligned fuel pricing.
    """
    if period_start >= period_end:
        raise HTTPException(status_code=400, detail="period_start must be before period_end")
        
    service = FleetFinancialIntelligenceService()
    return await service.get_fleet_summary(
        uow=uow,
        fleet_id=current_user.company_id,
        period_start=period_start,
        period_end=period_end,
        top_n=top_n
    )

@router.get("/trucks/{truck_id}", response_model=TruckIntelligenceDetailResponse)
async def get_truck_intelligence(
    truck_id: str,
    period_start: datetime,
    period_end: datetime,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    uow: AbstractUnitOfWork = Depends(get_read_uow),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve detailed fuel financial intelligence for a specific truck.
    Includes historical anomalies, financial impacts, and evidence-supported 
    possible contributing factors; not a confirmed causal diagnosis.
    """
    if period_start >= period_end:
        raise HTTPException(status_code=400, detail="period_start must be before period_end")
        
    service = TruckFinancialIntelligenceService()
    result = await service.get_truck_detail(
        uow=uow,
        truck_id=truck_id,
        company_id=current_user.company_id,
        period_start=period_start,
        period_end=period_end,
        limit=limit,
        offset=offset
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Truck not found or unauthorized")
        
    return result
