"""
FleetGuard — Maintenance Domain API Router
Provides Read-Only REST APIs for the Maintenance Business Domain.
(Write operations are processed asynchronously via Operational Events).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from database import get_db
from models.maintenance_domain import MaintenanceStatus
from services.maintenance_service import MaintenanceService
from schemas.maintenance_domain import MaintenanceRecordResponse

router = APIRouter(prefix="/v1", tags=["Maintenance Domain"])


@router.get("/maintenance", response_model=List[MaintenanceRecordResponse])
async def list_maintenance(
    status: Optional[MaintenanceStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> List[MaintenanceRecordResponse]:
    """List all maintenance records with optional status filter."""
    service = MaintenanceService(db)
    records = await service.search_maintenance(status=status, limit=limit, offset=offset)
    return [MaintenanceRecordResponse.model_validate(r) for r in records]


@router.get("/maintenance/search", response_model=List[MaintenanceRecordResponse])
async def search_maintenance(
    status: Optional[MaintenanceStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> List[MaintenanceRecordResponse]:
    """Search for maintenance records based on criteria."""
    service = MaintenanceService(db)
    records = await service.search_maintenance(status=status, limit=limit, offset=offset)
    return [MaintenanceRecordResponse.model_validate(r) for r in records]


@router.get("/maintenance/{maintenance_id}", response_model=MaintenanceRecordResponse)
async def get_maintenance(
    maintenance_id: int, 
    db: AsyncSession = Depends(get_db)
) -> MaintenanceRecordResponse:
    """Get a single maintenance record by ID."""
    service = MaintenanceService(db)
    record = await service.get_maintenance(maintenance_id)
    if not record:
        raise HTTPException(404, f"Maintenance Record {maintenance_id} not found")
    return MaintenanceRecordResponse.model_validate(record)


@router.get("/vehicles/{vehicle_id}/maintenance", response_model=List[MaintenanceRecordResponse])
async def get_maintenance_by_vehicle(
    vehicle_id: int, 
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
) -> List[MaintenanceRecordResponse]:
    """Get all maintenance records associated with a specific vehicle."""
    service = MaintenanceService(db)
    records = await service.get_maintenance_by_vehicle(vehicle_id, limit=limit, offset=offset)
    return [MaintenanceRecordResponse.model_validate(r) for r in records]
