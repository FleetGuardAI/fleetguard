"""
FleetGuard — Telematics Webhook Router
Handles hardware GPS payloads.
"""
import hmac
from typing import Annotated, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Security, Request, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings, settings as global_settings
from database import get_db
from schemas.telematics import NormalizedHardwareEvent, TelematicsBatchResponse
from services.location_service import LocationService

router = APIRouter(
    prefix="/api/v1/tracking/telematics",
    tags=["Hardware Telematics"],
)

webhook_header = APIKeyHeader(name="X-Telematics-Secret", auto_error=False)


def _get_settings(request: Request) -> Settings:
    return getattr(request.app.state, "settings", global_settings)


def verify_telematics_secret(
    request: Request,
    api_key_header: str = Security(webhook_header)
) -> bool:
    """
    Validates the hardware provider webhook secret using timing-safe comparison (FG-SEC-032).
    """
    settings: Settings = _get_settings(request)
    if not settings.TELEMATICS_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telematics ingestion not configured"
        )
    
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid telematics secret"
        )

    # Constant-time comparison to prevent side-channel timing attacks (FG-SEC-032)
    if not hmac.compare_digest(
        api_key_header.encode("utf-8"),
        settings.TELEMATICS_WEBHOOK_SECRET.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid telematics secret"
        )
    return True


@router.post(
    "/webhook",
    response_model=TelematicsBatchResponse,
    dependencies=[Depends(verify_telematics_secret)],
    status_code=status.HTTP_200_OK
)
async def process_hardware_telematics(
    request: Request,
    payload: List[NormalizedHardwareEvent],
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest a batch of hardware GPS locations.
    """
    settings: Settings = _get_settings(request)
    
    result = await LocationService.process_hardware_batch(
        db=db,
        locations=payload,
        allow_registration_only=settings.ALLOW_REGISTRATION_ONLY_TELEMATICS
    )
    
    await db.commit()
    return result
