import os
import sys
import re
import pytest

# --- 1. ENVIRONMENT CONFIGURATION (MUST BE SET BEFORE ANY APPLICATION IMPORTS) ---
os.environ["TESTING"] = "True"
os.environ["KAFKA_ENABLED"] = "False"
os.environ["OTP_MOCK_MODE"] = "True"
os.environ["DEBUG"] = "False"
os.environ["OCR_PROVIDER"] = "mock"
os.environ["GOOGLE_DOCUMENT_AI_PROJECT_ID"] = "test"
os.environ["GOOGLE_DOCUMENT_AI_LOCATION"] = "us"
os.environ["GOOGLE_MAPS_API_KEY"] = "test"
os.environ["OPENAI_API_KEY"] = "mock-openai-key"
os.environ["GEMINI_API_KEY"] = ""
os.environ["LLM_BASE_URL"] = ""

def mask_db_url(url: str) -> str:
    """Mask credentials in database URL to prevent credential leakage."""
    if not url:
        return ""
    return re.sub(r"://([^:@]+):([^@]+)@", r"://\1:***@", url)

def validate_approved_test_database(url: str) -> None:
    """
    Hard security guard ensuring tests only ever run against an approved, isolated test database.
    Aborts immediately if the URL points to production, a cloud provider, or an unapproved target.
    """
    masked = mask_db_url(url)
    url_lower = url.lower()

    # 1. Reject any production / cloud indicators
    forbidden = [
        "supabase",
        "pooler",
        "aws-",
        "rds.amazonaws",
        "azure",
        "gcp",
        "neon.tech",
        "elephantsql",
        "render.com",
        "railway.app",
        "lckabcseysgzlvkjpgtg",
    ]
    for f in forbidden:
        if f in url_lower:
            pytest.exit(
                f"CRITICAL TEST ISOLATION FAILURE: Refusing connection to cloud/production database ({masked}) during tests! "
                "Aborting test startup immediately to protect remote data."
            )

    # 2. Positive allowlist validation: strictly SQLite test DB or local PostgreSQL test DB
    is_approved_sqlite = "sqlite" in url_lower and ("test" in url_lower or ":memory:" in url_lower)
    is_approved_local_pg = (
        ("postgresql" in url_lower or "asyncpg" in url_lower)
        and ("localhost" in url_lower or "127.0.0.1" in url_lower)
        and "test" in url_lower
    )

    if not (is_approved_sqlite or is_approved_local_pg):
        pytest.exit(
            f"CRITICAL TEST ISOLATION FAILURE: Database URL '{masked}' is not an approved isolated test database! "
            "Tests are strictly restricted to isolated test databases (e.g. SQLite test_db or local localhost test DB)."
        )

# Dedicated isolated test database URL
TEST_DB_URL = os.environ.get("TEST_DATABASE_URL", "sqlite+aiosqlite:///./test_db.sqlite")
validate_approved_test_database(TEST_DB_URL)
os.environ["TEST_DATABASE_URL"] = TEST_DB_URL
os.environ["DATABASE_URL"] = TEST_DB_URL

# --- 2. SQLITE JSONB COMPILATION FALLBACK ---
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

# --- 3. MOCK EXTERNAL SERVICES & PROVIDERS (DETERMINISTIC TEST BEHAVIOR) ---
import services.file_upload_service as file_upload_service
file_upload_service.storage_service._supabase = file_upload_service.MockSupabaseStorage()
file_upload_service.storage_service.bucket = "test-bucket"

import services.otp_service as otp_service
otp_service.otp_provider = otp_service.MockOTPProvider()
otp_service.settings.OTP_MOCK_MODE = True

import services.ai_extraction_service as ai_extraction_service
ai_extraction_service.ai_extractor.client = None

# --- 4. CLEANUP HOOK ---
@pytest.fixture(scope="session", autouse=True)
async def cleanup_engine():
    yield
    try:
        from database import engine
        await engine.dispose()
    except Exception:
        pass
