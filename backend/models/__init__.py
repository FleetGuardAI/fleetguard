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
from models.truck import Truck
from models.driver import Driver
from models.ticket import Ticket
from models.fuel_log import FuelLog

# --- Event-Driven Architecture ---
from models.operational_event import OperationalEvent

__all__ = [
    # Auth
    "Company",
    "User",
    "AuthSession",
    "PasswordResetToken",
    # Fleet
    "Truck",
    "Driver",
    "Ticket",
    "FuelLog",
    # Event-Driven Architecture
    "OperationalEvent",
]
