"""
FleetGuard — Owner Dashboard API Router
Aggregation endpoints for the Owner Mobile App Dashboard.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.vehicle_domain import Vehicle, VehicleStatus
from models.driver_domain import Driver, DriverStatus
from models.expense_domain import Expense, ExpenseStatus
from models.trip_domain import Trip, TripStatus
from models.user import User
from services.auth_service import get_current_user
from schemas.trip_domain import TripResponse
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/owner/dashboard", tags=["Owner Dashboard"])


class OwnerDashboardKPIs(BaseModel):
    total_active_trucks: int
    total_active_drivers: int
    active_trips: int
    monthly_expenses: float
    attention_required: int


@router.get("/kpis", response_model=OwnerDashboardKPIs)
async def get_owner_dashboard_kpis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OwnerDashboardKPIs:
    """
    Fetch Owner App Dashboard KPIs:
    - Total Active Trucks
    - Total Active Drivers
    - Active Trips
    - Monthly Expenses
    - Attention Required (Pending Tickets)
    """
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Total Active Trucks
    active_vehicles_result = await db.execute(
        select(func.count(Vehicle.id)).where(
            Vehicle.status == VehicleStatus.ACTIVE,
            Vehicle.company_id == current_user.company_id
        )
    )
    active_trucks = active_vehicles_result.scalar() or 0

    # Total Active Drivers
    active_drivers_result = await db.execute(
        select(func.count(Driver.id)).where(
            Driver.status == DriverStatus.ACTIVE,
            Driver.company_id == current_user.company_id
        )
    )
    active_drivers = active_drivers_result.scalar() or 0

    # Active Trips
    active_trips_result = await db.execute(
        select(func.count(Trip.id)).where(
            Trip.status == TripStatus.IN_PROGRESS,
            Trip.company_id == current_user.company_id
        )
    )
    active_trips = active_trips_result.scalar() or 0

    # Monthly Expenses (via Driver)
    expenses_month_result = await db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0.0))
        .join(Driver, Driver.id == Expense.driver_id)
        .where(
            Expense.status == ExpenseStatus.APPROVED,
            Expense.updated_at >= month_start,
            Driver.company_id == current_user.company_id
        )
    )
    monthly_expenses = float(expenses_month_result.scalar() or 0)

    from models.ticket import Ticket, TicketStatus
    # Attention Required (Pending Tickets)
    attention_result = await db.execute(
        select(func.count(Ticket.id))
        .join(Driver, Ticket.driver_id == Driver.id)
        .where(
            Ticket.status == TicketStatus.PENDING,
            Driver.company_id == current_user.company_id
        )
    )
    attention_required = attention_result.scalar() or 0

    return OwnerDashboardKPIs(
        total_active_trucks=active_trucks,
        total_active_drivers=active_drivers,
        active_trips=active_trips,
        monthly_expenses=monthly_expenses,
        attention_required=attention_required,
    )

@router.get("/expense-analytics")
async def get_expense_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get expense breakdown for the pie chart.
    """
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # We need fuel, maintenance, and other
    result = await db.execute(
        select(Expense.category, func.sum(Expense.amount))
        .join(Driver, Driver.id == Expense.driver_id)
        .where(
            Expense.status == ExpenseStatus.APPROVED,
            Expense.updated_at >= month_start,
            Driver.company_id == current_user.company_id
        )
        .group_by(Expense.category)
    )
    rows = result.all()
    
    fuel_amount = 0.0
    maintenance_amount = 0.0
    other_amount = 0.0

    for cat, amt in rows:
        if cat.value == "FUEL":
            fuel_amount += float(amt)
        elif cat.value in ["MAINTENANCE", "REPAIR"]:
            maintenance_amount += float(amt)
        else:
            other_amount += float(amt)
            
    return {
        "total": fuel_amount + maintenance_amount + other_amount,
        "fuel": fuel_amount,
        "maintenance": maintenance_amount,
        "other": other_amount
    }

@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get recent ticket/trip activity for the owner dashboard.
    """
    from models.ticket import Ticket
    company_id = current_user.company_id

    result = await db.execute(
        select(Ticket, Driver.name, Vehicle.registration_number)
        .join(Driver, Ticket.driver_id == Driver.id)
        .outerjoin(Vehicle, Ticket.vehicle_id == Vehicle.id)
        .where(Driver.company_id == company_id)
        .order_by(Ticket.created_at.desc())
        .limit(limit)
    )
    rows = result.all()

    return [
        {
            "id": ticket.id,
            "title": ticket.issue_type,
            "description": f"Driver {driver_name} reported an issue for {truck_plate or 'Unknown Vehicle'}",
            "type": "ticket",
            "status": ticket.status.value,
            "timestamp": ticket.created_at.isoformat() if ticket.created_at else None,
        }
        for ticket, driver_name, truck_plate in rows
    ]

@router.get("/trips", response_model=List[TripResponse])
async def get_owner_trips(
    search: str = None,
    status: str = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[TripResponse]:
    """
    Get all trips belonging to the authenticated owner's fleet.
    Supports optional search and status filtering.
    """
    from services.trip_service import TripService
    from infrastructure.uow import SqlAlchemyUnitOfWork
    
    uow = SqlAlchemyUnitOfWork(db)
    service = TripService(uow)
    
    # Try parsing the status string into TripStatus enum if provided
    status_enum = None
    if status and status.upper() != 'ALL':
        try:
            status_enum = TripStatus(status.upper())
        except ValueError:
            pass
            
    trips = await service.search_trips(
        status=status_enum,
        limit=limit,
        offset=offset,
        company_id=current_user.company_id,
        search=search
    )
    return [TripResponse.model_validate(t) for t in trips]

@router.patch("/expenses/{expense_id}/approve")
async def approve_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from fastapi import HTTPException
    expense = await db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(404, "Expense not found")
        
    driver = await db.get(Driver, expense.driver_id)
    if not driver or driver.company_id != current_user.company_id:
        raise HTTPException(400, "Unauthorized: Expense belongs to another company")
        
    expense.status = ExpenseStatus.APPROVED
    await db.commit()
    return {"message": "Expense approved", "status": expense.status.value}

@router.patch("/expenses/{expense_id}/reject")
async def reject_expense(
    expense_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from fastapi import HTTPException
    expense = await db.get(Expense, expense_id)
    if not expense:
        raise HTTPException(404, "Expense not found")
        
    driver = await db.get(Driver, expense.driver_id)
    if not driver or driver.company_id != current_user.company_id:
        raise HTTPException(400, "Unauthorized: Expense belongs to another company")
        
    expense.status = ExpenseStatus.REJECTED
    await db.commit()
    return {"message": "Expense rejected", "status": expense.status.value}

@router.get("/trips/{trip_id}/pod")
async def get_owner_trip_pod(
    trip_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from models.proof_of_delivery import ProofOfDelivery
    from fastapi import HTTPException
    
    trip = await db.get(Trip, trip_id)
    if not trip or trip.company_id != current_user.company_id:
        raise HTTPException(404, "Trip not found or unauthorized")
        
    result = await db.execute(
        select(ProofOfDelivery).where(ProofOfDelivery.trip_id == trip_id)
    )
    pod = result.scalar_one_or_none()
    
    if not pod:
        raise HTTPException(404, "POD not found")
        
    return {
        "id": pod.id,
        "trip_id": pod.trip_id,
        "driver_id": pod.driver_id,
        "signature_url": pod.signature_url,
        "photos": pod.photos or [],
        "invoice_url": pod.invoice_url,
        "remarks": pod.remarks,
        "receiver_name": pod.receiver_name,
        "created_at": pod.created_at
    }

@router.get("/drivers/{driver_id}/documents")
async def get_owner_driver_documents(
    driver_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from fastapi import HTTPException
    
    driver = await db.get(Driver, driver_id)
    if not driver or driver.company_id != current_user.company_id:
        raise HTTPException(404, "Driver not found or unauthorized")
        
    return {
        "license_front_url": driver.license_front_url,
        "license_back_url": driver.license_back_url,
        "aadhaar_front_url": driver.aadhaar_front_url,
        "aadhaar_back_url": driver.aadhaar_back_url,
        "selfie_url": driver.selfie_url,
        "verification_status": driver.verification_status.value if driver.verification_status else None
    }

@router.get("/vehicle/{vehicle_id}/insights")
async def get_vehicle_insights(
    vehicle_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from fastapi import HTTPException
    
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.company_id != current_user.company_id:
        raise HTTPException(404, "Vehicle not found or unauthorized")
        
    # Get active trip
    trip_result = await db.execute(
        select(Trip).where(
            Trip.vehicle_id == vehicle_id,
            Trip.status == TripStatus.IN_PROGRESS
        ).order_by(Trip.id.desc()).limit(1)
    )
    active_trip = trip_result.scalar_one_or_none()
    
    # Get total expenses
    expense_result = await db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
            Expense.vehicle_id == vehicle_id,
            Expense.status == ExpenseStatus.APPROVED
        )
    )
    total_expenses = float(expense_result.scalar() or 0.0)
    
    # Get utilization (count of trips completed)
    completed_trips_result = await db.execute(
        select(func.count(Trip.id)).where(
            Trip.vehicle_id == vehicle_id,
            Trip.status == TripStatus.COMPLETED
        )
    )
    completed_trips = completed_trips_result.scalar() or 0
    
    return {
        "vehicle_id": vehicle.id,
        "active_trip": {
            "id": active_trip.id,
            "origin": active_trip.origin_location,
            "destination": active_trip.destination_location,
            "status": active_trip.status.value,
        } if active_trip else None,
        "total_expenses": total_expenses,
        "completed_trips": completed_trips,
        "utilization_percentage": None, 
        "maintenance_status": None,
        "last_known_location": None
    }

@router.get("/wallet-transactions")
async def get_owner_wallet_transactions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from models.driver_wallet import WalletTransaction
    from models.driver_domain import Driver
    
    result = await db.execute(
        select(WalletTransaction, Driver.name.label("driver_name"))
        .join(Driver, Driver.id == WalletTransaction.driver_id)
        .where(WalletTransaction.company_id == current_user.company_id)
        .order_by(WalletTransaction.created_at.desc())
        .limit(50)
    )
    
    transactions = []
    for tx, driver_name in result:
        transactions.append({
            "id": tx.id,
            "driver_name": driver_name,
            "transaction_type": tx.transaction_type.value if hasattr(tx.transaction_type, 'value') else tx.transaction_type,
            "amount": tx.amount,
            "status": tx.status.value if hasattr(tx.status, 'value') else tx.status,
            "description": tx.description,
            "created_at": tx.created_at,
        })
        
    return transactions
