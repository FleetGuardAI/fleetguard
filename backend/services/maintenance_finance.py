from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import logging
import uuid

from models.maintenance_domain import MaintenanceRecord, MaintenanceStatus, MaintenanceCategory
from models.expense_domain import Expense, ExpenseStatus, ExpenseCategory
from models.user import User

logger = logging.getLogger("fleetguard.maintenance_finance")

async def ensure_maintenance_expense(db: AsyncSession, maintenance: MaintenanceRecord):
    """
    Ensures the correct financial Expense exists for a MaintenanceRecord.
    If COMPLETED and cost > 0:
        - If no Expense exists, create ONE.
        - If Expense exists and is PENDING, update amount.
        - If Expense is APPROVED, do NOT modify.
    """
    if maintenance.status != MaintenanceStatus.COMPLETED or not maintenance.cost or maintenance.cost <= 0:
        # Do not create expense if not completed or cost is 0
        return

    # If expense already linked, try to update it
    if maintenance.expense_id:
        expense = await db.get(Expense, maintenance.expense_id)
        if expense:
            if expense.status == ExpenseStatus.PENDING:
                expense.amount = maintenance.cost
                db.add(expense)
            else:
                logger.debug(f"Expense {expense.id} for maintenance {maintenance.id} is already approved/finalized.")
            return

    # Create new Expense
    expense_category = ExpenseCategory.MAINTENANCE
    # We could refine the category based on preventive/corrective, but MAINTENANCE is standard.

    new_expense = Expense(
        company_id=maintenance.company_id,
        business_id=f"EXP-MNT-{str(uuid.uuid4())[:8]}",
        vehicle_id=maintenance.vehicle_id,
        driver_id=maintenance.driver_id,
        trip_id=maintenance.trip_id,
        category=expense_category,
        amount=maintenance.cost,
        status=ExpenseStatus.PENDING,
        expense_date=maintenance.completed_date or datetime.now(timezone.utc),
        description=f"Auto-generated for maintenance {maintenance.business_id}",
        origin_type="maintenance",
        origin_id=str(maintenance.id)
    )
    db.add(new_expense)
    await db.flush() # flush to get ID
    
    maintenance.expense_id = new_expense.id
    db.add(maintenance)
