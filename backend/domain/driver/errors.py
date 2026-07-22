"""
Driver Management Domain - Errors
"""

class DriverError(Exception):
    """Base exception for Driver Domain errors."""
    pass

class DriverNotFound(DriverError):
    pass

class DuplicateDriver(DriverError):
    pass

class DuplicateLicence(DriverError):
    pass

class InvalidDriverState(DriverError):
    pass

class InvalidLicence(DriverError):
    pass

class InvalidIdentifier(DriverError):
    pass
