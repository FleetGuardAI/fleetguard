"""
FleetGuard TMS — Main Application Entrypoint

FastAPI app with:
- Async lifespan (creates DB tables on startup)
- CORS middleware for React frontend
- All API routers mounted under /api
- Health check endpoint
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import create_all_tables, async_session_factory
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from utils.rate_limiter import limiter
from utils.security_headers import SecurityHeadersMiddleware

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("fleetguard")
from infrastructure.events.kafka_bus import KafkaEventBus
from infrastructure.events.kafka_consumer import KafkaConsumerRunner
# from processing import ProcessingEngineSubscriber - REMOVED
from infrastructure.evidence.providers.ocr import OCREvidenceProvider
from infrastructure.evidence.orchestrator import EvidenceOrchestrator
from infrastructure.evidence.registry import EvidenceProviderRegistry
from services.operational_event_service import OperationalEventService

from dispatchers.event_dispatcher import default_dispatcher

# Application-level event bus singleton.
# Injected into OperationalEventService via get_event_service dependency.
if settings.KAFKA_ENABLED:
    event_bus = KafkaEventBus(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        security_protocol=settings.KAFKA_SECURITY_PROTOCOL,
        sasl_mechanism=settings.KAFKA_SASL_MECHANISM,
        sasl_plain_username=settings.KAFKA_SASL_USERNAME,
        sasl_plain_password=settings.KAFKA_SASL_PASSWORD,
    )
else:
    from infrastructure.events.bus import InProcessEventBus
    event_bus = InProcessEventBus(dispatcher=default_dispatcher)

# Initialize Validation & Enrichment Engine
from infrastructure.validation.registry import ValidationRuleRegistry
from infrastructure.validation.rules.example_fuel_structural_rule import ExampleFuelStructuralRule
from infrastructure.validation.rules.tank_capacity_rule import TankCapacityRule
from infrastructure.validation.rules.expense_location_rule import ExpenseLocationFraudRule
from infrastructure.validation.engine import ValidationEngine
from infrastructure.validation.service import ValidationService
from infrastructure.validation.consumer import ValidationConsumer

# Initialize Validation & Register Rules
validation_registry = ValidationRuleRegistry()
validation_registry.register(ExampleFuelStructuralRule())
validation_registry.register(TankCapacityRule())
validation_registry.register(ExpenseLocationFraudRule())

validation_engine = ValidationEngine(validation_registry)

def event_service_factory(uow) -> OperationalEventService:
    return OperationalEventService(uow, dispatcher=default_dispatcher)

def validation_service_factory(db: async_session_factory) -> ValidationService:
    # Need to pass db inside consumer or instantiate service with factory.
    # Wait, ValidationService needs db_session_factory.
    return ValidationService(
        db_session_factory=async_session_factory,
        engine=validation_engine,
        event_service_factory=event_service_factory
    )

from infrastructure.events.dlq import DeadLetterPublisher
dlq_publisher = DeadLetterPublisher(event_bus=event_bus)

validation_consumer = ValidationConsumer(
    validation_service=ValidationService(
        db_session_factory=async_session_factory,
        engine=validation_engine,
        event_service_factory=event_service_factory
    )
)

# Attach Validation Engine to its own consumer group (Kafka mode only)
validation_consumer_runner = KafkaConsumerRunner(
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    group_id="validation-group",
    topic=settings.KAFKA_OPERATIONAL_EVENTS_TOPIC,
    subscriber=validation_consumer,
    dlq_publisher=dlq_publisher,
    security_protocol=settings.KAFKA_SECURITY_PROTOCOL,
    sasl_mechanism=settings.KAFKA_SASL_MECHANISM,
    sasl_plain_username=settings.KAFKA_SASL_USERNAME,
    sasl_plain_password=settings.KAFKA_SASL_PASSWORD,
) if settings.KAFKA_ENABLED else None

# Initialize Processing Engine
from infrastructure.processing.domain_router import get_default_domain_router
from infrastructure.processing.service import ProcessingService
from infrastructure.processing.consumer import ProcessingConsumer

processing_router = get_default_domain_router()

processing_consumer_instance = ProcessingConsumer(
    processing_service=ProcessingService(
        db_session_factory=async_session_factory,
        router=processing_router,
        event_service_factory=event_service_factory
    )
)

# Attach Processing Engine to its own consumer group (Kafka mode only)
processing_consumer = KafkaConsumerRunner(
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    group_id="processing-group",
    topic=settings.KAFKA_OPERATIONAL_EVENTS_TOPIC,
    subscriber=processing_consumer_instance,
    dlq_publisher=dlq_publisher,
    security_protocol=settings.KAFKA_SECURITY_PROTOCOL,
    sasl_mechanism=settings.KAFKA_SASL_MECHANISM,
    sasl_plain_username=settings.KAFKA_SASL_USERNAME,
    sasl_plain_password=settings.KAFKA_SASL_PASSWORD,
) if settings.KAFKA_ENABLED else None

# Initialize Evidence Framework
evidence_registry = EvidenceProviderRegistry()

# Register OCR Provider
from infrastructure.ocr.provider import MockOCRProvider, GoogleDocumentAIProvider, OCRProvider
from infrastructure.ocr.models import OCRResult
from infrastructure.ocr.openai_provider import OpenAIOCRProvider

class UnconfiguredOCRProvider(OCRProvider):
    async def extract_text(self, file_data: bytes, mime_type: str, document_type: str = "receipt") -> OCRResult:
        raise RuntimeError("AI service temporarily unavailable")

if settings.OCR_PROVIDER.lower() == "openai":
    if not settings.OPENAI_API_KEY:
        logger.warning("⚠️ OPENAI_API_KEY is not set. OCR will return 503 errors.")
        ocr_base_provider = UnconfiguredOCRProvider()
    else:
        ocr_base_provider = OpenAIOCRProvider(api_key=settings.OPENAI_API_KEY)
elif settings.OCR_PROVIDER.lower() == "mock":
    ocr_base_provider = MockOCRProvider()
elif settings.OCR_PROVIDER.lower() == "google":
    ocr_base_provider = GoogleDocumentAIProvider()
elif settings.OCR_PROVIDER.lower() == "ocr_space":
    from infrastructure.ocr.provider import OCRSpaceProvider
    ocr_key = getattr(settings, "OCR_SPACE_API_KEY", None) or os.environ.get("OCR_SPACE_API_KEY")
    if not ocr_key:
        logger.warning("⚠️ OCR_SPACE_API_KEY is not set. OCR will return 503 errors.")
        ocr_base_provider = UnconfiguredOCRProvider()
    else:
        ocr_base_provider = OCRSpaceProvider(api_key=ocr_key)
else:
    raise ValueError(f"Unknown OCR_PROVIDER: {settings.OCR_PROVIDER}")

ocr_evidence_provider = OCREvidenceProvider(
    db_session_factory=async_session_factory,
    provider=ocr_base_provider
)
evidence_registry.register(ocr_evidence_provider)

evidence_orchestrator = EvidenceOrchestrator(
    session_factory=async_session_factory,
    registry=evidence_registry,
    event_service_factory=event_service_factory
)

# Attach Evidence Engine to its own consumer group (Kafka mode only)
evidence_consumer_runner = KafkaConsumerRunner(
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    group_id="evidence-group",
    topic=settings.KAFKA_OPERATIONAL_EVENTS_TOPIC,
    subscriber=evidence_orchestrator,
    dlq_publisher=dlq_publisher,
    security_protocol=settings.KAFKA_SECURITY_PROTOCOL,
    sasl_mechanism=settings.KAFKA_SASL_MECHANISM,
    sasl_plain_username=settings.KAFKA_SASL_USERNAME,
    sasl_plain_password=settings.KAFKA_SASL_PASSWORD,
) if settings.KAFKA_ENABLED else None

# Initialize Fuel Intelligence Engine
from infrastructure.intelligence.fuel_domain.orchestrator import FuelIntelligenceOrchestrator
from infrastructure.intelligence.fuel_domain.consumer import FuelIntelligenceConsumer

fuel_intelligence_consumer = FuelIntelligenceConsumer(
    orchestrator=FuelIntelligenceOrchestrator()
)

# Attach Fuel Intelligence to its own consumer group (Kafka mode only)
fuel_intelligence_consumer_runner = KafkaConsumerRunner(
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    group_id="fie-group",
    topic=settings.KAFKA_OPERATIONAL_EVENTS_TOPIC,
    subscriber=fuel_intelligence_consumer,
    dlq_publisher=dlq_publisher,
    security_protocol=settings.KAFKA_SECURITY_PROTOCOL,
    sasl_mechanism=settings.KAFKA_SASL_MECHANISM,
    sasl_plain_username=settings.KAFKA_SASL_USERNAME,
    sasl_plain_password=settings.KAFKA_SASL_PASSWORD,
) if settings.KAFKA_ENABLED else None

# Register all subscribers with the in-process event dispatcher
default_dispatcher.register_subscriber(evidence_orchestrator)
default_dispatcher.register_subscriber(validation_consumer)
default_dispatcher.register_subscriber(processing_consumer_instance)
default_dispatcher.register_subscriber(fuel_intelligence_consumer)

# Initialize Outbox Pattern
from infrastructure.events.outbox_publisher import OutboxPublisher
from infrastructure.events.outbox_worker import OutboxWorkerRunner

outbox_publisher = OutboxPublisher(db_session_factory=async_session_factory, event_bus=event_bus)
outbox_worker = OutboxWorkerRunner(publisher=outbox_publisher)

# Import models so they are registered with Base.metadata before create_all_tables
import models  # noqa: F401

# Import routers
from routers.dashboard import router as dashboard_router
from routers.tickets import router as tickets_router
from routers.support import router as support_router
# from routers.assignment_domain import router as assignment_domain_router
from routers.driver_domain import router as driver_domain_router
from routers.driver_qualification import router as driver_qualification_router
from routers.trip_domain import router as trip_domain_router
from domain.fuel.api import router as fuel_domain_router
from routers.fuel_domain import router as fuel_domain_ops_router
from routers.maintenance_domain import router as maintenance_domain_router
from routers.tyre_domain import router as tyre_domain_router
from routers.asset_domain import router as asset_domain_router
from routers.expense_domain import router as expense_router
from routers.vehicle_domain import router as vehicle_domain_router
from routers.fuel import router as fuel_router
from routers.auth import router as auth_router
from routers.operational_events import router as operational_events_router
from routers.documents import router as documents_router
from routers.evidence import router as evidence_router
from routers.fleet_intelligence import router as fleet_intelligence_router
from routers.fuel_intelligence import router as fuel_intelligence_router
from routers.copilot import router as copilot_router
from routers.owner_dashboard import router as owner_dashboard_router
from routers.owner_emergency import router as owner_emergency_router
from routers.notifications import router as notifications_router
from routers.location import router as location_router
from routers.telematics import router as telematics_router
from routers.route_intelligence import router as route_intelligence_router

# Import Driver Mobile App routers
from routers.driver_mobile import router as driver_mobile_router
from routers.location_tracking import router as location_tracking_router
from routers.fleet_invite import router as fleet_invite_router
from routers.driver_trips import router as driver_trips_router
from routers.driver_expenses import router as driver_expenses_router
from routers.driver_inspection import router as driver_inspection_router
from routers.driver_pod import router as driver_pod_router
from routers.driver_emergency import router as driver_emergency_router
from routers.driver_wallet import router as driver_wallet_router
from routers.ws_driver import router as ws_driver_router

# --- Admin Internal Portal ---
from routers.admin_auth import router as admin_auth_router
from routers.admin_support import router as admin_support_router
from routers.admin_dashboard import router as admin_dashboard_router
from routers.admin_documents import router as admin_documents_router
from routers.admin_audit import router as admin_audit_router
from routers.admin_passwords import router as admin_passwords_router




# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.
    - Startup: Create all database tables.
    - Shutdown: Cleanup resources.
    """
    logger.info("🚛 FleetGuard TMS starting up...")
    # FG-SEC-003: Enforce dedicated admin signing secret on startup
    from services.admin_auth_service import get_admin_jwt_secret
    get_admin_jwt_secret()
    # FG-SEC-002: Enforce dedicated OTP recipient fingerprint key on startup
    from services.otp_service import get_otp_fingerprint_key
    get_otp_fingerprint_key()
    logger.info(f"   Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    logger.info(f"   OpenAI configured: {bool(settings.OPENAI_API_KEY)}")
    logger.info(f"   Event Bus: {event_bus}")

    logger.info("PRODUCTION CORS ORIGINS: %s", settings.CORS_ORIGINS)
    logger.info("CORS SUPER ADMIN ALLOWED: %s", "https://super-admin-seven-sepia.vercel.app" in settings.CORS_ORIGINS)

    logger.info("✅ PostgreSQL database detected. Alembic manages the schema exclusively.")

    # Database Migrations (Alembic) are now handled exclusively by the CI/CD pipeline
    # (see .github/workflows/backend-migrations.yml) to ensure safe, controlled schema updates.

    # --- MSG91 OTP Configuration Validation ---
    if not settings.OTP_MOCK_MODE and getattr(settings, 'OTP_PROVIDER', 'MSG91').upper() == 'MSG91':
        if not settings.MSG91_AUTH_KEY:
            logger.error("❌ CRITICAL CONFIGURATION ERROR: MSG91_AUTH_KEY is not set in environment variables. OTP sends will fail.")
        if not getattr(settings, 'MSG91_TEMPLATE_ID', None):
            logger.error("❌ CRITICAL CONFIGURATION ERROR: MSG91_TEMPLATE_ID is not set in environment variables. MSG91 Standard OTP API requires a template ID.")

    if settings.KAFKA_ENABLED:
        try:
            await validation_consumer_runner.start()
            await processing_consumer.start()
            await evidence_consumer_runner.start()
            await outbox_worker.start()
            await fuel_intelligence_consumer_runner.start()
            logger.info("✅ Background Kafka runners started.")
        except Exception as e:
            logger.warning(f"⚠️ Could not start background Kafka runners: {e}")
    else:
        logger.info("Kafka workers disabled — KAFKA_ENABLED=False (using InProcessEventBus)")
        try:
            # Replay any pending/crashed outbox events on startup
            replayed = await outbox_publisher.publish_pending()
            if replayed > 0:
                logger.info(f"✅ Recovered and published {replayed} pending outbox events at startup.")
        except Exception as e:
            logger.warning(f"⚠️ Could not replay pending outbox events at startup: {e}")
        try:
            # Start background outbox polling worker for periodic retries of failed/staged events
            await outbox_worker.start()
            logger.info("✅ In-process Outbox polling worker started.")
        except Exception as e:
            logger.warning(f"⚠️ Could not start in-process outbox worker: {e}")

    yield

    logger.info("🛑 FleetGuard TMS shutting down.")
    if settings.KAFKA_ENABLED:
        if validation_consumer_runner:
            await validation_consumer_runner.stop()
        if processing_consumer:
            await processing_consumer.stop()
        if evidence_consumer_runner:
            await evidence_consumer_runner.stop()
        await outbox_worker.stop()
        if fuel_intelligence_consumer_runner:
            await fuel_intelligence_consumer_runner.stop()
        await event_bus.stop()
    else:
        # Gracefully stop the in-process outbox polling worker
        await outbox_worker.stop()


# --- FastAPI App ---
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Transport Management System for fraud prevention, "
        "expense tracking, fuel telematics, and BI reporting."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- Mount Static Files (Uploads) ---
# REMOVED for production security: Files are now retrieved securely via Supabase Storage signed URLs.

# --- CORS & Security Headers Middleware ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
)

# --- Global Exception Handler (Ensures CORS headers are attached even on 500 errors) ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, RateLimitExceeded):
        return _rate_limit_exceeded_handler(request, exc)
    logger.exception(f"Unhandled server error on {request.method} {request.url.path}: {exc}")
    origin = request.headers.get("origin")
    headers = {}
    if origin and origin in settings.CORS_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        headers["Access-Control-Allow-Headers"] = "*"
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred.",
            "error_type": type(exc).__name__,
        },
        headers=headers,
    )


# --- Health Check ---
@app.get("/", tags=["Health"])
async def root() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Detailed health check validating core service readiness."""
    db_status = "connected"
    try:
        from sqlalchemy import text
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        logger.warning(f"Database health check probe failed: {type(e).__name__}")
        db_status = "disconnected"

    is_healthy = (db_status == "connected")
    return {
        "status": "healthy" if is_healthy else "degraded",
        "database": db_status,
        "openai": "configured" if bool(settings.OPENAI_API_KEY) else "not_configured",
    }

@app.get("/api/v1/health/cors", tags=["Health"])
async def cors_health_check() -> dict:
    return {
        "cors_origins": settings.CORS_ORIGINS,
        "super_admin_allowed": "https://super-admin-seven-sepia.vercel.app" in settings.CORS_ORIGINS
    }


# --- Mount Routers ---
API_PREFIX = "/api"

app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(tickets_router, prefix=API_PREFIX)
app.include_router(support_router, prefix="/api/v1")
app.include_router(support_router, prefix=API_PREFIX)
app.include_router(driver_domain_router, prefix=API_PREFIX)
app.include_router(driver_qualification_router, prefix=API_PREFIX)
app.include_router(trip_domain_router, prefix=API_PREFIX)
app.include_router(maintenance_domain_router, prefix=API_PREFIX)
app.include_router(tyre_domain_router, prefix=API_PREFIX)
app.include_router(asset_domain_router, prefix=API_PREFIX)
app.include_router(vehicle_domain_router, prefix=API_PREFIX)
app.include_router(expense_router, prefix=API_PREFIX)
app.include_router(fuel_router, prefix=API_PREFIX)
app.include_router(fuel_domain_router, prefix=API_PREFIX)
app.include_router(fuel_domain_ops_router, prefix=API_PREFIX)
app.include_router(auth_router)                   # carries its own /api/v1/auth prefix
app.include_router(operational_events_router)     # carries its own /api/v1/events prefix
app.include_router(documents_router)              # carries its own /api/v1/documents prefix
app.include_router(evidence_router)               # carries its own /api/v1/events/{event_id}/evidence prefix
app.include_router(fleet_intelligence_router, prefix="/api/v1") # carries /intelligence prefix
app.include_router(fuel_intelligence_router, prefix="/api/v1") # carries /intelligence/fuel prefix
app.include_router(copilot_router, prefix="/api/v1")
app.include_router(owner_dashboard_router)
app.include_router(owner_emergency_router, prefix="/api/v1")
app.include_router(notifications_router)
app.include_router(location_router, prefix="/api")
app.include_router(telematics_router)
app.include_router(route_intelligence_router)


# Mount Driver Mobile App Routers
app.include_router(driver_mobile_router)
app.include_router(location_tracking_router)
app.include_router(fleet_invite_router)
app.include_router(driver_trips_router)
app.include_router(driver_expenses_router)
app.include_router(driver_inspection_router)
app.include_router(driver_pod_router)
app.include_router(driver_emergency_router)
app.include_router(driver_wallet_router)
app.include_router(ws_driver_router)

# Mount Admin Internal Portal Routers
app.include_router(admin_auth_router)
app.include_router(admin_support_router)
app.include_router(admin_dashboard_router)
app.include_router(admin_documents_router)
app.include_router(admin_audit_router)
app.include_router(admin_passwords_router)

logger.info(
    f"📋 Registered routes: "
    f"{[route.path for route in app.routes if hasattr(route, 'path')]}"
)
