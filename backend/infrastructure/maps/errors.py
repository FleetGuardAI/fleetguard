"""
Maps Service - Errors
"""

class MapsServiceError(Exception):
    """Base exception for all Maps Service errors."""
    pass

class MapsServiceUnavailable(MapsServiceError):
    """Raised when the maps provider is unreachable or returns 5xx."""
    pass

class InvalidCoordinate(MapsServiceError):
    """Raised when a provided coordinate is structurally invalid."""
    pass

class InvalidAddress(MapsServiceError):
    """Raised when a provided address is invalid or unresolvable."""
    pass

class RouteCalculationFailed(MapsServiceError):
    """Raised when a route cannot be calculated between coordinates."""
    pass
