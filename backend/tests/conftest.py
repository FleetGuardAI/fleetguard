import os
import pytest
import pytest_asyncio
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient

from main import app
from database import get_db, Base, get_uow, get_read_uow
from config import settings

# --- 0. MOCK STORAGE SERVICE ---
# We must monkeypatch StorageService BEFORE anything else imports it,
# or just monkeypatch the instance directly since it's a singleton.
import services.file_upload_service as file_upload_service
file_upload_service.storage_service.supabase = file_upload_service.MockSupabaseStorage()
file_upload_service.storage_service.bucket = "test-bucket"

import services.otp_service as otp_service
otp_service.otp_provider = otp_service.MockOTPProvider()
otp_service.settings.OTP_MOCK_MODE = True

# --- 1. SECURITY GUARD & CONFIGURATION ---

# We load TEST_DATABASE_URL. It MUST be explicitly set.
# For local testing convenience without Docker, you can use SQLite:
# TEST_DATABASE_URL=sqlite+aiosqlite:///./test_db.sqlite
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    pytest.exit("TEST_DATABASE_URL is required. Refusing to run tests against DATABASE_URL.")

if TEST_DATABASE_URL == settings.DATABASE_URL:
    pytest.exit("TEST_DATABASE_URL must be separate from DATABASE_URL. Refusing to run tests.")

if "pooler.supabase.com" in TEST_DATABASE_URL:
    pytest.exit("TEST_DATABASE_URL appears to point to production Supabase. Refusing to run.")

print(f"\n[TEST ENVIRONMENT] Using database: {TEST_DATABASE_URL.split('@')[-1] if '@' in TEST_DATABASE_URL else TEST_DATABASE_URL}\n")


# --- 2. ENGINE & SESSION SETUP ---

# We use an async engine tailored to the test database
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

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
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Optional teardown
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# --- 5. TRANSACTION ISOLATION & DEPENDENCY OVERRIDE ---

@pytest_asyncio.fixture(scope="function")
async def db_session():
    """
    Yields an isolated database session. 
    Uses connection-level savepoints (begin_nested) to rollback all changes 
    at the end of the test, guaranteeing no pollution.
    """
    async with test_engine.connect() as conn:
        await conn.begin()
        await conn.begin_nested() # For nested transactions (savepoints)
        
        session = AsyncSession(
            bind=conn,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        
        yield session
        
        await session.close()
        await conn.rollback() # Rolls back everything that happened in the test

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
