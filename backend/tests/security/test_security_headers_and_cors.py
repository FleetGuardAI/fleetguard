"""
FleetGuard TMS — Security Verification Suite: Phase B, Batch 5
Tests:
1. FG-SEC-049: Production HTTP Security Headers Middleware (HSTS, CSP, X-Frame-Options, nosniff, etc.)
2. FG-SEC-048: Strict CORS configuration (trusted origins allowed, untrusted origins rejected, no wildcard reflection)
3. FG-SEC-046: GitHub Actions Workflow least-privilege permission verification
"""

import os
import glob
from starlette.testclient import TestClient

from main import app
from config import settings


# ==============================================================================
# FG-SEC-049: HTTP Security Headers Verification
# ==============================================================================

def test_security_headers_present_on_api_endpoints():
    """
    FG-SEC-049: Verify that production-grade HTTP security headers are enforced
    across API responses to prevent XSS, clickjacking, MIME sniffing, and downgrade attacks.
    """
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200

    headers = response.headers

    # 1. MIME Sniffing protection
    assert headers.get("X-Content-Type-Options") == "nosniff"

    # 2. Clickjacking protection (Framing denied)
    assert headers.get("X-Frame-Options") == "DENY"

    # 3. HTTP Strict Transport Security (HSTS)
    hsts = headers.get("Strict-Transport-Security", "")
    assert "max-age=31536000" in hsts
    assert "includeSubDomains" in hsts

    # 4. Referrer Policy
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    # 5. Permissions Policy
    perm_policy = headers.get("Permissions-Policy", "")
    assert "geolocation=(self)" in perm_policy
    assert "camera=()" in perm_policy
    assert "microphone=()" in perm_policy

    # 6. Content Security Policy (CSP)
    csp = headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "object-src 'none'" in csp

    # 7. Cross-Origin Policies
    assert headers.get("Cross-Origin-Opener-Policy") == "same-origin"
    assert headers.get("Cross-Origin-Resource-Policy") == "cross-origin"


# ==============================================================================
# FG-SEC-048: Strict CORS Configuration Verification
# ==============================================================================

def test_cors_trusted_origin_accepted():
    """
    FG-SEC-048: Authorized frontend domains receive Access-Control headers with credentials.
    """
    client = TestClient(app)
    trusted_origin = "http://localhost:5173"

    response = client.get("/", headers={"Origin": trusted_origin})
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == trusted_origin
    assert response.headers.get("Access-Control-Allow-Credentials") == "true"


def test_cors_untrusted_origin_rejected():
    """
    FG-SEC-048: Untrusted/arbitrary external origins are denied CORS access
    and never reflected back in Access-Control-Allow-Origin with credentials.
    """
    client = TestClient(app)
    malicious_origin = "https://malicious-attacker-domain.com"

    response = client.get("/", headers={"Origin": malicious_origin})
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") is None


def test_cors_preflight_handling():
    """
    FG-SEC-048: OPTIONS preflight requests for allowed origins succeed,
    while untrusted origins do not receive allow headers.
    """
    client = TestClient(app)

    # Allowed origin preflight
    resp_trusted = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        }
    )
    assert resp_trusted.status_code == 200
    assert resp_trusted.headers.get("Access-Control-Allow-Origin") == "http://localhost:5173"

    # Untrusted origin preflight
    resp_evil = client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "https://evil-site.org",
            "Access-Control-Request-Method": "POST",
        }
    )
    assert resp_evil.headers.get("Access-Control-Allow-Origin") is None


# ==============================================================================
# FG-SEC-046: GitHub Actions Workflow Permissions Verification
# ==============================================================================

def test_github_workflows_permissions_read_all():
    """
    FG-SEC-046: Verify that all GitHub Actions workflow files declare top-level
    least-privilege permissions ('read-all' or 'contents: read') to prevent token abuse.
    """
    # Navigate from backend/tests/security/test_*.py -> repo root
    security_dir = os.path.dirname(os.path.abspath(__file__))
    tests_dir = os.path.dirname(security_dir)
    backend_dir = os.path.dirname(tests_dir)
    repo_root = os.path.dirname(backend_dir)
    workflow_dir = os.path.join(repo_root, ".github", "workflows")

    workflow_files = glob.glob(os.path.join(workflow_dir, "*.yml"))
    assert len(workflow_files) >= 4, f"Expected at least 4 workflow files, found {len(workflow_files)}"

    for wf_path in workflow_files:
        with open(wf_path, "r", encoding="utf-8") as f:
            content = f.read()

        basename = os.path.basename(wf_path)
        assert "permissions:" in content, f"Workflow {basename} is missing top-level permissions declaration"
        assert (
            "permissions: read-all" in content
            or "contents: read" in content
        ), f"Workflow {basename} does not enforce least-privilege read permissions"
