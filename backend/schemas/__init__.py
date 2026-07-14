"""
FleetGuard Pydantic Schemas Package.
"""

from schemas.truck import TruckCreate, TruckUpdate, TruckResponse
from schemas.driver import DriverCreate, DriverUpdate, DriverResponse
from schemas.ticket import TicketCreate, TicketUpdate, TicketResponse, TicketApproval
from schemas.fuel_log import FuelLogCreate, FuelLogResponse, FuelAlertResponse
from schemas.auth import (
    CompanyRegistrationRequest,
    LoginRequest,
    TokenResponse,
    CompanyOut,
    UserOut,
    RegisterCompanyResponse,
    MeResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ForgotPasswordResponse,
    GenericMessageResponse,
)
from schemas.operational_event import (
    OperationalEventCreate,
    OperationalEventUpdate,
    OperationalEventResponse,
)

__all__ = [
    "TruckCreate", "TruckUpdate", "TruckResponse",
    "DriverCreate", "DriverUpdate", "DriverResponse",
    "TicketCreate", "TicketUpdate", "TicketResponse", "TicketApproval",
    "FuelLogCreate", "FuelLogResponse", "FuelAlertResponse",

    # Auth Schemas
    "CompanyRegistrationRequest",
    "LoginRequest",
    "TokenResponse",
    "CompanyOut",
    "UserOut",
    "RegisterCompanyResponse",
    "MeResponse",
]

