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
from models.owner_pairing_token import OwnerPairingToken

# --- Fleet Models ---
from models.vehicle_domain import Vehicle
from models.driver_domain import Driver, VerificationStatus, DutyStatus
from models.trip_domain import Trip
from models.maintenance_domain import MaintenanceRecord, MaintenanceTask
from models.tyre_domain import Tyre, TyreLifecycleRecord
from models.asset_domain import Asset, AssetHistory, AssetOperationalStatus, AssetHistoryCategory
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus
from models.ticket import Ticket
from models.fuel_log import FuelLog
from models.fuel_domain import FuelTransaction, FuelState
from models.operational_event import OperationalEvent
from models.evidence import Evidence
#from models.assignment_domain import DriverAssignment
from models.processing_record import ProcessingRecord
from models.processed_event import ProcessedEvent
from models.outbox_event import OutboxEvent, OutboxStatus

# --- Document Intelligence ---
from models.document import Document

# --- FIE ---
from models.derived_fuel_metrics import DerivedFuelMetric
from models.entity_baseline import EntityBaseline
from models.fuel_anomaly import FuelAnomaly
from models.fuel_financial_impact import FuelFinancialImpact
from models.fuel_root_cause import FuelRootCauseAnalysis, FuelRootCauseEvidence

# --- Driver App Models ---
from models.fleet_invite import FleetInvite
from models.location_tracking import DriverLocation, LocationAlert
from models.vehicle_inspection import VehicleInspection
from models.proof_of_delivery import ProofOfDelivery
from models.emergency import EmergencyAlert
from models.driver_wallet import WalletTransaction
from models.trip_start_selfie import TripStartSelfie

# --- Owner App ---
from models.notification import Notification, NotificationCategory

__all__ = [
    # Auth
    "Company",
    "User",
    "AuthSession",
    "PasswordResetToken",
    "OwnerPairingToken",
    # Fleet
    "Vehicle",
    "Driver",
    "VerificationStatus",
    "DutyStatus",
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
    "ProcessingRecord",
    "ProcessedEvent",
    "OutboxEvent",
    "OutboxStatus",
    # Document Intelligence
    "Document",
    # FIE
    "DerivedFuelMetric",
    "EntityBaseline",
    "FuelAnomaly",
    "FuelFinancialImpact",
    "FuelRootCauseAnalysis",
    "FuelRootCauseEvidence",
    # Driver App
    "FleetInvite",
    "DriverLocation",
    "LocationAlert",
    "VehicleInspection",
    "ProofOfDelivery",
    "EmergencyAlert",
    "WalletTransaction",
    "TripStartSelfie",
    "Notification",
]
