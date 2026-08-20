"""
FleetGuard Pydantic Schemas Package.
"""

from schemas.vehicle_domain import VehicleResponse
from schemas.driver_domain import DriverResponse
from schemas.trip_domain import TripResponse
from schemas.maintenance_domain import MaintenanceRecordResponse
from schemas.tyre_domain import TyreResponse
from schemas.asset_domain import AssetResponse
from schemas.expense_domain import ExpenseResponse
from schemas.ticket import TicketCreate, TicketUpdate, TicketResponse, TicketApproval
from schemas.fuel_log import FuelLogCreate, FuelLogResponse, FuelAlertResponse
from schemas.auth import (
    CompanyRegistrationRequest,
    CompanyUpdateRequest,
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
    OwnerQRLoginRequest,
    OwnerQRPairingResponse,
)
from schemas.operational_event import (
    OperationalEventCreate,
    OperationalEventResponse,
    OperationalEventUpdate,
)
from schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
)
from schemas.evidence import (
    EvidenceCreate,
    EvidenceResponse,
    EvidenceStatusUpdate,
)

__all__ = [
    "VehicleResponse",
    "DriverResponse",
    "TripResponse",
    "MaintenanceRecordResponse",
    "TyreResponse",
    "AssetResponse",
    "ExpenseResponse",
    "TicketCreate",
    "TicketUpdate",
    "TicketResponse",
    "TicketApproval",
    "FuelLogCreate",
    "FuelLogResponse",
    "FuelAlertResponse",

    # Auth Schemas
    "CompanyRegistrationRequest",
    "CompanyUpdateRequest",
    "LoginRequest",
    "TokenResponse",
    "CompanyOut",
    "UserOut",
    "RegisterCompanyResponse",
    "MeResponse",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "ForgotPasswordResponse",
    "GenericMessageResponse",
    "OwnerQRLoginRequest",
    "OwnerQRPairingResponse",

    # Event-Driven Architecture Schemas
    "OperationalEventCreate",
    "OperationalEventResponse",
    "OperationalEventUpdate",

    # Document Intelligence
    "DocumentCreate",
    "DocumentResponse",
    "DocumentUpdate",

    # Evidence Framework
    "EvidenceCreate",
    "EvidenceResponse",
    "EvidenceStatusUpdate",
]