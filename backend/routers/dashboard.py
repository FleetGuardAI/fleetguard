"""
FleetGuard — Dashboard API Router
Aggregation endpoints for the Owner BI Dashboard KPIs and summary data.
"""

from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.vehicle_domain import Vehicle
from models.driver_domain import Driver
from models.ticket import Ticket, TicketStatus, RiskLevel
from models.fuel_log import FuelLog
from schemas.ticket import DashboardKPIs

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/kpis", response_model=DashboardKPIs)
async def get_dashboard_kpis(db: AsyncSession = Depends(get_db)) -> DashboardKPIs:
    """
    Fetch top-level KPI card data for the owner dashboard.
    Returns: active trucks, pending approvals, theft alerts, flagged drivers,
    and expense totals for today and this month.
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Active trucks (now vehicles)
    active_vehicles_result = await db.execute(
        select(func.count(Vehicle.id)).where(Vehicle.status == "ACTIVE")  # noqa: E712
    )
    active_trucks = active_vehicles_result.scalar() or 0

    # Pending approvals
    pending_result = await db.execute(
        select(func.count(Ticket.id)).where(Ticket.status == TicketStatus.PENDING)
    )
    pending_approvals = pending_result.scalar() or 0

    # Theft alerts (unresolved fuel theft alerts in the last 30 days)
    thirty_days_ago = now - timedelta(days=30)
    theft_result = await db.execute(
        select(func.count(FuelLog.id)).where(
            FuelLog.is_theft_alert == True,  # noqa: E712
            FuelLog.timestamp >= thirty_days_ago,
        )
    )
    theft_alerts = theft_result.scalar() or 0

    # Flagged drivers (risk_score > 50) - Temporarily disabled for Driver Domain Foundation refactor
    flagged_drivers = 0

    # Total approved expenses — today
    expenses_today_result = await db.execute(
        select(func.coalesce(func.sum(Ticket.amount), 0.0)).where(
            Ticket.status == TicketStatus.APPROVED,
            Ticket.updated_at >= today_start,
        )
    )
    total_expenses_today = float(expenses_today_result.scalar() or 0)

    # Total approved expenses — this month
    expenses_month_result = await db.execute(
        select(func.coalesce(func.sum(Ticket.amount), 0.0)).where(
            Ticket.status == TicketStatus.APPROVED,
            Ticket.updated_at >= month_start,
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
) -> list[dict]:
    """
    Fetch recent ticket activity for the dashboard activity feed.
    Returns the most recent tickets with driver and truck info.
    """
    result = await db.execute(
        select(Ticket, Driver.name, Vehicle.registration_number)
        .join(Driver, Ticket.driver_id == Driver.id)
        .join(Vehicle, Ticket.vehicle_id == Vehicle.id)
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
            "truck_plate": vehicle_reg,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        }
        for ticket, driver_name, vehicle_reg in rows
    ]
