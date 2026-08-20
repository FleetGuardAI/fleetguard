import math
from datetime import datetime
from typing import Optional

from infrastructure.uow import AbstractUnitOfWork
from models.derived_fuel_metrics import DerivedFuelMetric, FuelMetricType
from models.entity_baseline import EntityBaseline, BaselineStatus
from models.fuel_anomaly import FuelAnomaly, AnomalyStatus, AnomalyDirection
from models.fuel_financial_impact import FuelFinancialImpact, FuelPriceSource
from models.operational_event import OperationalEvent, EventType
from infrastructure.intelligence.fuel_domain.financial.schemas import FuelFinancialImpactResult
from infrastructure.intelligence.core.financial import GenericFinancialImpactEngine

class FuelFinancialImpactEngine:
    def __init__(self):
        self.generic_engine = GenericFinancialImpactEngine()

    async def calculate_financial_impact(
        self,
        uow: AbstractUnitOfWork,
        anomaly: FuelAnomaly,
        baseline: EntityBaseline,
        observation: DerivedFuelMetric
    ) -> FuelFinancialImpactResult:
        """
        Calculates the financial exposure of a fuel anomaly using exact historical records.
        """
        
        # 1. Anomaly Validation
        if anomaly.status != AnomalyStatus.ANOMALY or anomaly.direction != AnomalyDirection.DEGRADATION:
            return FuelFinancialImpactResult(
                status="INSUFFICIENT_DATA",
                reason="NOT_A_DEGRADATION_ANOMALY"
            )
            
        # 2. Baseline Validation
        if baseline.status != BaselineStatus.VALID or not baseline.baseline_value or not math.isfinite(baseline.baseline_value) or baseline.baseline_value <= 0:
            return FuelFinancialImpactResult(
                status="INSUFFICIENT_DATA",
                reason="BASELINE_UNAVAILABLE"
            )
            
        # 3. Observation Validation
        if not observation.value or not math.isfinite(observation.value) or observation.value <= 0:
            return FuelFinancialImpactResult(
                status="INSUFFICIENT_DATA",
                reason="INVALID_CURRENT_EFFICIENCY"
            )
            
        # 4. Extract Exact Source Events
        if not observation.source_reference:
            return FuelFinancialImpactResult(
                status="INSUFFICIENT_DATA",
                reason="INVALID_DISTANCE"
            )
            
        if observation.source_reference.startswith("events:["):
            return FuelFinancialImpactResult(
                status="INSUFFICIENT_DATA",
                reason="UNSUPPORTED_SOURCE_REFERENCE_FORMAT"
            )
            
        event_ids = observation.source_reference.split(",")
        if len(event_ids) < 2:
            return FuelFinancialImpactResult(
                status="INSUFFICIENT_DATA",
                reason="INVALID_DISTANCE"
            )
            
        # Fetch actual events
        all_events = await uow.repositories.operational_event.list_events_by_entity(
            entity_type=observation.entity_type.name, # EntityType maps to str natively but .name is safer if enum mismatch
            entity_id=observation.entity_id,
            limit=1000
        )
        
        # We need exactly the ones that match event_ids
        source_events = [e for e in all_events if str(e.id) in event_ids and e.event_type == EventType.FUEL_FILLED]
        
        if len(source_events) != len(event_ids):
            return FuelFinancialImpactResult(
                status="INSUFFICIENT_DATA",
                reason="SOURCE_EVENTS_NOT_FOUND"
            )
            
        source_events.sort(key=lambda x: x.occurred_at)
        
        first_evt = source_events[0]
        last_evt = source_events[-1]
        
        first_odo = first_evt.payload.get("odometer_km")
        last_odo = last_evt.payload.get("odometer_km")
        
        if first_odo is None or last_odo is None:
            return FuelFinancialImpactResult(
                status="INSUFFICIENT_DATA",
                reason="INVALID_DISTANCE"
            )
            
        distance = float(last_odo - first_odo)
        if distance <= 0 or not math.isfinite(distance):
            return FuelFinancialImpactResult(
                status="INSUFFICIENT_DATA",
                reason="INVALID_DISTANCE"
            )
            
        # 5. Extract Historical Fuel Price
        # Fuel purchased at first_evt is for the previous interval. 
        # Fuel consumed during THIS interval was purchased at source_events[1:]
        total_liters_purchased = 0.0
        total_cost_inr = 0.0
        
        for evt in source_events[1:]:
            liters = evt.payload.get("liters")
            cost = evt.payload.get("cost_inr")
            
            if liters and cost and float(liters) > 0 and float(cost) > 0:
                total_liters_purchased += float(liters)
                total_cost_inr += float(cost)
                
        if total_liters_purchased <= 0:
            return FuelFinancialImpactResult(
                status="INSUFFICIENT_DATA",
                reason="FUEL_PRICE_UNAVAILABLE"
            )
            
        weighted_price = total_cost_inr / total_liters_purchased
        if weighted_price <= 0 or not math.isfinite(weighted_price):
            return FuelFinancialImpactResult(
                status="INSUFFICIENT_DATA",
                reason="FUEL_PRICE_UNAVAILABLE"
            )
            
        fuel_price_source = FuelPriceSource.ACTUAL_PURCHASE_PRICE if len(source_events[1:]) == 1 else FuelPriceSource.VOLUME_WEIGHTED_PURCHASE_PRICE

        # 6. Calculate Fuel Economics (NO INTERMEDIATE ROUNDING)
        expected_fuel = distance / baseline.baseline_value
        implied_fuel = distance / observation.value
        excess_fuel = implied_fuel - expected_fuel
            
        exposure = excess_fuel * weighted_price

        # Build Domain Context
        domain_context = {
            "distance": distance,
            "expected_fuel_liters": expected_fuel,
            "implied_fuel_liters": implied_fuel,
            "excess_fuel_liters": excess_fuel if excess_fuel > 0 else 0.0,
            "fuel_price_per_liter": weighted_price,
            "fuel_price_source": fuel_price_source.value,
        }

        # 7. Leverage Generic Engine for Validation and Assembly
        payload = {
            "status": "SUCCESS",
            "entity_id": anomaly.entity_id,
            "entity_type": anomaly.entity_type,
            "metric_type": anomaly.metric_type,
            "baseline_value": baseline.baseline_value,
            "observed_value": observation.value,
            "estimated_financial_exposure": exposure,
            "currency": "INR",
            "domain_context": domain_context,
            "anomaly_reference": anomaly.observation_reference,
            "baseline_reference": anomaly.baseline_reference,
            "observation_reference": observation.source_reference,
            "period_start": anomaly.period_start,
            "period_end": anomaly.period_end,
            "calculation_method": "BASELINE_VS_OBSERVED_EFFICIENCY"
        }

        generic_result = self.generic_engine.validate_and_construct(payload)

        # 8. Construct Fuel Result for API backward compatibility
        result = FuelFinancialImpactResult(
            status=generic_result.status,
            reason=generic_result.reason,
            entity_id=generic_result.entity_id,
            entity_type=generic_result.entity_type,
            metric_type=generic_result.metric_type,
            baseline_efficiency=generic_result.baseline_value,
            observed_efficiency=generic_result.observed_value,
            distance=domain_context["distance"],
            expected_fuel_liters=domain_context["expected_fuel_liters"],
            implied_fuel_liters=domain_context["implied_fuel_liters"],
            excess_fuel_liters=domain_context["excess_fuel_liters"],
            fuel_price_per_liter=domain_context["fuel_price_per_liter"],
            fuel_price_source=fuel_price_source,
            estimated_financial_exposure=generic_result.estimated_financial_exposure,
            anomaly_reference=generic_result.anomaly_reference,
            baseline_reference=generic_result.baseline_reference,
            observation_reference=generic_result.observation_reference,
            period_start=generic_result.period_start,
            period_end=generic_result.period_end,
            calculation_method=generic_result.calculation_method
        )
        
        # 9. Dual-Write Persistence
        impact_record = FuelFinancialImpact(
            entity_id=generic_result.entity_id,
            entity_type=generic_result.entity_type,
            metric_type=generic_result.metric_type,
            
            # --- Generic Fields ---
            baseline_value=generic_result.baseline_value,
            observed_value=generic_result.observed_value,
            domain_context=generic_result.domain_context,
            
            # --- Legacy Fields ---
            baseline_efficiency=generic_result.baseline_value,
            observed_efficiency=generic_result.observed_value,
            distance=domain_context["distance"],
            expected_fuel_liters=domain_context["expected_fuel_liters"],
            implied_fuel_liters=domain_context["implied_fuel_liters"],
            excess_fuel_liters=domain_context["excess_fuel_liters"],
            fuel_price_per_liter=domain_context["fuel_price_per_liter"],
            fuel_price_source=fuel_price_source,
            
            # --- Universal Fields ---
            estimated_financial_exposure=generic_result.estimated_financial_exposure,
            currency=generic_result.currency,
            anomaly_reference=generic_result.anomaly_reference,
            baseline_reference=generic_result.baseline_reference,
            observation_reference=generic_result.observation_reference,
            period_start=generic_result.period_start,
            period_end=generic_result.period_end,
            calculation_method=generic_result.calculation_method
        )
        
        await uow.repositories.fuel_financial_impact.upsert_impact(impact_record)
        
        return result
