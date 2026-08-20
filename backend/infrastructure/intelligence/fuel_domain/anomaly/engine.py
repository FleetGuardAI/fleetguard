import math
from datetime import datetime, timezone
from typing import Optional, Tuple

from infrastructure.uow import AbstractUnitOfWork
from models.derived_fuel_metrics import DerivedFuelMetric, DataQuality, MeasurementType, FuelMetricType
from models.entity_baseline import EntityBaseline, BaselineStatus
from models.fuel_anomaly import FuelAnomaly, AnomalyDirection, AnomalySeverity, AnomalyStatus
from infrastructure.intelligence.fuel_domain.anomaly.schemas import FuelAnomalyResult
from config import settings

from infrastructure.intelligence.core.contracts import DirectionStrategy, SeverityStrategy, Direction, Severity, Status
from infrastructure.intelligence.core.anomaly import GenericAnomalyEngine

class FuelDirectionStrategy(DirectionStrategy):
    def evaluate_direction(self, deviation_percent: float) -> Direction:
        # For fuel efficiency, positive is improvement, negative is degradation.
        if deviation_percent > 0:
            return Direction.IMPROVEMENT
        elif deviation_percent < 0:
            return Direction.DEGRADATION
        else:
            return Direction.NORMAL

class FuelSeverityStrategy(SeverityStrategy):
    def evaluate_severity(self, deviation_percent: float) -> Tuple[Severity, Status]:
        warning_threshold = settings.FUEL_ANOMALY_WARNING_THRESHOLD
        critical_threshold = settings.FUEL_ANOMALY_CRITICAL_THRESHOLD
        
        # Deviation thresholds are positive configurations (e.g. 10.0 for 10%), but deviation is negative for degradation.
        if deviation_percent <= -critical_threshold:
            return Severity.CRITICAL, Status.ANOMALY
        elif deviation_percent <= -warning_threshold:
            return Severity.WARNING, Status.ANOMALY
        else:
            return Severity.NORMAL, Status.NORMAL

class FuelAnomalyEngine:
    def __init__(self):
        self._generic_engine = GenericAnomalyEngine()
        self._direction_strategy = FuelDirectionStrategy()
        self._severity_strategy = FuelSeverityStrategy()

    async def detect_anomaly(
        self,
        uow: AbstractUnitOfWork,
        current_observation: DerivedFuelMetric,
        baseline: Optional[EntityBaseline]
    ) -> FuelAnomalyResult:
        """
        Calculates if the current fuel observation is anomalous compared to its historical baseline.
        """
        
        # 1. Validate Baseline
        if not baseline or baseline.status != BaselineStatus.VALID or not baseline.baseline_value or baseline.baseline_value <= 0:
            return FuelAnomalyResult(
                status=AnomalyStatus.INSUFFICIENT_DATA,
                reason="BASELINE_UNAVAILABLE"
            )
            
        if baseline.sample_size < 5:
            return FuelAnomalyResult(
                status=AnomalyStatus.INSUFFICIENT_DATA,
                reason="BASELINE_UNAVAILABLE"
            )

        # 2. Validate Current Observation
        if current_observation.metric_type != FuelMetricType.FUEL_EFFICIENCY:
            return FuelAnomalyResult(
                status=AnomalyStatus.INSUFFICIENT_DATA,
                reason="INVALID_CURRENT_OBSERVATION"
            )
            
        if current_observation.value is None or current_observation.value <= 0 or not math.isfinite(current_observation.value):
            return FuelAnomalyResult(
                status=AnomalyStatus.INSUFFICIENT_DATA,
                reason="INVALID_CURRENT_OBSERVATION"
            )
            
        if current_observation.measurement_type == MeasurementType.ESTIMATED:
            return FuelAnomalyResult(
                status=AnomalyStatus.INSUFFICIENT_DATA,
                reason="ESTIMATED_OBSERVATION_NOT_SUPPORTED"
            )
            
        if current_observation.quality not in [DataQuality.HIGH, DataQuality.MEDIUM]:
            return FuelAnomalyResult(
                status=AnomalyStatus.INSUFFICIENT_DATA,
                reason="INVALID_CURRENT_OBSERVATION"
            )
            
        # Ensure we are comparing the same entity
        if current_observation.entity_id != baseline.entity_id or current_observation.entity_type != baseline.entity_type:
            return FuelAnomalyResult(
                status=AnomalyStatus.INSUFFICIENT_DATA,
                reason="ENTITY_MISMATCH"
            )
            
        # Ensure we are comparing the same metric
        if current_observation.metric_type != baseline.metric_type:
            return FuelAnomalyResult(
                status=AnomalyStatus.INSUFFICIENT_DATA,
                reason="METRIC_MISMATCH"
            )

        # 3. Calculate Relative Deviation (Percentage) via Generic Engine
        deviation_percent, gen_direction, gen_severity, gen_status = self._generic_engine.evaluate(
            observed_value=current_observation.value,
            baseline_value=baseline.baseline_value,
            direction_strategy=self._direction_strategy,
            severity_strategy=self._severity_strategy
        )
        
        if deviation_percent is None:
            return FuelAnomalyResult(
                status=AnomalyStatus.INSUFFICIENT_DATA,
                reason="INVALID_CURRENT_OBSERVATION"
            )
            
        # Map generic enums back to Fuel specific ORM enums
        direction = AnomalyDirection(gen_direction.value)
        severity = AnomalySeverity(gen_severity.value)
        status = AnomalyStatus(gen_status.value)
            
        now = datetime.now(timezone.utc)
            
        result = FuelAnomalyResult(
            status=status,
            entity_id=current_observation.entity_id,
            entity_type=current_observation.entity_type,
            metric_type=current_observation.metric_type,
            baseline_value=baseline.baseline_value,
            observed_value=current_observation.value,
            deviation_percent=deviation_percent,
            direction=direction,
            severity=severity,
            baseline_reference=str(baseline.id) if hasattr(baseline, 'id') else "unknown_baseline",
            observation_reference=str(current_observation.id),
            detected_at=now,
            period_start=current_observation.period_start,
            period_end=current_observation.period_end
        )
        
        # 6. Persist Anomaly (If valid metrics were processed)
        anomaly_record = FuelAnomaly(
            entity_id=current_observation.entity_id,
            entity_type=current_observation.entity_type,
            metric_type=current_observation.metric_type,
            baseline_value=baseline.baseline_value,
            observed_value=current_observation.value,
            deviation_percent=deviation_percent,
            direction=direction,
            severity=severity,
            status=status,
            baseline_reference=str(baseline.id) if hasattr(baseline, 'id') else "unknown_baseline",
            observation_reference=str(current_observation.id),
            period_start=current_observation.period_start,
            period_end=current_observation.period_end,
            detected_at=now
        )
        
        await uow.repositories.fuel_anomaly.upsert_anomaly(anomaly_record)
        
        return result
