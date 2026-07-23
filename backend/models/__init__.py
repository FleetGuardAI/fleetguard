"""
FleetGuard ORM Models Package.
Import all models here so Base.metadata picks them up for table creation.

Import ORDER matters:
  - Company must be imported before User (FK dependency).
  - Auth models are imported first so tenant FK is always resolvable.
"""

# --- Auth / Tenant Models (import first — other models will FK to these) ---
from models.company import Company
from models.user import User
from models.auth_session import AuthSession
from models.password_reset_token import PasswordResetToken

# --- Fleet Models ---
from models.vehicle_domain import Vehicle
from models.driver_domain import Driver
from models.trip_domain import Trip
from models.maintenance_domain import MaintenanceRecord, MaintenanceTask
from models.tyre_domain import Tyre, TyreLifecycleRecord
from models.asset_domain import Asset, AssetHistory, AssetOperationalStatus, AssetHistoryCategory
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus
from models.ticket import Ticket
from models.fuel_log import FuelLog
from models.operational_event import OperationalEvent
from models.evidence import Evidence
#from models.assignment_domain import DriverAssignment
from models.processing_record import ProcessingRecord
from models.processed_event import ProcessedEvent
from models.outbox_event import OutboxEvent, OutboxStatus

# --- Document Intelligence ---
from models.document import Document

__all__ = [
    # Auth
    "Company",
    "User",
    "AuthSession",
    "PasswordResetToken",
    # Fleet
    "Vehicle",
    "Driver",
    "Trip",
    "MaintenanceRecord",
    "MaintenanceTask",
    "Tyre",
    "TyreLifecycleRecord",
    "Asset",
    "AssetHistory",
    "Expense",
    "Ticket",
    "FuelLog",
    # Event-Driven Architecture
    "OperationalEvent",
    "Evidence",
    "FuelState",
    "FuelTransaction",
    "ProcessingRecord",
    "ProcessedEvent",
    "OutboxEvent",
    "OutboxStatus",
    # Document Intelligence
    "Document",
]
