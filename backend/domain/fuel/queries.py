"""
Fuel Operations Domain - Query Layer
"""

from typing import List, Optional
from domain.fuel.repository import BaseFuelRepository
from domain.fuel.projections import FuelBalanceSummary, FuelHistoryProjection

class FuelQueryService:
    def __init__(self, repository: BaseFuelRepository):
        self._repository = repository

    def get_current_balance(self, vehicle_id: str) -> FuelBalanceSummary:
        ledger = self._repository.get_ledger(vehicle_id)
        capacity = ledger.calibration.max_capacity_liters if ledger.calibration else None
        return FuelBalanceSummary(
            vehicle_id=vehicle_id,
            current_balance_liters=ledger.current_balance,
            max_capacity_liters=capacity
        )

    def get_transaction_history(self, vehicle_id: str) -> List[FuelHistoryProjection]:
        ledger = self._repository.get_ledger(vehicle_id)
        return [
            FuelHistoryProjection(
                transaction_id=tx.transaction_id,
                vehicle_id=tx.vehicle_id,
                transaction_type=tx.transaction_type.value,
                volume_liters=tx.volume.liters,
                timestamp=tx.timestamp,
                driver_assignment_id=tx.driver_assignment_id,
                trip_id=tx.trip_id
            ) for tx in ledger.transactions
        ]
