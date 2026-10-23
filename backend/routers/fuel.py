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
from schemas.fuel_domain import FuelTransactionCreate, FuelTransactionResponse
from models.fuel_domain import FuelTransaction, FuelTransactionType
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus
from models.trip_domain import Trip
from models.driver_domain import Driver
import uuid
from services.auth_service import get_current_user
from models.user import User
from services.odometer_service import OdometerService

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
        prev_log_result = await db.execute(
            select(FuelLog)
            .where(FuelLog.vehicle_id == log.vehicle_id, FuelLog.timestamp < log.timestamp)
            .order_by(FuelLog.timestamp.desc())
            .limit(1)
        )
        prev_log = prev_log_result.scalars().first()
        drop = (prev_log.filtered_level - log.filtered_level) if prev_log and prev_log.filtered_level is not None else 0
        before = prev_log.filtered_level if prev_log and prev_log.filtered_level is not None else log.filtered_level

        alerts.append(
            FuelAlertResponse(
                id=log.id,
                truck_id=log.vehicle_id,
                truck_plate=truck_plate,
                timestamp=log.timestamp,
                fuel_drop_liters=drop,
                filtered_level_before=before,
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

    # Phase 12: EMA Smoothing
    ALPHA = 0.15 # typical for 1-minute intervals
    
    last_log_result = await db.execute(
        select(FuelLog)
        .where(FuelLog.vehicle_id == payload.truck_id)
        .order_by(FuelLog.timestamp.desc())
        .limit(1)
    )
    last_log = last_log_result.scalars().first()
    
    filtered_level = payload.raw_level
    is_theft = False
    
    if last_log and last_log.filtered_level is not None:
        level_diff = payload.raw_level - last_log.filtered_level
        if level_diff > 30:
            filtered_level = payload.raw_level
            
            # Basic Reconciliation Matching
            recent_unmatched = await db.execute(
                select(FuelTransaction)
                .where(
                    FuelTransaction.vehicle_id == payload.truck_id,
                    FuelTransaction.reconciliation_status == 'UNMATCHED',
                    FuelTransaction.timestamp >= payload.timestamp - timedelta(hours=2)
                )
                .order_by(FuelTransaction.timestamp.desc())
                .limit(1)
            )
            matched_tx = recent_unmatched.scalars().first()
            if matched_tx:
                matched_tx.reconciled_sensor_liters = level_diff
                matched_tx.variance_liters = level_diff - matched_tx.amount_liters
                # +/- 5 Liters tolerance
                if abs(matched_tx.variance_liters) <= 5.0:
                    matched_tx.reconciliation_status = "MATCHED"
                else:
                    matched_tx.reconciliation_status = "PARTIAL_MATCH"
                db.add(matched_tx)
        elif level_diff < -150:
            filtered_level = payload.raw_level
        else:
            filtered_level = (ALPHA * payload.raw_level) + ((1 - ALPHA) * last_log.filtered_level)
            drop_liters = last_log.filtered_level - filtered_level
            if drop_liters > 15 and payload.speed < 10:
                is_theft = True
            elif drop_liters > 40:
                is_theft = True

    fuel_log = FuelLog(
        vehicle_id=payload.truck_id,
        timestamp=payload.timestamp,
        raw_level=payload.raw_level,
        filtered_level=filtered_level,
        expected_level=payload.expected_level,
        speed=payload.speed,
        latitude=payload.latitude,
        longitude=payload.longitude,
        is_theft_alert=is_theft,
    )

    db.add(fuel_log)
    await db.flush()
    await db.refresh(fuel_log)

    return FuelLogResponse.model_validate(fuel_log)

@router.post("/transactions", response_model=FuelTransactionResponse, status_code=201)
async def create_fuel_transaction(
    payload: FuelTransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FuelTransactionResponse:
    """Record a manual fuel transaction."""
    vehicle = await db.get(Vehicle, payload.vehicle_id)
    if not vehicle or vehicle.company_id != current_user.company_id:
        raise HTTPException(404, f"Vehicle {payload.vehicle_id} not found")

    driver_id = payload.driver_id
    if driver_id:
        driver = await db.get(Driver, driver_id)
        if not driver or driver.company_id != current_user.company_id:
            raise HTTPException(403, "Invalid driver")
            
    if payload.trip_id:
        trip = await db.get(Trip, payload.trip_id)
        if not trip or trip.company_id != current_user.company_id:
            raise HTTPException(403, "Invalid trip")
            if not driver_id:
                driver_id = trip.driver_id

    total_cost = payload.quantity_liters * payload.price_per_liter
    
    business_id = f"EXP-{str(uuid.uuid4())[:8].upper()}"
    expense = Expense(
        business_id=business_id,
        company_id=current_user.company_id,
        category=ExpenseCategory.FUEL,
        amount=total_cost,
        currency="INR",
        status=ExpenseStatus.APPROVED,
        expense_date=payload.occurred_at or datetime.now(timezone.utc),
        description=payload.description or f"Refuel at {payload.station or 'Unknown'}",
        receipt_reference=payload.receipt_url,
        vehicle_id=payload.vehicle_id,
        driver_id=driver_id,
        trip_id=payload.trip_id,
        origin_type="manual_fuel_entry",
        origin_id=str(current_user.id)
    )
    db.add(expense)
    await db.flush()

    if payload.odometer is not None:
        OdometerService.update_odometer_if_valid(vehicle, payload.odometer, payload.occurred_at or datetime.now(timezone.utc))
        db.add(vehicle)

    fuel_tx = FuelTransaction(
        company_id=current_user.company_id,
        vehicle_id=payload.vehicle_id,
        driver_id=driver_id,
        trip_id=payload.trip_id,
        expense_id=expense.id,
        transaction_type=FuelTransactionType.FILL,
        amount_liters=payload.quantity_liters,
        fuel_type=payload.fuel_type,
        price_per_liter=payload.price_per_liter,
        total_cost=total_cost,
        odometer=payload.odometer,
        station=payload.station,
        receipt_url=payload.receipt_url,
        origin_type="manual_entry",
        origin_id=str(current_user.id),
        timestamp=payload.occurred_at or datetime.now(timezone.utc),
        description=payload.description
    )
    db.add(fuel_tx)
    await db.commit()
    await db.refresh(fuel_tx)

    return FuelTransactionResponse.model_validate(fuel_tx)


@router.get("/transactions", response_model=list[FuelTransactionResponse])
async def list_fuel_transactions(
    vehicle_id: Optional[int] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[FuelTransactionResponse]:
    """Get manual fuel transactions."""
    query = select(FuelTransaction).where(FuelTransaction.company_id == current_user.company_id)
    
    if vehicle_id:
        query = query.where(FuelTransaction.vehicle_id == vehicle_id)
        
    query = query.order_by(FuelTransaction.timestamp.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    return [FuelTransactionResponse.model_validate(tx) for tx in transactions]
