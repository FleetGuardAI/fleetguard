import os
import pytest
import pytest_asyncio
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

os.environ["OCR_PROVIDER"] = "mock"
os.environ["GOOGLE_DOCUMENT_AI_PROJECT_ID"] = "test"
os.environ["GOOGLE_DOCUMENT_AI_LOCATION"] = "us"
os.environ["GOOGLE_MAPS_API_KEY"] = "test"
os.environ["TEST_DATABASE_URL"] = "sqlite+aiosqlite:///./test_db.sqlite"

from main import app
from database import get_db, Base, get_uow, get_read_uow
from config import settings

# --- 0. MOCK STORAGE SERVICE ---
# We must monkeypatch StorageService BEFORE anything else imports it,
# or just monkeypatch the instance directly since it's a singleton.
import services.file_upload_service as file_upload_service
file_upload_service.storage_service._supabase = file_upload_service.MockSupabaseStorage()
file_upload_service.storage_service.bucket = "test-bucket"

import services.otp_service as otp_service
otp_service.otp_provider = otp_service.MockOTPProvider()
otp_service.settings.OTP_MOCK_MODE = True

# --- 1. SECURITY GUARD & CONFIGURATION ---
import re

def mask_db_url(url: str) -> str:
    if not url:
        return ""
    return re.sub(r"://([^:@]+):([^@]+)@", r"://\1:***@", url)

def validate_approved_test_database(url: str) -> None:
    masked = mask_db_url(url)
    url_lower = url.lower()
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
                "Aborting test run immediately to protect remote data."
            )
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

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "sqlite+aiosqlite:///./test_db.sqlite")
validate_approved_test_database(TEST_DATABASE_URL)
validate_approved_test_database(settings.DATABASE_URL)

print(f"\n[TEST ENVIRONMENT] Using database: {mask_db_url(TEST_DATABASE_URL)}\n")


# --- 2. ENGINE & SESSION SETUP ---
from database import engine, AsyncSessionLocal
test_engine = engine
TestSessionLocal = AsyncSessionLocal

# --- 3. EVENT LOOP SCOPING (Fixes "Event loop is closed") ---

@pytest.fixture(scope="session")
def event_loop():
    """
    Creates a single event loop for the entire test session.
    This prevents 'RuntimeError: Event loop is closed' when background tasks 
    from previous tests overlap with pytest-asyncio tearing down function-scoped loops.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# --- 4. SCHEMA INITIALIZATION ---

@pytest_asyncio.fixture(scope="session", autouse=True)
async def initialize_test_database():
    """
    Initializes the schema on the test database.
    Since we might be using SQLite for testing (which is compatible via JSONB fallback and Uuid),
    we use Base.metadata.create_all for broad compatibility in the isolated test environment.
    """
    import models  # noqa: F401 - Ensure all models are registered on Base.metadata
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Optional teardown
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def auth_headers():
    from utils.security import create_access_token
    from models.user import UserRole
    token = create_access_token(data={
        "sub": "1",
        "company_id": 1,
        "role": UserRole.COMPANY_ADMIN.value,
    })
    return {"Authorization": f"Bearer {token}"}

# --- 5. TRANSACTION ISOLATION & DEPENDENCY OVERRIDE ---

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """
    Yields an isolated database session for testing using the test engine session factory,
    and cleans up all table data before and after each test to guarantee complete test isolation.
    """
    from database import async_session_factory, Base
    async with async_session_factory() as session:
        try:
            for table in reversed(Base.metadata.sorted_tables):
                await session.execute(table.delete())
            await session.commit()
        except Exception:
            await session.rollback()

        yield session

        try:
            for table in reversed(Base.metadata.sorted_tables):
                await session.execute(table.delete())
            await session.commit()
        except Exception:
            await session.rollback()

from infrastructure.uow import SqlAlchemyUnitOfWork, AbstractUnitOfWork, RepositoryRegistry

@pytest.fixture(scope="function")
def client(db_session):
    """
    FastAPI TestClient with the `get_db`, `get_uow`, and `get_read_uow` dependencies 
    securely overridden to use our transactional test session.
    """
    async def override_get_db():
        yield db_session

    async def override_get_uow():
        class TestUoW(SqlAlchemyUnitOfWork):
            def __init__(self):
                self.session_factory = None
                
            async def __aenter__(self):
                self.session = db_session
                self.repositories = RepositoryRegistry(self.session)
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                # Don't close the shared db_session
                if exc_type:
                    await self.rollback()

        async with TestUoW() as uow:
            yield uow

    async def override_get_read_uow():
        class _TestSessionUoW(AbstractUnitOfWork):
            def __init__(self):
                self._session = db_session
                self.repositories = RepositoryRegistry(db_session)

            async def commit(self):
                await self._session.commit()

            async def rollback(self):
                await self._session.rollback()

        uow = _TestSessionUoW()
        yield uow

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_uow] = override_get_uow
    app.dependency_overrides[get_read_uow] = override_get_read_uow
    
    with TestClient(app) as test_client:
        yield test_client
        
    app.dependency_overrides.clear()
