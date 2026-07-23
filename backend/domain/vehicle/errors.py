"""
Vehicle Management Domain - Errors
"""

class VehicleError(Exception):
    """Base exception for Vehicle Domain errors."""
    pass

class VehicleNotFound(VehicleError):
    pass

class DuplicateRegistration(VehicleError):
    pass

class InvalidVehicleState(VehicleError):
    pass

class InvalidVehicleConfiguration(VehicleError):
    pass

class InvalidIdentifier(VehicleError):
    pass
