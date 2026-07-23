"""
GPS Gateway Framework - Executor
"""

import time
import logging
import traceback
from typing import Dict, Any

from infrastructure.gps.registry import GPSProviderRegistry
from infrastructure.gps.models import GPSProcessingResult, GPSProcessingStatus, GPSPosition
from infrastructure.gps.events import PositionRecorded, IgnitionStateChanged

logger = logging.getLogger(__name__)


class GPSGatewayExecutor:
    """
    Executes the GPS telemetry ingestion pipeline.
    """
    def __init__(self, registry: GPSProviderRegistry):
        self.registry = registry

    def process_payload(self, provider_key: str, payload: Dict[str, Any]) -> GPSProcessingResult:
        start_time = time.perf_counter()
        
        try:
            # 1. Resolve Provider
            try:
                provider = self.registry.get_provider(provider_key)
            except KeyError:
                return GPSProcessingResult(
                    processing_status=GPSProcessingStatus.PROVIDER_NOT_FOUND,
                    error_message=f"No provider found for key: {provider_key}",
                    execution_time_ms=(time.perf_counter() - start_time) * 1000
                )

            # 2. Validate Payload
            try:
                provider.validate(payload)
            except ValueError as e:
                return GPSProcessingResult(
                    processing_status=GPSProcessingStatus.VALIDATION_FAILED,
                    error_message=str(e),
                    execution_time_ms=(time.perf_counter() - start_time) * 1000
                )
                
            # 3. Normalize Data to GPSPosition
            try:
                gps_position = provider.normalize(payload)
            except Exception as e:
                logger.error(f"Normalization failed for payload {payload}: {str(e)}")
                return GPSProcessingResult(
                    processing_status=GPSProcessingStatus.NORMALIZATION_FAILED,
                    error_message=str(e),
                    execution_time_ms=(time.perf_counter() - start_time) * 1000
                )

            # 4. Generate Operational Events from the normalized GPSPosition
            operational_events = []
            
            # Event 1: PositionRecorded (always emitted if we got a valid position)
            pos_event = PositionRecorded(
                device_id=gps_position.device_id,
                provider=gps_position.provider,
                latitude=gps_position.latitude,
                longitude=gps_position.longitude,
                altitude=gps_position.altitude,
                heading=gps_position.heading,
                speed=gps_position.speed,
                accuracy=gps_position.accuracy,
                timestamp=gps_position.timestamp,
                metadata={"position_id": str(gps_position.position_id)}
            )
            operational_events.append(pos_event)
            
            # Event 2: IgnitionStateChanged
            if gps_position.ignition is not None:
                ign_event = IgnitionStateChanged(
                    device_id=gps_position.device_id,
                    provider=gps_position.provider,
                    ignition_on=gps_position.ignition,
                    timestamp=gps_position.timestamp,
                    metadata={"position_id": str(gps_position.position_id)}
                )
                operational_events.append(ign_event)

            # 5. Return Success Result
            return GPSProcessingResult(
                position=gps_position,
                operational_events=operational_events,
                processing_status=GPSProcessingStatus.SUCCESS,
                execution_time_ms=(time.perf_counter() - start_time) * 1000
            )

        except Exception as e:
            logger.error(f"System error processing GPS payload: {str(e)}")
            logger.debug(traceback.format_exc())
            return GPSProcessingResult(
                processing_status=GPSProcessingStatus.SYSTEM_ERROR,
                error_message=f"System error: {str(e)}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000
            )
