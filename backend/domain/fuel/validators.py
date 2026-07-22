"""
Fuel Operations Domain - Validators
"""

from domain.fuel.errors import CapacityExceededError, NegativeBalanceError
from domain.fuel.value_objects import TankCalibration

def validate_balance_bounds(new_balance: float, calibration: TankCalibration | None) -> None:
    if new_balance < 0:
        raise NegativeBalanceError(f"Fuel balance cannot be negative: {new_balance}L")
        
    if calibration and new_balance > calibration.max_capacity_liters:
        raise CapacityExceededError(f"New balance {new_balance}L exceeds tank capacity {calibration.max_capacity_liters}L")
