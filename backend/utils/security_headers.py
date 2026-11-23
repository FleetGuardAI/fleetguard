"""
FleetGuard TMS — HTTP Security Headers Middleware (FG-SEC-049)

Enforces defense-in-depth HTTP security headers across all API responses:
- Strict-Transport-Security (HSTS)
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Content-Security-Policy (CSP)
- Referrer-Policy
- Permissions-Policy
- X-XSS-Protection
- Cross-Origin-Opener-Policy (COOP)
- Cross-Origin-Resource-Policy (CORP)
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that injects production-grade HTTP security headers on all responses."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # 1. Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 2. Prevent clickjacking by forbidding iframe framing
        response.headers["X-Frame-Options"] = "DENY"

        # 3. HTTP Strict Transport Security (HSTS): 1 year + includeSubDomains + preload
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # 4. Strict Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 5. Restrict access to sensitive browser features/hardware APIs
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(self), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"
        )

        # 6. Legacy XSS filter protection for older browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 7. Content Security Policy (CSP)
        # Allows self assets and necessary CDN/Swagger UI assets while blocking untrusted object/frame embeds
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: blob: https:; "
            "style-src 'self' 'unsafe-inline' https:; "
            "script-src 'self' 'unsafe-inline' https:; "
            "font-src 'self' data: https:; "
            "connect-src 'self' https: wss: ws:; "
            "frame-ancestors 'none'; "
            "object-src 'none'; "
            "base-uri 'self';"
        )

        # 8. Cross-Origin isolation policies
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"

        return response
