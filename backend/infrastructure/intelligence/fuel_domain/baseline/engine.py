import statistics
from datetime import datetime
from typing import List

from infrastructure.uow import AbstractUnitOfWork
from models.derived_fuel_metrics import EntityTypeEnum, FuelMetricType, DataQuality, MeasurementType, DerivedFuelMetric
from models.entity_baseline import EntityBaseline, BaselineStatus
from infrastructure.intelligence.fuel_domain.baseline.schemas import BaselineResult

from infrastructure.intelligence.core.contracts import MetricObservation
from infrastructure.intelligence.core.baseline import GenericBaselineEngine

class FuelBaselineEngine:
    MIN_BASELINE_SAMPLES = 5

    def __init__(self):
        self._generic_engine = GenericBaselineEngine()

    async def calculate_baseline(
        self,
        uow: AbstractUnitOfWork,
        entity_id: str,
        entity_type: EntityTypeEnum,
        metric_type: FuelMetricType,
        period_start: datetime,
        period_end: datetime
    ) -> BaselineResult:
        """
        Calculates and persists the historical normal state for an entity.
        Does NOT calculate financial impact or anomaly detection.
        """
        # 1. Fetch historical observations
        observations = await uow.repositories.derived_fuel_metric.get_historical_observations(
            entity_id=entity_id,
            entity_type=entity_type,
            metric_type=metric_type,
            period_start=period_start,
            period_end=period_end
        )
        
        # 2. Filter valid observations (Fuel-specific rules)
        valid_observations = self._filter_valid_observations(observations)
        
        # 3. Check sample size before adapting
        if len(valid_observations) < self.MIN_BASELINE_SAMPLES:
            return BaselineResult(
                status=BaselineStatus.INSUFFICIENT_DATA,
                reason="INSUFFICIENT_BASELINE_SAMPLES",
                entity_id=entity_id,
                entity_type=entity_type,
                metric_type=metric_type,
                sample_size=len(valid_observations),
                period_start=period_start,
                period_end=period_end
            )
            
        # 4. Map to generic contract and calculate median
        generic_observations = []
        for obs in valid_observations:
            generic_observations.append(MetricObservation(
                entity_id=obs.entity_id,
                entity_type=obs.entity_type.value,
                metric_type=obs.metric_type.value,
                value=obs.value,
                unit=obs.unit,
                period_start=obs.period_start,
                period_end=obs.period_end,
                source=obs.source.value,
                quality=obs.quality.value,
                measurement_type=obs.measurement_type.value,
                source_reference=obs.source_reference,
                observation_id=str(obs.id)
            ))
            
        median_value = self._generic_engine.calculate_median(generic_observations, min_samples=self.MIN_BASELINE_SAMPLES)
        
        if median_value is None:
            return BaselineResult(
                status=BaselineStatus.INSUFFICIENT_DATA,
                reason="INSUFFICIENT_BASELINE_SAMPLES",
                entity_id=entity_id,
                entity_type=entity_type,
                metric_type=metric_type,
                sample_size=len(valid_observations),
                period_start=period_start,
                period_end=period_end
            )
        
        # 5. Determine Overall Quality
        overall_quality = DataQuality.HIGH
        if any(obs.quality == DataQuality.MEDIUM for obs in valid_observations):
            overall_quality = DataQuality.MEDIUM
            
        # All valid observations should have the same unit
        unit = valid_observations[0].unit if valid_observations else "KM_PER_LITRE"
            
        result = BaselineResult(
            status=BaselineStatus.VALID,
            entity_id=entity_id,
            entity_type=entity_type,
            metric_type=metric_type,
            baseline_value=median_value,
            unit=unit,
            sample_size=len(valid_observations),
            calculation_method="MEDIAN",
            data_quality=overall_quality,
            period_start=period_start,
            period_end=period_end
        )
        
        # 6. Persist Baseline
        baseline_record = EntityBaseline(
            entity_id=entity_id,
            entity_type=entity_type,
            metric_type=metric_type,
            baseline_value=median_value,
            unit=unit,
            sample_size=len(valid_observations),
            calculation_method="MEDIAN",
            data_quality=overall_quality,
            status=BaselineStatus.VALID,
            period_start=period_start,
            period_end=period_end
        )
        
        await uow.repositories.entity_baseline.upsert_baseline(baseline_record)
        
        return result
        
    def _filter_valid_observations(self, observations: List[DerivedFuelMetric]) -> List[DerivedFuelMetric]:
        valid = []
        for obs in observations:
            if obs.value is None or obs.value <= 0:
                continue
            
            import math
            if not math.isfinite(obs.value):
                continue
                
            if obs.measurement_type == MeasurementType.ESTIMATED:
                continue
                
            if obs.quality not in [DataQuality.HIGH, DataQuality.MEDIUM]:
                continue
                
            valid.append(obs)
            
        return valid
