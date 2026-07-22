"""
Trip Management Domain - Errors
"""

class TripDomainError(Exception):
    """Base exception for Trip domain errors."""
    pass

class TripNotFound(TripDomainError):
    """Raised when a requested trip cannot be found."""
    pass

class InvalidTripState(TripDomainError):
    """Raised when a requested lifecycle transition is invalid."""
    pass

class ImmutableTripError(TripDomainError):
    """Raised when attempting to modify a completed or cancelled trip."""
    pass
