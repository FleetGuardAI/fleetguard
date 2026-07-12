"""
FleetGuard Pydantic Schemas Package.
"""

from schemas.truck import TruckCreate, TruckUpdate, TruckResponse
from schemas.driver import DriverCreate, DriverUpdate, DriverResponse
from schemas.ticket import TicketCreate, TicketUpdate, TicketResponse, TicketApproval
from schemas.fuel_log import FuelLogCreate, FuelLogResponse, FuelAlertResponse

__all__ = [
    "TruckCreate", "TruckUpdate", "TruckResponse",
    "DriverCreate", "DriverUpdate", "DriverResponse",
    "TicketCreate", "TicketUpdate", "TicketResponse", "TicketApproval",
    "FuelLogCreate", "FuelLogResponse", "FuelAlertResponse",
]
