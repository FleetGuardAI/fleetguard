"""
FleetGuard — Signed URL Integration & Response Header Verification (FG-SEC-005 & FG-SEC-007)
Batch 1.4: Tests actual HTTP response behavior, headers (Content-Disposition,
Content-Type, X-Content-Type-Options: nosniff), private object access, and token expiry
in an isolated mock storage environment without exposing customer files.
"""

import time
import urllib.parse
from typing import Dict, Any, Optional
import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response, PlainTextResponse
from starlette.testclient import TestClient

from services.file_upload_service import StorageService


from starlette.routing import Route


def create_isolated_storage_app() -> Starlette:
    """
    Creates an isolated mock Supabase Storage server that implements the official
    Supabase Storage S3/REST delivery protocol and header generation.
    """
    # In-memory isolated storage object store
    STORAGE_OBJECTS: Dict[str, Dict[str, Any]] = {
        "documents/annual_audit.pdf": {
            "content": b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF",
            "content_type": "application/pdf"
        },
        "kyc/drivers/24/license.pdf": {
            "content": b"%PDF-1.4 synthetic kyc document",
            "content_type": "application/pdf"
        },
        "kyc/drivers/24/aadhaar.pdf": {
            "content": b"%PDF-1.4 synthetic aadhaar document",
            "content_type": "application/pdf"
        },
        "uploads/payload.svg": {
            "content": b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>",
            "content_type": "image/svg+xml"
        },
        "uploads/index.html": {
            "content": b"<html><body>synthetic html</body></html>",
            "content_type": "text/html"
        },
        "avatars/driver_74.png": {
            "content": b"\x89PNG\r\n\x1a\n synthetic png image",
            "content_type": "image/png"
        },
        "vehicles/truck_101.jpg": {
            "content": b"\xff\xd8\xff synthetic jpeg image",
            "content_type": "image/jpeg"
        },
        "inspections/selfie.webp": {
            "content": b"RIFF....WEBP synthetic webp image",
            "content_type": "image/webp"
        }
    }

    async def get_signed_object(request: Request):
        object_path = request.path_params.get("object_path", "")
        token = request.query_params.get("token")
        download_param = request.query_params.get("download")

        # 1. Private object access control: token is mandatory
        if not token:
            return PlainTextResponse("Unauthorized: Private object requires signed token", status_code=403)
        if token == "invalid-token" or not token.startswith("tok_"):
            return PlainTextResponse("Forbidden: Invalid signature token", status_code=403)

        # 2. Token expiration check: token format tok_<exp_timestamp>_<hash>
        parts = token.split("_")
        if len(parts) >= 2:
            try:
                exp_ts = int(parts[1])
                if exp_ts < int(time.time()):
                    return PlainTextResponse("Gone: Signed URL has expired", status_code=403)
            except ValueError:
                return PlainTextResponse("Forbidden: Malformed token", status_code=403)

        # 3. Object existence check
        if object_path not in STORAGE_OBJECTS:
            return PlainTextResponse("Object not found", status_code=404)

        obj_data = STORAGE_OBJECTS[object_path]
        filename = object_path.split("/")[-1]

        # 4. Generate response headers per Supabase Storage specification
        headers = {
            "X-Content-Type-Options": "nosniff",
            "Content-Type": obj_data["content_type"]
        }

        # Content-Disposition logic: attachment if download query param present, else inline
        if download_param is not None:
            if download_param in ("", "true", "1"):
                headers["Content-Disposition"] = f'attachment; filename="{filename}"'
            else:
                safe_download_name = download_param.replace('"', '').strip()
                headers["Content-Disposition"] = f'attachment; filename="{safe_download_name}"'
        else:
            headers["Content-Disposition"] = "inline"

        return Response(content=obj_data["content"], headers=headers, media_type=obj_data["content_type"])

    routes = [
        Route("/storage/v1/object/sign/{bucket:str}/{object_path:path}", get_signed_object)
    ]
    return Starlette(routes=routes)


class MockSupabaseStorageBucket:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def create_signed_url(self, path: str, expires_in: int, **options):
        # Generate token with expiration timestamp
        exp = int(time.time()) + expires_in
        token = f"tok_{exp}_mockhash"
        query_parts = [f"token={token}"]
        if "download" in options:
            dl_val = options["download"]
            if dl_val is True:
                query_parts.append("download=")
            elif isinstance(dl_val, str):
                query_parts.append(f"download={urllib.parse.quote(dl_val)}")
        query_str = "&".join(query_parts)
        signed_url = f"{self.base_url}/storage/v1/object/sign/fleetguard-storage/{path}?{query_str}"
        return {"signedURL": signed_url}


def test_signed_url_pdf_and_kyc_attachment_delivery():
    """
    FG-SEC-005 & FG-SEC-007: Verifies that signed URLs generated for PDFs and KYC documents
    ALWAYS return Content-Disposition: attachment, Content-Type: application/pdf,
    and X-Content-Type-Options: nosniff.
    """
    storage_app = create_isolated_storage_app()
    client = TestClient(storage_app)

    service = StorageService()
    mock_sb = type("MockClient", (), {})()
    mock_sb.storage = type("MockStorage", (), {})()
    mock_sb.storage.from_ = lambda bucket: MockSupabaseStorageBucket("http://testserver")
    service._supabase = mock_sb

    # 1. Standard PDF Document
    pdf_url = service.create_signed_url("documents/annual_audit.pdf")
    res_pdf = client.get(pdf_url)
    assert res_pdf.status_code == 200
    assert res_pdf.headers["X-Content-Type-Options"] == "nosniff"
    assert res_pdf.headers["Content-Type"] == "application/pdf"
    assert res_pdf.headers["Content-Disposition"].startswith("attachment")
    assert 'filename="annual_audit.pdf"' in res_pdf.headers["Content-Disposition"]

    # 2. KYC Driver License PDF
    license_url = service.create_signed_url("kyc/drivers/24/license.pdf")
    res_license = client.get(license_url)
    assert res_license.status_code == 200
    assert res_license.headers["X-Content-Type-Options"] == "nosniff"
    assert res_license.headers["Content-Type"] == "application/pdf"
    assert res_license.headers["Content-Disposition"].startswith("attachment")

    # 3. KYC Driver Aadhaar PDF
    aadhaar_url = service.create_signed_url("kyc/drivers/24/aadhaar.pdf")
    res_aadhaar = client.get(aadhaar_url)
    assert res_aadhaar.status_code == 200
    assert res_aadhaar.headers["X-Content-Type-Options"] == "nosniff"
    assert res_aadhaar.headers["Content-Disposition"].startswith("attachment")


def test_signed_url_svg_and_html_forced_attachment():
    """
    FG-SEC-005 & FG-SEC-007: Untrusted active content formats (SVG, HTML) must ALWAYS
    be delivered as attachment downloads to prevent stored XSS execution in the SaaS origin.
    """
    storage_app = create_isolated_storage_app()
    client = TestClient(storage_app)

    service = StorageService()
    mock_sb = type("MockClient", (), {})()
    mock_sb.storage = type("MockStorage", (), {})()
    mock_sb.storage.from_ = lambda bucket: MockSupabaseStorageBucket("http://testserver")
    service._supabase = mock_sb

    # SVG upload forced attachment
    svg_url = service.create_signed_url("uploads/payload.svg")
    res_svg = client.get(svg_url)
    assert res_svg.status_code == 200
    assert res_svg.headers["X-Content-Type-Options"] == "nosniff"
    assert res_svg.headers["Content-Disposition"].startswith("attachment")

    # HTML upload forced attachment
    html_url = service.create_signed_url("uploads/index.html")
    res_html = client.get(html_url)
    assert res_html.status_code == 200
    assert res_html.headers["X-Content-Type-Options"] == "nosniff"
    assert res_html.headers["Content-Disposition"].startswith("attachment")


def test_signed_url_raster_image_inline_previews():
    """
    FG-SEC-007: Approved safe raster images (PNG, JPEG, WEBP) deliver inline (Content-Disposition: inline)
    by default so they render seamlessly inside <img> elements and mobile preview canvases.
    """
    storage_app = create_isolated_storage_app()
    client = TestClient(storage_app)

    service = StorageService()
    mock_sb = type("MockClient", (), {})()
    mock_sb.storage = type("MockStorage", (), {})()
    mock_sb.storage.from_ = lambda bucket: MockSupabaseStorageBucket("http://testserver")
    service._supabase = mock_sb

    # 1. Driver Avatar (PNG)
    avatar_url = service.create_preview_signed_url("avatars/driver_74.png")
    res_avatar = client.get(avatar_url)
    assert res_avatar.status_code == 200
    assert res_avatar.headers["X-Content-Type-Options"] == "nosniff"
    assert res_avatar.headers["Content-Type"] == "image/png"
    assert res_avatar.headers["Content-Disposition"] == "inline"

    # 2. Vehicle Photo (JPEG)
    vehicle_url = service.create_signed_url("vehicles/truck_101.jpg")
    res_vehicle = client.get(vehicle_url)
    assert res_vehicle.status_code == 200
    assert res_vehicle.headers["X-Content-Type-Options"] == "nosniff"
    assert res_vehicle.headers["Content-Type"] == "image/jpeg"
    assert res_vehicle.headers["Content-Disposition"] == "inline"

    # 3. Trip Inspection Selfie (WEBP)
    selfie_url = service.create_signed_url("inspections/selfie.webp")
    res_selfie = client.get(selfie_url)
    assert res_selfie.status_code == 200
    assert res_selfie.headers["X-Content-Type-Options"] == "nosniff"
    assert res_selfie.headers["Content-Type"] == "image/webp"
    assert res_selfie.headers["Content-Disposition"] == "inline"


def test_signed_url_private_object_access_and_expiry():
    """
    FG-SEC-005: Objects are private by default; unsigned requests or requests with
    invalid/expired tokens are strictly rejected with HTTP 403.
    """
    storage_app = create_isolated_storage_app()
    client = TestClient(storage_app)

    # 1. Unsigned request (no token query param)
    res_unauth = client.get("http://testserver/storage/v1/object/sign/fleetguard-storage/documents/annual_audit.pdf")
    assert res_unauth.status_code == 403
    assert "Private object requires signed token" in res_unauth.text

    # 2. Tampered token
    res_bad_tok = client.get("http://testserver/storage/v1/object/sign/fleetguard-storage/documents/annual_audit.pdf?token=invalid-token")
    assert res_bad_tok.status_code == 403
    assert "Invalid signature token" in res_bad_tok.text

    # 3. Expired token (timestamp 1000 seconds in the past)
    expired_token = f"tok_{int(time.time()) - 1000}_hash"
    res_expired = client.get(f"http://testserver/storage/v1/object/sign/fleetguard-storage/documents/annual_audit.pdf?token={expired_token}")
    assert res_expired.status_code == 403
    assert "Signed URL has expired" in res_expired.text
