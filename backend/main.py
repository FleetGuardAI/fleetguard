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
from database import create_all_tables

# Import models so they are registered with Base.metadata before create_all_tables
import models  # noqa: F401

# Import routers
from routers.whatsapp import router as whatsapp_router
from routers.dashboard import router as dashboard_router
from routers.tickets import router as tickets_router
from routers.drivers import router as drivers_router
from routers.trucks import router as trucks_router
from routers.fuel import router as fuel_router
from routers.auth import router as auth_router

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

    await create_all_tables()
    logger.info("✅ Database tables created/verified.")

    yield

    logger.info("🛑 FleetGuard TMS shutting down.")


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
app.include_router(drivers_router, prefix=API_PREFIX)
app.include_router(trucks_router, prefix=API_PREFIX)
app.include_router(fuel_router, prefix=API_PREFIX)
app.include_router(auth_router)

logger.info(
    f"📋 Registered routes: "
    f"{[route.path for route in app.routes if hasattr(route, 'path')]}"
)
