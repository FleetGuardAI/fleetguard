"""
Fuel Sensor Gateway Framework - Executor
"""

import time
import logging
import traceback
from typing import Dict, Any

from infrastructure.fuel.registry import FuelProviderRegistry
from infrastructure.fuel.models import FuelProcessingResult, FuelProcessingStatus
from infrastructure.fuel.events import FuelLevelRecorded, SensorStatusChanged

logger = logging.getLogger(__name__)


class FuelGatewayExecutor:
    """
    Executes the Fuel telemetry ingestion pipeline.
    """
    def __init__(self, registry: FuelProviderRegistry):
        self.registry = registry

    def process_payload(self, provider_key: str, payload: Dict[str, Any]) -> FuelProcessingResult:
        start_time = time.perf_counter()
        
        try:
            # 1. Resolve Provider
            try:
                provider = self.registry.get_provider(provider_key)
            except KeyError:
                return FuelProcessingResult(
                    processing_status=FuelProcessingStatus.UNKNOWN_PROVIDER,
                    error_message=f"No provider found for key: {provider_key}",
                    execution_time_ms=(time.perf_counter() - start_time) * 1000
                )

            # 2. Validate Payload
            try:
                provider.validate(payload)
            except ValueError as e:
                return FuelProcessingResult(
                    processing_status=FuelProcessingStatus.VALIDATION_ERROR,
                    error_message=str(e),
                    execution_time_ms=(time.perf_counter() - start_time) * 1000
                )
                
            # 3. Normalize Data to FuelTelemetry
            try:
                fuel_telemetry = provider.normalize(payload)
            except Exception as e:
                logger.error(f"Normalization failed for payload {payload}: {str(e)}")
                return FuelProcessingResult(
                    processing_status=FuelProcessingStatus.NORMALIZATION_ERROR,
                    error_message=str(e),
                    execution_time_ms=(time.perf_counter() - start_time) * 1000
                )

            # 4. Generate Operational Events from the normalized FuelTelemetry
            operational_events = []
            
            # Event 1: FuelLevelRecorded
            level_event = FuelLevelRecorded(
                device_id=fuel_telemetry.device_id,
                provider=fuel_telemetry.provider,
                fuel_level=fuel_telemetry.fuel_level,
                measurement_unit=fuel_telemetry.measurement_unit,
                quality=fuel_telemetry.quality,
                temperature=fuel_telemetry.temperature,
                timestamp=fuel_telemetry.timestamp,
                metadata={"telemetry_id": str(fuel_telemetry.telemetry_id)}
            )
            operational_events.append(level_event)
            
            # Event 2: SensorStatusChanged
            if fuel_telemetry.sensor_health is not None:
                status_event = SensorStatusChanged(
                    device_id=fuel_telemetry.device_id,
                    provider=fuel_telemetry.provider,
                    sensor_health=fuel_telemetry.sensor_health,
                    timestamp=fuel_telemetry.timestamp,
                    metadata={"telemetry_id": str(fuel_telemetry.telemetry_id)}
                )
                operational_events.append(status_event)

            # 5. Return Success Result
            return FuelProcessingResult(
                telemetry=fuel_telemetry,
                operational_events=operational_events,
                processing_status=FuelProcessingStatus.SUCCESS,
                execution_time_ms=(time.perf_counter() - start_time) * 1000
            )

        except Exception as e:
            logger.error(f"System error processing fuel payload: {str(e)}")
            logger.debug(traceback.format_exc())
            return FuelProcessingResult(
                processing_status=FuelProcessingStatus.SYSTEM_ERROR,
                error_message=f"System error: {str(e)}",
                execution_time_ms=(time.perf_counter() - start_time) * 1000
            )
