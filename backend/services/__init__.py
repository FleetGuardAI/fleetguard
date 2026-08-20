"""
FleetGuard Services Package.

This package is the public interface for all service-layer operations.
No router or external module should import from individual service files
directly — always import from `services`.

Modules
-------
auth_service              — company registration, login, JWT, current_user dependency
operational_event_service — create, read, and update Operational Events
"""

from services.auth_service import (
    register_company,
    authenticate_user,
    get_current_user,
    create_token_for_user,
    create_forgot_password_request,
    reset_password_with_token,
    logout_user,
    _oauth2_scheme,
    request_otp,
    resend_otp,
    verify_otp,
)

from services.operational_event_service import (
    OperationalEventService,
    EventServiceError,
    EventNotFound,
    EventWriteError,
)

from services.document_service import (
    DocumentService,
    DocumentServiceError,
    DocumentNotFound,
)

from services.evidence_service import (
    EvidenceService,
    EvidenceServiceError,
    EventDoesNotExistError,
    EvidenceNotFound,
)

__all__ = [
    # Auth
    "register_company",
    "authenticate_user",
    "get_current_user",
    "create_token_for_user",
    "create_forgot_password_request",
    "reset_password_with_token",
    "logout_user",
    "_oauth2_scheme",
    "request_otp",
    "resend_otp",
    "verify_otp",

    # Operational Events
    "OperationalEventService",
    "EventServiceError",
    "EventNotFound",
    "EventWriteError",

    # Document Intelligence
    "DocumentService",
    "DocumentServiceError",
    "DocumentNotFound",

    # Evidence Framework
    "EvidenceService",
    "EvidenceServiceError",
    "EventDoesNotExistError",
    "EvidenceNotFound",
]