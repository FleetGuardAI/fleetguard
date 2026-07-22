"""
Fuel Operations Domain - Aggregate Root
"""

import uuid
from typing import List, Tuple, Optional
from datetime import datetime, timezone

from domain.fuel.models import FuelTransaction, TransactionType
from domain.fuel.value_objects import Volume, TankCalibration, Location
from domain.fuel.events import (
    DomainEvent,
    FuelFillRecorded,
    FuelDrainRecorded,
    FuelBalanceUpdated,
    FuelCalibrationUpdated
)
from domain.fuel.validators import validate_balance_bounds

class FuelLedger:
    """
    Aggregate root protecting the mathematical integrity of a vehicle's fuel state.
    """
    def __init__(self, vehicle_id: str):
        self.vehicle_id = vehicle_id
        self.transactions: List[FuelTransaction] = []
        self.calibration: Optional[TankCalibration] = None
        self._balance: float = 0.0

    @property
    def current_balance(self) -> float:
        return self._balance

    def load_from_history(self, transactions: List[FuelTransaction], calibration: Optional[TankCalibration] = None) -> None:
        """Hydrates the ledger and reconstructs the balance from historical transactions."""
        self.transactions = sorted(transactions, key=lambda t: t.timestamp)
        self.calibration = calibration
        self._recalculate_balance()

    def _recalculate_balance(self) -> None:
        balance = 0.0
        for tx in self.transactions:
            if tx.transaction_type == TransactionType.FILL:
                balance += tx.volume.liters
            elif tx.transaction_type in (TransactionType.DRAIN, TransactionType.BURN):
                balance -= tx.volume.liters
            elif tx.transaction_type == TransactionType.ADJUSTMENT:
                balance += tx.volume.liters
        self._balance = balance

    def record_fill(self, volume: Volume, driver_id: Optional[uuid.UUID] = None, trip_id: Optional[uuid.UUID] = None, location: Optional[Location] = None) -> Tuple[FuelTransaction, List[DomainEvent]]:
        new_balance = self._balance + volume.liters
        validate_balance_bounds(new_balance, self.calibration)

        tx = FuelTransaction(
            vehicle_id=self.vehicle_id,
            transaction_type=TransactionType.FILL,
            volume=volume,
            driver_assignment_id=driver_id,
            trip_id=trip_id,
            location=location
        )
        self.transactions.append(tx)
        self._balance = new_balance

        event = FuelFillRecorded(
            vehicle_id=self.vehicle_id,
            transaction_id=tx.transaction_id,
            volume_liters=volume.liters,
            new_balance_liters=self._balance,
            driver_assignment_id=driver_id,
            trip_id=trip_id
        )
        return tx, [event, FuelBalanceUpdated(vehicle_id=self.vehicle_id, new_balance_liters=self._balance)]

    def record_drain(self, volume: Volume, driver_id: Optional[uuid.UUID] = None, trip_id: Optional[uuid.UUID] = None, location: Optional[Location] = None) -> Tuple[FuelTransaction, List[DomainEvent]]:
        new_balance = self._balance - volume.liters
        validate_balance_bounds(new_balance, self.calibration)

        tx = FuelTransaction(
            vehicle_id=self.vehicle_id,
            transaction_type=TransactionType.DRAIN,
            volume=volume,
            driver_assignment_id=driver_id,
            trip_id=trip_id,
            location=location
        )
        self.transactions.append(tx)
        self._balance = new_balance

        event = FuelDrainRecorded(
            vehicle_id=self.vehicle_id,
            transaction_id=tx.transaction_id,
            volume_liters=volume.liters,
            new_balance_liters=self._balance,
            driver_assignment_id=driver_id,
            trip_id=trip_id
        )
        return tx, [event, FuelBalanceUpdated(vehicle_id=self.vehicle_id, new_balance_liters=self._balance)]

    def update_calibration(self, calibration: TankCalibration) -> List[DomainEvent]:
        # Just setting it, does not mutate balance, but future transactions will be bounded by it.
        self.calibration = calibration
        return [FuelCalibrationUpdated(vehicle_id=self.vehicle_id, max_capacity_liters=calibration.max_capacity_liters)]
