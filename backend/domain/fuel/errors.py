"""
Fuel Operations Domain - Errors
"""

class FuelDomainError(Exception):
    pass

class CapacityExceededError(FuelDomainError):
    pass

class NegativeBalanceError(FuelDomainError):
    pass

class TankCalibrationMissingError(FuelDomainError):
    pass
