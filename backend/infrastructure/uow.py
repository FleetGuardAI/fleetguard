"""
FleetGuard — Unit of Work
Abstracts database session management and provides a unified transactional
gateway to all repositories.
"""

from abc import ABC, abstractmethod
from sqlalchemy.ext.asyncio import AsyncSession

# Import all repositories
from repositories.asset_repository import AssetRepository
from repositories.document_repository import DocumentRepository
from repositories.driver_repository import DriverRepository
from repositories.evidence_repository import EvidenceRepository
from repositories.expense_repository import ExpenseRepository
from repositories.fuel_repository import FuelRepository
from repositories.fuel_state_repository import FuelStateRepository
from repositories.maintenance_repository import MaintenanceRepository
from repositories.operational_event_repository import OperationalEventRepository
from repositories.processing_repository import ProcessingRepository
from repositories.trip_repository import TripRepository
from repositories.tyre_repository import TyreRepository
from repositories.vehicle_repository import VehicleRepository
from repositories.outbox_repository import OutboxRepository
from repositories.derived_fuel_metric_repository import DerivedFuelMetricRepository
from repositories.entity_baseline_repository import EntityBaselineRepository
from repositories.fuel_anomaly_repository import FuelAnomalyRepository
from repositories.fuel_financial_impact_repository import FuelFinancialImpactRepository
from repositories.fuel_root_cause_repository import FuelRootCauseRepository
from infrastructure.idempotency.repository import IdempotencyRepository


class RepositoryRegistry:
    """
    Groups all transactional repositories for easy access via UnitOfWork.
    """
    def __init__(self, db: AsyncSession):
        self.asset = AssetRepository(db)
        self.document = DocumentRepository(db)
        self.driver = DriverRepository(db)
        self.evidence = EvidenceRepository(db)
        self.expense = ExpenseRepository(db)
        self.fuel = FuelRepository(db)
        self.fuel_state = FuelStateRepository(db)
        self.maintenance = MaintenanceRepository(db)
        self.operational_event = OperationalEventRepository(db)
        self.processing = ProcessingRepository(db)
        self.trip = TripRepository(db)
        self.tyre = TyreRepository(db)
        self.vehicle = VehicleRepository(db)
        self.outbox = OutboxRepository(db)
        self.derived_fuel_metric = DerivedFuelMetricRepository(db)
        self.entity_baseline = EntityBaselineRepository(db)
        self.fuel_anomaly = FuelAnomalyRepository(db)
        self.fuel_financial_impact = FuelFinancialImpactRepository(db)
        self.fuel_root_cause = FuelRootCauseRepository(db)
        self.idempotency = IdempotencyRepository(db)


class AbstractUnitOfWork(ABC):
    """
    Interface for Unit of Work.
    Services depend on this abstraction, never on SQLAlchemy directly.
    """
    repositories: RepositoryRegistry

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, tb):
        await self.rollback()

    @abstractmethod
    async def commit(self):
        pass

    @abstractmethod
    async def rollback(self):
        pass


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    """
    SQLAlchemy-specific implementation of the Unit of Work.
    """
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.session: AsyncSession = None

    async def __aenter__(self):
        self.session = self.session_factory()
        self.repositories = RepositoryRegistry(self.session)
        await super().__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, tb):
        await super().__aexit__(exc_type, exc_val, tb)
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
