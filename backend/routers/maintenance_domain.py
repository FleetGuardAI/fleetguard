"""
FleetGuard — Maintenance Domain API Router
Provides Read-Only REST APIs for the Maintenance Business Domain.
(Write operations are processed asynchronously via Operational Events).

Security: All endpoints require authentication and are scoped to the
authenticated user's company. Maintenance records are linked to company
via the Vehicle→company_id relationship.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from database import get_db, get_read_uow
from infrastructure.uow import AbstractUnitOfWork
from models.maintenance_domain import MaintenanceRecord, MaintenanceStatus
from models.vehicle_domain import Vehicle
from schemas.maintenance_domain import MaintenanceRecordResponse
from services.auth_service import get_current_user
from models.user import User

router = APIRouter(prefix="/v1", tags=["Maintenance Domain"])


@router.get("/maintenance", response_model=List[MaintenanceRecordResponse])
async def list_maintenance(
    status: Optional[MaintenanceStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[MaintenanceRecordResponse]:
    """List all maintenance records with optional status filter. Company-scoped."""
    company_id = current_user.company_id

    query = (
        select(MaintenanceRecord)
        .outerjoin(Vehicle, MaintenanceRecord.vehicle_id == Vehicle.id)
        .where(Vehicle.company_id == company_id)
    )
    if status:
        query = query.where(MaintenanceRecord.status == status)
    query = query.order_by(MaintenanceRecord.id.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    records = result.scalars().all()
    return [MaintenanceRecordResponse.model_validate(r) for r in records]


@router.get("/maintenance/search", response_model=List[MaintenanceRecordResponse])
async def search_maintenance(
    status: Optional[MaintenanceStatus] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[MaintenanceRecordResponse]:
    """Search for maintenance records based on criteria. Company-scoped."""
    company_id = current_user.company_id

    query = (
        select(MaintenanceRecord)
        .outerjoin(Vehicle, MaintenanceRecord.vehicle_id == Vehicle.id)
        .where(Vehicle.company_id == company_id)
    )
    if status:
        query = query.where(MaintenanceRecord.status == status)
    query = query.order_by(MaintenanceRecord.id.desc()).offset(offset).limit(limit)

    result = await db.execute(query)
    records = result.scalars().all()
    return [MaintenanceRecordResponse.model_validate(r) for r in records]


@router.get("/maintenance/{maintenance_id}", response_model=MaintenanceRecordResponse)
async def get_maintenance(
    maintenance_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MaintenanceRecordResponse:
    """Get a single maintenance record by ID. Verifies company ownership."""
    company_id = current_user.company_id

    result = await db.execute(
        select(MaintenanceRecord)
        .outerjoin(Vehicle, MaintenanceRecord.vehicle_id == Vehicle.id)
        .where(MaintenanceRecord.id == maintenance_id, Vehicle.company_id == company_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(404, f"Maintenance Record {maintenance_id} not found")
    return MaintenanceRecordResponse.model_validate(record)


@router.get("/vehicles/{vehicle_id}/maintenance", response_model=List[MaintenanceRecordResponse])
async def get_maintenance_by_vehicle(
    vehicle_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[MaintenanceRecordResponse]:
    """Get all maintenance records associated with a specific vehicle. Verifies vehicle ownership."""
    company_id = current_user.company_id

    # Verify vehicle belongs to the company
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.company_id != company_id:
        raise HTTPException(404, f"Vehicle {vehicle_id} not found")

    result = await db.execute(
        select(MaintenanceRecord)
        .where(MaintenanceRecord.vehicle_id == vehicle_id)
        .order_by(MaintenanceRecord.id.desc())
        .offset(offset)
        .limit(limit)
    )
    records = result.scalars().all()
    return [MaintenanceRecordResponse.model_validate(r) for r in records]
