"""
FleetGuard — Dashboard API Router
Aggregation endpoints for the Owner BI Dashboard KPIs and summary data.
"""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database import get_db
from models.truck import Truck
from models.driver import Driver
from models.ticket import Ticket, TicketStatus, RiskLevel
from models.fuel_log import FuelLog
from models.user import User
from schemas.ticket import DashboardKPIs
from services.auth_service import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/kpis", response_model=DashboardKPIs)
async def get_dashboard_kpis(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardKPIs:
    """
    Fetch top-level KPI card data for the owner dashboard.
    Returns KPIs scoped to the logged-in user's company: active trucks, pending approvals,
    theft alerts, flagged drivers, and expense totals for today and this month.
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Active trucks for this company
    active_trucks_result = await db.execute(
        select(func.count(Truck.id)).where(
            Truck.is_active == True,  # noqa: E712
            Truck.company_id == current_user.company_id
        )
    )
    active_trucks = active_trucks_result.scalar() or 0

    # Pending approvals for this company
    pending_result = await db.execute(
        select(func.count(Ticket.id))
        .join(Truck, Ticket.truck_id == Truck.id)
        .where(
            Ticket.status == TicketStatus.PENDING,
            Truck.company_id == current_user.company_id
        )
    )
    pending_approvals = pending_result.scalar() or 0

    # Theft alerts (unresolved fuel theft alerts in the last 30 days) for this company
    thirty_days_ago = now - timedelta(days=30)
    theft_result = await db.execute(
        select(func.count(FuelLog.id))
        .join(Truck, FuelLog.truck_id == Truck.id)
        .where(
            FuelLog.is_theft_alert == True,  # noqa: E712
            FuelLog.timestamp >= thirty_days_ago,
            Truck.company_id == current_user.company_id
        )
    )
    theft_alerts = theft_result.scalar() or 0

    # Flagged drivers (risk_score > 50) for this company
    flagged_result = await db.execute(
        select(func.count(Driver.id)).where(
            Driver.risk_score > 50,
            Driver.is_active == True,  # noqa: E712
            Driver.company_id == current_user.company_id
        )
    )
    flagged_drivers = flagged_result.scalar() or 0

    # Total approved expenses — today for this company
    expenses_today_result = await db.execute(
        select(func.coalesce(func.sum(Ticket.amount), 0.0))
        .join(Truck, Ticket.truck_id == Truck.id)
        .where(
            Ticket.status == TicketStatus.APPROVED,
            Ticket.updated_at >= today_start,
            Truck.company_id == current_user.company_id
        )
    )
    total_expenses_today = float(expenses_today_result.scalar() or 0)

    # Total approved expenses — this month for this company
    expenses_month_result = await db.execute(
        select(func.coalesce(func.sum(Ticket.amount), 0.0))
        .join(Truck, Ticket.truck_id == Truck.id)
        .where(
            Ticket.status == TicketStatus.APPROVED,
            Ticket.updated_at >= month_start,
            Truck.company_id == current_user.company_id
        )
    )
    total_expenses_month = float(expenses_month_result.scalar() or 0)

    return DashboardKPIs(
        active_trucks=active_trucks,
        pending_approvals=pending_approvals,
        theft_alerts=theft_alerts,
        flagged_drivers=flagged_drivers,
        total_expenses_today=total_expenses_today,
        total_expenses_month=total_expenses_month,
    )


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    """
    Fetch recent ticket activity for the logged-in user's company dashboard activity feed.
    Returns the most recent tickets with driver and truck info.
    """
    result = await db.execute(
        select(Ticket, Driver.name, Truck.license_plate)
        .join(Driver, Ticket.driver_id == Driver.id)
        .join(Truck, Ticket.truck_id == Truck.id)
        .where(Truck.company_id == current_user.company_id)
        .order_by(Ticket.created_at.desc())
        .limit(limit)
    )
    rows = result.all()

    return [
        {
            "id": ticket.id,
            "issue_type": ticket.issue_type,
            "amount": ticket.amount,
            "status": ticket.status.value,
            "risk_level": ticket.risk_level.value,
            "driver_name": driver_name,
            "truck_plate": truck_plate,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        }
        for ticket, driver_name, truck_plate in rows
    ]
