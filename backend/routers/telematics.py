"""
FleetGuard / Vahan — Universal Telematics Ingestion Router
Handles hardware GPS payloads from multi-protocol gateways, Traccar forwarders,
direct cellular trackers, and webhook integrations.
"""
import logging
from typing import Annotated, Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Security, Request, status, Query
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings, settings as global_settings
from database import get_db
from schemas.telematics import NormalizedHardwareEvent, TelematicsBatchResponse
from services.location_service import LocationService
from services.traccar_service import TraccarService
from infrastructure.gps.registry import create_default_registry

logger = logging.getLogger("fleetguard.tracking.telematics")

router = APIRouter(
    prefix="/api/v1/tracking/telematics",
    tags=["Hardware Telematics"],
)

webhook_header = APIKeyHeader(name="X-Telematics-Secret", auto_error=False)


def _get_settings(request: Request) -> Settings:
    app_state = getattr(getattr(request, "app", None), "state", None)
    return getattr(app_state, "settings", global_settings) if app_state else global_settings


def verify_telematics_secret(
    request: Request,
    api_key_header: Optional[str] = Security(webhook_header)
) -> bool:
    """
    Validates the hardware provider webhook secret strictly from X-Telematics-Secret header.
    Query-string fallback is explicitly rejected to prevent credential leakage in proxy and server logs.
    """
    active_settings = _get_settings(request)
    expected_secret = getattr(active_settings, "TELEMATICS_WEBHOOK_SECRET", None)
    if not expected_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telematics ingestion not configured"
        )
    
    if not api_key_header or api_key_header != expected_secret:
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
    Ingest a batch of normalized hardware GPS locations.
    """
    active_settings = _get_settings(request)
    allow_reg = getattr(active_settings, "ALLOW_REGISTRATION_ONLY_TELEMATICS", False)
    
    result = await LocationService.process_hardware_batch(
        db=db,
        locations=payload,
        allow_registration_only=allow_reg
    )
    
    await db.commit()
    return result


@router.post(
    "/traccar",
    response_model=TelematicsBatchResponse,
    dependencies=[Depends(verify_telematics_secret)],
    status_code=status.HTTP_200_OK
)
async def process_traccar_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest GPS event forwarded by Traccar GPS server.
    Accepts single position JSON, wrapped position JSON, or array of positions.
    """
    body = await request.json()
    items = body if isinstance(body, list) else [body]
    
    normalized_events: List[NormalizedHardwareEvent] = []
    for raw_item in items:
        if isinstance(raw_item, dict):
            event = TraccarService.parse_forward_payload(raw_item)
            if event.device_imei:
                normalized_events.append(event)
                
    if not normalized_events:
        return TelematicsBatchResponse(accepted=0, duplicates=0, rejected=len(items), items=[])

    active_settings = _get_settings(request)
    allow_reg = getattr(active_settings, "ALLOW_REGISTRATION_ONLY_TELEMATICS", False)
    
    result = await LocationService.process_hardware_batch(
        db=db,
        locations=normalized_events,
        allow_registration_only=allow_reg
    )
    await db.commit()
    return result


@router.post(
    "/report",
    response_model=TelematicsBatchResponse,
    dependencies=[Depends(verify_telematics_secret)],
    status_code=status.HTTP_200_OK
)
async def process_direct_protocol_report(
    request: Request,
    provider: str = Query("generic", description="Provider/protocol key: generic, teltonika, queclink, ais140, gt06, tk103, mqtt"),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingests raw vendor payload for specified protocol (GT06, AIS-140, Teltonika, TK103, etc.)
    and normalizes via the Universal GPS Gateway framework.
    """
    body = await request.json()
    items = body if isinstance(body, list) else [body]
    
    registry = create_default_registry()
    try:
        provider_instance = registry.get_provider(provider)
    except KeyError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Unsupported provider/protocol '{provider}'")

    normalized_events: List[NormalizedHardwareEvent] = []
    for item in items:
        try:
            gps_pos = provider_instance.receive(item)
            norm_event = NormalizedHardwareEvent(
                device_imei=gps_pos.device_id,
                latitude=gps_pos.latitude,
                longitude=gps_pos.longitude,
                timestamp=gps_pos.timestamp,
                speed=gps_pos.speed,
                heading=gps_pos.heading,
                accuracy=gps_pos.accuracy,
                ignition_status=gps_pos.ignition,
                source_metadata=gps_pos.metadata
            )
            normalized_events.append(norm_event)
        except Exception as e:
            logger.warning(f"Failed to normalize report for provider {provider}: {e}")

    if not normalized_events:
        return TelematicsBatchResponse(accepted=0, duplicates=0, rejected=len(items), items=[])

    active_settings = _get_settings(request)
    allow_reg = getattr(active_settings, "ALLOW_REGISTRATION_ONLY_TELEMATICS", False)
    
    result = await LocationService.process_hardware_batch(
        db=db,
        locations=normalized_events,
        allow_registration_only=allow_reg
    )
    await db.commit()
    return result
