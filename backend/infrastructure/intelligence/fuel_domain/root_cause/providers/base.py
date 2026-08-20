from abc import ABC, abstractmethod

from infrastructure.uow import AbstractUnitOfWork
from models.fuel_anomaly import FuelAnomaly
from models.fuel_financial_impact import FuelFinancialImpact
from infrastructure.intelligence.fuel_domain.root_cause.schemas import RootCauseEvidenceResult

class BaseEvidenceProvider(ABC):
    """
    Base class for all evidence providers in the Root Cause Engine.
    """
    
    @abstractmethod
    async def evaluate(
        self,
        uow: AbstractUnitOfWork,
        anomaly: FuelAnomaly,
        impact: FuelFinancialImpact | None
    ) -> RootCauseEvidenceResult:
        pass
