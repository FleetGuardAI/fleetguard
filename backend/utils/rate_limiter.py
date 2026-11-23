"""
FleetGuard TMS — Rate Limiter Utility (FG-SEC-021)
Centralized SlowAPI rate limiter configuration using client IP (with X-Forwarded-For support).
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from config import settings


def get_client_ip(request: Request) -> str:
    """Extract client IP, inspecting X-Forwarded-For header when behind reverse proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # First IP in the comma-separated list is the original client IP
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_client_ip,
    default_limits=["300/minute"],
    headers_enabled=False,
    enabled=getattr(settings, "RATE_LIMIT_ENABLED", True),
)
