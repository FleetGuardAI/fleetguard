"""
FleetGuard — Generic Provider Interface
"""

from abc import ABC, abstractmethod
from typing import Optional

from infrastructure.intelligence.core.contributing_factors import EvidenceResult

class BaseContributingFactorProvider(ABC):
    """
    Base class for all evidence providers in the generic Contributing Factor Engine.
    """
    
    @abstractmethod
    async def evaluate(
        self,
        uow,
        anomaly,
        impact
    ) -> Optional[EvidenceResult]:
        pass
