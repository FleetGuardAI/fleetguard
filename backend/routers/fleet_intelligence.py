"""
FleetGuard — Fleet Intelligence API Router
Exposes the Fleet Intelligence Engine to the frontend dashboard.
"""

from fastapi import APIRouter, Depends
from infrastructure.uow import AbstractUnitOfWork
from database import get_read_uow
from services.fleet_intelligence_service import FleetIntelligenceService
from schemas.fleet_intelligence import FleetHealthResponse


router = APIRouter(prefix="/intelligence", tags=["Fleet Intelligence"])


@router.get("/fleet-health", response_model=FleetHealthResponse)
async def get_fleet_health(
    uow: AbstractUnitOfWork = Depends(get_read_uow)
) -> FleetHealthResponse:
    """
    Retrieve the current Fleet Health Report deterministically computed by 
    the Fleet Intelligence Engine based on operational events.
    """
    service = FleetIntelligenceService(uow)
    return await service.get_fleet_health()
