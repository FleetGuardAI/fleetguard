"""
FleetGuard TMS — Main Application Entrypoint

FastAPI app with:
- Async lifespan (creates DB tables on startup)
- CORS middleware for React frontend
- All API routers mounted under /api
- Health check endpoint
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import create_all_tables, async_session_factory
from infrastructure.events.kafka_bus import KafkaEventBus
from infrastructure.events.kafka_consumer import KafkaConsumerRunner
# from processing import ProcessingEngineSubscriber - REMOVED
from infrastructure.evidence.providers.ocr import OCREvidenceProvider
from infrastructure.evidence.orchestrator import EvidenceOrchestrator
from infrastructure.evidence.registry import EvidenceProviderRegistry
from services.operational_event_service import OperationalEventService

# Application-level event bus singleton.
# Injected into OperationalEventService via get_event_service dependency.
event_bus = KafkaEventBus(settings.KAFKA_BOOTSTRAP_SERVERS)

# Initialize Validation & Enrichment Engine
from infrastructure.validation.registry import ValidationRuleRegistry
from infrastructure.validation.rules.example_fuel_structural_rule import ExampleFuelStructuralRule
from infrastructure.validation.rules.tank_capacity_rule import TankCapacityRule
from infrastructure.validation.engine import ValidationEngine
from infrastructure.validation.service import ValidationService
from infrastructure.validation.consumer import ValidationConsumer

# Initialize Validation & Register Rules
validation_registry = ValidationRuleRegistry()
validation_registry.register(ExampleFuelStructuralRule())
validation_registry.register(TankCapacityRule())

validation_engine = ValidationEngine(validation_registry)

def event_service_factory(uow) -> OperationalEventService:
    return OperationalEventService(uow)

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

# Attach Validation Engine to its own consumer group
validation_consumer_runner = KafkaConsumerRunner(
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    group_id="validation-group",
    topic=settings.KAFKA_OPERATIONAL_EVENTS_TOPIC,
    subscriber=validation_consumer,
    dlq_publisher=dlq_publisher
)

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

# Attach Processing Engine to its own consumer group
processing_consumer = KafkaConsumerRunner(
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    group_id="processing-group",
    topic=settings.KAFKA_OPERATIONAL_EVENTS_TOPIC,
    subscriber=processing_consumer_instance,
    dlq_publisher=dlq_publisher
)

# Initialize Evidence Framework
evidence_registry = EvidenceProviderRegistry()

# Register OCR Provider
from infrastructure.ocr.provider import MockOCRProvider
ocr_evidence_provider = OCREvidenceProvider(
    db_session_factory=async_session_factory, 
    provider=MockOCRProvider()
)
evidence_registry.register(ocr_evidence_provider)

def event_service_factory(uow) -> OperationalEventService:
    return OperationalEventService(uow)

evidence_consumer_runner = KafkaConsumerRunner(
    bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
    group_id="evidence-group",
    topic=settings.KAFKA_OPERATIONAL_EVENTS_TOPIC,
    subscriber=EvidenceOrchestrator(
        session_factory=async_session_factory,
        registry=evidence_registry,
        event_service_factory=event_service_factory
    ),
    dlq_publisher=dlq_publisher
)

# Initialize Outbox Pattern
from infrastructure.events.outbox_publisher import OutboxPublisher
from infrastructure.events.outbox_worker import OutboxWorkerRunner

outbox_publisher = OutboxPublisher(db_session_factory=async_session_factory, event_bus=event_bus)
outbox_worker = OutboxWorkerRunner(publisher=outbox_publisher)

# Import models so they are registered with Base.metadata before create_all_tables
import models  # noqa: F401

# Import routers
from routers.whatsapp import router as whatsapp_router
from routers.dashboard import router as dashboard_router
from routers.tickets import router as tickets_router
from routers.assignment_domain import router as assignment_domain_router
from domain.fuel.api import router as fuel_domain_router
from routers.maintenance_domain import router as maintenance_domain_router
from routers.tyre_domain import router as tyre_domain_router
from routers.asset_domain import router as asset_domain_router
from routers.expense_domain import router as expense_router
from routers.vehicle_domain import router as vehicle_domain_router
from routers.fuel import router as fuel_router
from routers.fuel_domain import router as fuel_domain_router
from routers.auth import router as auth_router
from routers.operational_events import router as operational_events_router
from routers.documents import router as documents_router
from routers.evidence import router as evidence_router

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("fleetguard")


# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.
    - Startup: Create all database tables.
    - Shutdown: Cleanup resources.
    """
    logger.info("🚛 FleetGuard TMS starting up...")
    logger.info(f"   Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    logger.info(f"   OpenAI configured: {bool(settings.OPENAI_API_KEY)}")
    logger.info(f"   WhatsApp configured: {bool(settings.WHATSAPP_API_TOKEN)}")
    logger.info(f"   Event Bus: {event_bus}")

    await create_all_tables()
    logger.info("✅ Database tables created/verified.")
    
    # Start Kafka Producer
    # await event_bus.start()
    
    # Start Kafka Consumers
    # await validation_consumer.start()
    # await processing_consumer.start()
    # await evidence_consumer_runner.start()
    
    # Start Outbox Worker
    # await outbox_worker.start()

    yield

    logger.info("🛑 FleetGuard TMS shutting down.")
    
    # Stop Outbox Worker
    # await outbox_worker.stop()
    
    # Stop Kafka Consumers
    # await evidence_consumer_runner.stop()
    # await processing_consumer.stop()
    # await validation_consumer.stop()
    
    # Stop Kafka Producer
    await event_bus.stop()


# --- FastAPI App ---
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Transport Management System for fraud prevention, "
        "WhatsApp expense tracking, fuel telematics, and BI reporting."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "openai": "configured" if settings.OPENAI_API_KEY else "not_configured",
        "whatsapp": "configured" if settings.WHATSAPP_API_TOKEN else "not_configured",
    }


# --- Mount Routers ---
API_PREFIX = "/api"

app.include_router(whatsapp_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(tickets_router, prefix=API_PREFIX)
app.include_router(driver_domain_router, prefix=API_PREFIX)
app.include_router(trip_domain_router, prefix=API_PREFIX)
app.include_router(maintenance_domain_router, prefix=API_PREFIX)
app.include_router(tyre_domain_router, prefix=API_PREFIX)
app.include_router(asset_domain_router, prefix=API_PREFIX)
app.include_router(vehicle_domain_router, prefix=API_PREFIX)
app.include_router(expense_router, prefix=API_PREFIX)
app.include_router(fuel_router, prefix=API_PREFIX)
app.include_router(fuel_domain_router, prefix=API_PREFIX)
app.include_router(auth_router)                   # carries its own /api/v1/auth prefix
app.include_router(operational_events_router)     # carries its own /api/v1/events prefix
app.include_router(documents_router)              # carries its own /api/v1/documents prefix
app.include_router(evidence_router)               # carries its own /api/v1/events/{event_id}/evidence prefix

logger.info(
    f"📋 Registered routes: "
    f"{[route.path for route in app.routes if hasattr(route, 'path')]}"
)
