"""
Driver Management Domain - Queries
"""

import uuid
from typing import List
from domain.driver.repository import BaseDriverRepository
from domain.driver.projections import DriverSummary

class DriverQueryService:
    """
    Handles read-only queries.
    """
    def __init__(self, repository: BaseDriverRepository):
        self.repository = repository

    def drivers_by_organization(self, organization_id: uuid.UUID) -> List[DriverSummary]:
        drivers = self.repository.find_by_organization(organization_id)
        return [DriverSummary.from_domain(d) for d in drivers]

    def search(self, **kwargs) -> List[DriverSummary]:
        drivers = self.repository.search(**kwargs)
        return [DriverSummary.from_domain(d) for d in drivers]
