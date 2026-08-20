"""
FleetGuard — Dashboard KPI Router
Aggregated metrics for the React Dashboard.

Security: All endpoints require authentication and are scoped
to the authenticated user's company_id.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.vehicle_domain import Vehicle
from models.driver_domain import Driver
from models.trip_domain import Trip, TripStatus
from models.ticket import Ticket, TicketStatus, RiskLevel
from services.auth_service import get_current_user
from models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/kpis")
async def get_dashboard_kpis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get aggregate KPIs for the dashboard.
    All metrics are scoped to the authenticated user's company.
    """
    company_id = current_user.company_id

    # Vehicle stats — scoped to company
    vehicle_result = await db.execute(
        select(
            func.count(Vehicle.id).label("total"),
            func.count(case((Vehicle.status == "active", 1))).label("active"),
            func.count(case((Vehicle.status == "maintenance", 1))).label("maintenance"),
        ).where(Vehicle.company_id == company_id)
    )
    v = vehicle_result.one()

    # Driver stats — scoped to company
    driver_result = await db.execute(
        select(
            func.count(Driver.id).label("total"),
            func.count(case((Driver.status == "active", 1))).label("active"),
        ).where(Driver.company_id == company_id)
    )
    d = driver_result.one()

    # Trip stats — scoped to company
    trip_result = await db.execute(
        select(
            func.count(Trip.id).label("total"),
            func.count(case((Trip.status == TripStatus.IN_PROGRESS, 1))).label("active"),
            func.count(case((Trip.status == TripStatus.COMPLETED, 1))).label("completed"),
        ).where(Trip.company_id == company_id)
    )
    t = trip_result.one()

    # Ticket stats — scoped to company via driver->company relationship
    ticket_result = await db.execute(
        select(
            func.count(Ticket.id).label("total"),
            func.count(case((Ticket.status == TicketStatus.PENDING, 1))).label("pending"),
            func.count(case((Ticket.risk_level == RiskLevel.HIGH, 1))).label("high_risk"),
            func.count(case((Ticket.risk_level == RiskLevel.CRITICAL, 1))).label("critical_risk"),
            func.coalesce(func.sum(Ticket.amount), 0).label("total_amount"),
        )
        .join(Driver, Ticket.driver_id == Driver.id)
        .where(Driver.company_id == company_id)
    )
    tk = ticket_result.one()

    return {
        "vehicles": {
            "total": v.total,
            "active": v.active,
            "maintenance": v.maintenance,
        },
        "drivers": {
            "total": d.total,
            "active": d.active,
        },
        "trips": {
            "total": t.total,
            "active": t.active,
            "completed": t.completed,
        },
        "tickets": {
            "total": tk.total,
            "pending": tk.pending,
            "high_risk": tk.high_risk,
            "critical_risk": tk.critical_risk,
            "total_amount": float(tk.total_amount),
        },
    }


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get recent ticket activity for the dashboard.
    Scoped to the authenticated user's company.
    """
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
            "type": ticket.issue_type,
            "amount": ticket.amount,
            "status": ticket.status.value,
            "risk_level": ticket.risk_level.value,
            "driver_name": driver_name,
            "truck_plate": truck_plate,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        }
        for ticket, driver_name, truck_plate in rows
    ]
