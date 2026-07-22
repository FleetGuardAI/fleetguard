"""
FleetGuard — Domain Router
Maps Operational Events (by EventType) to their target Business Domains.
Supports deterministic routing to multiple domains per event.
"""

from typing import Callable, Sequence, Any
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.uow import AbstractUnitOfWork
from models.operational_event import EventType
from schemas.operational_event import OperationalEventResponse

from services.assignment_service import AssignmentService
from domain.fuel.service import FuelService
from services.driver_service import DriverService
from services.trip_service import TripService
from services.maintenance_service import MaintenanceService
from services.tyre_service import TyreService
from services.asset_service import AssetService
from services.expense_service import ExpenseService


# A Domain Handler is a factory that takes an AbstractUnitOfWork and returns a service instance
DomainHandlerFactory = Callable[[AbstractUnitOfWork], Any]

class DomainRouter:
    """
    Registry for routing OperationalEvents to Business Domain services.
    Decouples the Processing Engine from specific domain classes.
    Routes explicitly by EventType, allowing multiple domains per event.
    """
    
    def __init__(self):
        self._routes: dict[EventType, list[DomainHandlerFactory]] = {}
        
    def register(self, event_type: EventType, handler_factory: DomainHandlerFactory) -> None:
        """Register a domain handler factory for an event type. Preserves registration order."""
        if event_type not in self._routes:
            self._routes[event_type] = []
        self._routes[event_type].append(handler_factory)
        
    def resolve(self, event: OperationalEventResponse, uow: AbstractUnitOfWork) -> Sequence[Any]:
        """
        Return initialized service instances for all domains that should process
        the given event.
        """
        factories = self._routes.get(event.event_type, [])
        return [factory(uow) for factory in factories]


# ===========================================================================
# Global Default Router
# ===========================================================================

def get_default_domain_router() -> DomainRouter:
    """
    Initialize and return the default domain router with explicit EventType mapping.
    Multiple domains can be registered for the same event type.
    """
    router = DomainRouter()
    
    # --- FUEL_FILLED ---
    router.register(EventType.FUEL_FILLED, lambda uow: FuelService(uow))
    router.register(EventType.FUEL_FILLED, lambda uow: ExpenseService(uow))
    
    # --- VEHICLE_* ---
    for evt in (EventType.VEHICLE_ASSIGNED, EventType.VEHICLE_UNASSIGNED, EventType.VEHICLE_STATUS_CHANGED):
        router.register(evt, lambda uow: VehicleService(uow))
        
    # --- DRIVER_* ---
    for evt in (EventType.DRIVER_ASSIGNED, EventType.DRIVER_UNASSIGNED, EventType.DRIVER_STATUS_CHANGED):
        router.register(evt, lambda uow: DriverService(uow))
        
    # --- TRIP_* ---
    for evt in (EventType.TRIP_CREATED, EventType.TRIP_STARTED, EventType.TRIP_PAUSED, EventType.TRIP_RESUMED, EventType.TRIP_COMPLETED, EventType.TRIP_CANCELLED, EventType.TRIP_DRIVER_ASSIGNED, EventType.TRIP_VEHICLE_ASSIGNED):
        router.register(evt, lambda uow: TripService(uow))
            
    # --- MAINTENANCE_* ---
    for evt in (EventType.MAINTENANCE_CREATED, EventType.MAINTENANCE_SCHEDULED, EventType.MAINTENANCE_STARTED, EventType.MAINTENANCE_COMPLETED, EventType.MAINTENANCE_CANCELLED, EventType.MAINTENANCE_OVERDUE, EventType.MAINTENANCE_TASK_ADDED, EventType.MAINTENANCE_TASK_COMPLETED):
        router.register(evt, lambda uow: MaintenanceService(uow))
        if evt == EventType.MAINTENANCE_COMPLETED:
            router.register(evt, lambda uow: ExpenseService(uow))
            
    # --- TYRE_* ---
    for evt in (EventType.TYRE_REGISTERED, EventType.TYRE_INSTALLED, EventType.TYRE_REMOVED, EventType.TYRE_ROTATED, EventType.TYRE_REPAIRED, EventType.TYRE_RETREADED, EventType.TYRE_RETIRED, EventType.TYRE_REPLACED, EventType.TYRE_PRESSURE_ALERT):
        router.register(evt, lambda uow: TyreService(uow))
        
    # --- ASSET_* ---
    for evt in (EventType.ASSET_REGISTERED, EventType.ASSET_INSTALLED, EventType.ASSET_REMOVED, EventType.ASSET_CALIBRATED, EventType.ASSET_REPAIRED, EventType.ASSET_REPLACED, EventType.ASSET_RETIRED):
        router.register(evt, lambda uow: AssetService(uow))
        if evt in (EventType.ASSET_REPAIRED, EventType.ASSET_REPLACED):
            router.register(evt, lambda uow: ExpenseService(uow))
            
    # --- EXPENSE_* ---
    for evt in (EventType.EXPENSE_ADDED, EventType.EXPENSE_APPROVED, EventType.EXPENSE_REJECTED):
        router.register(evt, lambda uow: ExpenseService(uow))
    
    return router
