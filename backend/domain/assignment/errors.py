"""
Assignment Management Domain - Errors
"""

class AssignmentDomainError(Exception):
    """Base class for assignment domain errors."""
    pass


class InvalidAssignmentState(AssignmentDomainError):
    """Raised when an assignment transition is invalid."""
    pass


class AssignmentConflictError(AssignmentDomainError):
    """Raised when an assignment violates conflict invariants (e.g., driver already assigned to an active vehicle)."""
    pass


class AssignmentNotFound(AssignmentDomainError):
    """Raised when an assignment cannot be found."""
    pass


class AssignmentValidationFailed(AssignmentDomainError):
    """Raised when an assignment fails validation constraints."""
    pass
