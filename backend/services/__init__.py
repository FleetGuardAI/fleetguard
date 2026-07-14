"""
FleetGuard Services Package.
Business logic services for authentication, WhatsApp, OCR, fuel analysis, and scoring.
"""

from services.auth_service import (
    register_company,
    authenticate_user,
    get_current_user,
    create_token_for_user,
)

__all__ = [
    "register_company",
    "authenticate_user",
    "get_current_user",
    "create_token_for_user",
]
