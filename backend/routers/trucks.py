"""
FleetGuard — Trucks API Router
CRUD operations for fleet vehicles.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database import get_db
from models.truck import Truck
from models.user import User
from schemas.truck import TruckCreate, TruckUpdate, TruckResponse
from services.auth_service import get_current_user

router = APIRouter(prefix="/trucks", tags=["Trucks"])


@router.get("", response_model=list[TruckResponse])
async def list_trucks(
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TruckResponse]:
    """List all trucks for the logged-in user's company."""
    query = select(Truck).where(Truck.company_id == current_user.company_id)

    if is_active is not None:
        query = query.where(Truck.is_active == is_active)

    query = query.order_by(Truck.license_plate).offset(offset).limit(limit)
    result = await db.execute(query)
    trucks = result.scalars().all()

    return [TruckResponse.model_validate(t) for t in trucks]


@router.get("/{truck_id}", response_model=TruckResponse)
async def get_truck(
    truck_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TruckResponse:
    """Get a single truck by ID for the logged-in user's company."""
    truck = await db.get(Truck, truck_id)
    if not truck or truck.company_id != current_user.company_id:
        raise HTTPException(404, f"Truck {truck_id} not found")
    return TruckResponse.model_validate(truck)


@router.post("", response_model=TruckResponse, status_code=201)
async def create_truck(
    payload: TruckCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TruckResponse:
    """Register a new truck in the fleet for the logged-in user's company."""
    # Check for duplicate license plate within the user's company
    existing = await db.execute(
        select(Truck).where(
            Truck.license_plate == payload.license_plate,
            Truck.company_id == current_user.company_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Truck with plate '{payload.license_plate}' already exists")

    truck = Truck(
        company_id=current_user.company_id,
        license_plate=payload.license_plate,
        make=payload.make,
        model=payload.model,
        year=payload.year,
        tank_capacity=payload.tank_capacity,
    )
    db.add(truck)
    await db.flush()
    await db.refresh(truck)

    return TruckResponse.model_validate(truck)


@router.patch("/{truck_id}", response_model=TruckResponse)
async def update_truck(
    truck_id: int,
    payload: TruckUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TruckResponse:
    """Update truck information for the logged-in user's company."""
    truck = await db.get(Truck, truck_id)
    if not truck or truck.company_id != current_user.company_id:
        raise HTTPException(404, f"Truck {truck_id} not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(truck, field, value)

    await db.flush()
    await db.refresh(truck)
    return TruckResponse.model_validate(truck)


@router.delete("/{truck_id}", status_code=204)
async def deactivate_truck(
    truck_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Soft-delete a truck (set is_active=False) for the logged-in user's company."""
    truck = await db.get(Truck, truck_id)
    if not truck or truck.company_id != current_user.company_id:
        raise HTTPException(404, f"Truck {truck_id} not found")

    truck.is_active = False
    await db.flush()
