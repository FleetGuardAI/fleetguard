"""
FleetGuard — Fuel Monitoring API Router
Fuel log queries, chart data, and theft alert listing.
"""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database import get_db
from models.fuel_log import FuelLog
from models.vehicle_domain import Vehicle
from schemas.fuel_log import FuelLogCreate, FuelLogResponse, FuelAlertResponse, FuelChartData
from services.auth_service import get_current_user
from models.user import User

router = APIRouter(prefix="/fuel", tags=["Fuel Monitoring"])


@router.get("/logs/{truck_id}", response_model=list[FuelLogResponse])
async def get_fuel_logs(
    truck_id: int,
    hours: int = Query(24, ge=1, le=720, description="Look-back window in hours"),
    limit: int = Query(500, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[FuelLogResponse]:
    """Get fuel log entries for a specific truck within a time window."""
    vehicle = await db.get(Vehicle, truck_id)
    if not vehicle or vehicle.company_id != current_user.company_id:
        raise HTTPException(404, f"Vehicle {truck_id} not found")

    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    result = await db.execute(
        select(FuelLog)
        .where(
            FuelLog.vehicle_id == truck_id,
            FuelLog.timestamp >= since,
        )
        .order_by(FuelLog.timestamp.asc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return [FuelLogResponse.model_validate(log) for log in logs]


@router.get("/chart/{truck_id}", response_model=list[FuelChartData])
async def get_fuel_chart_data(
    truck_id: int,
    hours: int = Query(24, ge=1, le=720),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[FuelChartData]:
    """
    Get time-series chart data for the Live Fuel Monitor.
    Returns expected burn curve vs actual EMA-filtered level,
    shaped specifically for the Recharts LineChart component.
    """
    vehicle = await db.get(Vehicle, truck_id)
    if not vehicle or vehicle.company_id != current_user.company_id:
        raise HTTPException(404, f"Vehicle {truck_id} not found")

    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    result = await db.execute(
        select(FuelLog)
        .where(
            FuelLog.vehicle_id == truck_id,
            FuelLog.timestamp >= since,
        )
        .order_by(FuelLog.timestamp.asc())
    )
    logs = result.scalars().all()

    return [
        FuelChartData(
            timestamp=log.timestamp,
            expected_level=log.expected_level,
            actual_filtered_level=log.filtered_level,
            raw_level=log.raw_level,
            is_theft_alert=log.is_theft_alert,
        )
        for log in logs
    ]


@router.get("/alerts", response_model=list[FuelAlertResponse])
async def get_fuel_alerts(
    days: int = Query(30, ge=1, le=365, description="Look-back window in days"),
    truck_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[FuelAlertResponse]:
    """Get fuel theft alerts across all trucks or a specific truck."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    query = (
        select(FuelLog, Vehicle.registration_number)
        .join(Vehicle, FuelLog.vehicle_id == Vehicle.id)
        .where(
            Vehicle.company_id == current_user.company_id,
            FuelLog.is_theft_alert == True,  # noqa: E712
            FuelLog.timestamp >= since,
        )
    )

    if truck_id is not None:
        query = query.where(FuelLog.vehicle_id == truck_id)

    query = query.order_by(FuelLog.timestamp.desc()).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    alerts: list[FuelAlertResponse] = []
    for log, truck_plate in rows:
        # Calculate fuel drop from the previous reading's perspective
        # In Phase 3, the fuel_service will populate this more accurately
        alerts.append(
            FuelAlertResponse(
                id=log.id,
                truck_id=log.vehicle_id,
                truck_plate=truck_plate,
                timestamp=log.timestamp,
                fuel_drop_liters=abs(log.raw_level - log.filtered_level),
                filtered_level_before=log.filtered_level + abs(log.raw_level - log.filtered_level),
                filtered_level_after=log.filtered_level,
                speed=log.speed,
                latitude=log.latitude,
                longitude=log.longitude,
                created_at=log.created_at,
            )
        )

    return alerts


@router.post("/ingest", response_model=FuelLogResponse, status_code=201)
async def ingest_fuel_reading(
    payload: FuelLogCreate,
    db: AsyncSession = Depends(get_db),
    # Optional: You can enforce current_user here if API is called by frontend, 
    # but normally IoT ingestion uses API keys, so I'll leave this as depends on user for now.
    current_user: User = Depends(get_current_user)
) -> FuelLogResponse:
    """
    Ingest a single fuel reading.
    """
    vehicle = await db.get(Vehicle, payload.truck_id)
    if not vehicle or vehicle.company_id != current_user.company_id:
        raise HTTPException(404, f"Vehicle {payload.truck_id} not found")

    # For now, filtered_level = raw_level (Phase 3 adds EMA smoothing)
    fuel_log = FuelLog(
        vehicle_id=payload.truck_id,
        timestamp=payload.timestamp,
        raw_level=payload.raw_level,
        filtered_level=payload.raw_level,  # Will be EMA-smoothed in Phase 3
        expected_level=payload.expected_level,
        speed=payload.speed,
        latitude=payload.latitude,
        longitude=payload.longitude,
        is_theft_alert=False,
    )

    db.add(fuel_log)
    await db.flush()
    await db.refresh(fuel_log)

    return FuelLogResponse.model_validate(fuel_log)
