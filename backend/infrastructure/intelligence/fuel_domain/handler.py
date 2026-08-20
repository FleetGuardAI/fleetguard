import logging
from typing import Any, List
from datetime import datetime

from infrastructure.uow import AbstractUnitOfWork
from models.operational_event import EventType
from models.trip_domain import TripStatus, Trip
from models.derived_fuel_metrics import EntityTypeEnum, FuelMetricType
from models.fuel_anomaly import AnomalyDirection, AnomalyStatus
from models.entity_baseline import BaselineStatus

from infrastructure.intelligence.core.handler import IntelligenceHandler
from infrastructure.intelligence.fuel_domain.metrics.providers import FuelIntelligenceDataLayer
from infrastructure.intelligence.fuel_domain.baseline.engine import FuelBaselineEngine
from infrastructure.intelligence.fuel_domain.anomaly.engine import FuelAnomalyEngine
from infrastructure.intelligence.fuel_domain.financial.engine import FuelFinancialImpactEngine
from infrastructure.intelligence.fuel_domain.root_cause.engine import FuelRootCauseEngine

logger = logging.getLogger("fleetguard.intelligence.fuel_handler")

class FuelIntelligenceHandler(IntelligenceHandler):
    """
    Handles Fuel Intelligence orchestration.
    """
    def __init__(self):
        self.data_layer = FuelIntelligenceDataLayer()
        self.baseline_engine = FuelBaselineEngine()
        self.anomaly_engine = FuelAnomalyEngine()
        self.financial_engine = FuelFinancialImpactEngine()
        self.root_cause_engine = FuelRootCauseEngine()

    @property
    def name(self) -> str:
        return "fuel_intelligence_handler"
        
    def supports(self, event_type: EventType) -> bool:
        return event_type in (EventType.TRIP_COMPLETED, EventType.FUEL_FILLED)
        
    async def check_relevance(
        self, 
        uow: AbstractUnitOfWork, 
        event_type: EventType, 
        entity_id: str, 
        payload: dict, 
        occurred_at: datetime
    ) -> List[Any]:
        """
        Determines which Trip(s) need Fuel Intelligence processing.
        """
        trips_to_process = []
        
        if event_type == EventType.TRIP_COMPLETED:
            trip = await uow.repositories.trip.get_trip_by_business_id(entity_id)
            if trip and trip.status == TripStatus.COMPLETED and trip.actual_start_time and trip.actual_end_time and trip.vehicle:
                trips_to_process.append(trip)
                
        elif event_type == EventType.FUEL_FILLED:
            vehicle_registration = entity_id
            vehicle = await uow.repositories.vehicle.get_vehicle_by_registration(vehicle_registration)
            if not vehicle:
                return []
            
            recent_trips = await uow.repositories.trip.get_trips_by_vehicle(vehicle.id, limit=50)
            
            for trip in recent_trips:
                if trip.status == TripStatus.COMPLETED and trip.actual_start_time and trip.actual_end_time:
                    if trip.actual_start_time <= occurred_at <= trip.actual_end_time:
                        trip.vehicle = vehicle 
                        trips_to_process.append(trip)
                        break 
                        
        return trips_to_process

    async def process(self, uow: AbstractUnitOfWork, context: Any) -> None:
        """
        Executes the conditional FIE cascade for a specific Trip context.
        """
        trip: Trip = context
        vehicle_reg = trip.vehicle.registration_number
        
        logger.info(f"FIE Pipeline Triggered | Vehicle: {vehicle_reg} | Trip: {trip.trip_id}")
        
        # 1. Produce Observation
        metric_result = await self.data_layer.get_fuel_efficiency(
            uow=uow,
            entity_id=vehicle_reg,
            entity_type=EntityTypeEnum.TRUCK,
            period_start=trip.actual_start_time,
            period_end=trip.actual_end_time
        )
        
        if metric_result.status != "SUCCESS" or not metric_result.metric:
            logger.info(f"FIE Pipeline Stopped | Reason: {metric_result.reason}")
            return # Permanent Insufficient Data
            
        metric = metric_result.metric
        
        # Idempotency Check: Does this exact observation already exist?
        existing_metric = await uow.repositories.derived_fuel_metric.get_by_source_reference(metric.source_reference)
        if existing_metric:
            logger.info(f"FIE Pipeline Stopped | Reason: Observation already processed (Idempotent success)")
            return
            
        # Persist Metric
        from models.derived_fuel_metrics import DerivedFuelMetric
        derived_metric = DerivedFuelMetric(
            entity_id=metric.entity_id,
            entity_type=metric.entity_type,
            metric_type=metric.metric_type,
            value=metric.value,
            unit=metric.unit,
            source=metric.source,
            quality=metric.quality,
            measurement_type=metric.measurement_type,
            period_start=metric.period_start,
            period_end=metric.period_end,
            sample_size=metric.sample_size,
            source_reference=metric.source_reference
        )
        metric = await uow.repositories.derived_fuel_metric.upsert_metric(derived_metric)
        
        # 2. Trigger Baseline
        baseline_result = await self.baseline_engine.calculate_baseline(
            uow=uow,
            entity_id=vehicle_reg,
            entity_type=EntityTypeEnum.TRUCK,
            metric_type=FuelMetricType.FUEL_EFFICIENCY,
            period_start=datetime.min.replace(tzinfo=trip.actual_start_time.tzinfo),
            period_end=trip.actual_start_time
        )
        
        if baseline_result.status != BaselineStatus.VALID:
            logger.info(f"FIE Pipeline Stopped | Reason: {baseline_result.reason}")
            return
            
        baseline = await uow.repositories.entity_baseline.get_baseline(
            entity_id=vehicle_reg,
            entity_type=EntityTypeEnum.TRUCK,
            metric_type=FuelMetricType.FUEL_EFFICIENCY,
            period_start=baseline_result.period_start,
            period_end=baseline_result.period_end
        )
            
        # 3. Trigger Anomaly
        anomaly_result = await self.anomaly_engine.detect_anomaly(
            uow=uow,
            current_observation=metric,
            baseline=baseline
        )
        
        if anomaly_result.status != AnomalyStatus.ANOMALY or anomaly_result.direction != AnomalyDirection.DEGRADATION:
            logger.info(f"FIE Pipeline Stopped | Reason: Normal efficiency or non-degradation anomaly.")
            return
            
        anomaly = await uow.repositories.fuel_anomaly.get_by_observation(metric.source_reference)
            
        # 4. Trigger Financial Impact
        impact_result = await self.financial_engine.calculate_financial_impact(
            uow=uow,
            anomaly=anomaly,
            baseline=baseline,
            observation=metric
        )
        
        if impact_result.status != "SUCCESS":
            logger.info(f"FIE Pipeline Stopped | Reason: Financial Impact Engine -> {impact_result.reason}")
            return
            
        impact = await uow.repositories.fuel_financial_impact.get_by_anomaly(anomaly.observation_reference)
            
        # 5. Trigger Root Cause Analysis
        root_cause_result = await self.root_cause_engine.analyze_root_cause(
            uow=uow,
            anomaly=anomaly,
            impact=impact
        )
        
        logger.info(f"FIE Pipeline Successfully Completed | Vehicle: {vehicle_reg} | Exposure: {impact_result.estimated_financial_exposure}")
