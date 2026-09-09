"""
FleetGuard — Pre-Trip Intelligence Service

Progressive decision engine for evaluating trips before dispatch.
Multi-factor logic (Economics + Feasibility + Risk + Confidence).
"""

from typing import List, Tuple, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from models.vehicle_domain import Vehicle, VehicleStatus
from models.driver_domain import Driver, DriverStatus
from models.expense_domain import Expense, ExpenseCategory
from models.trip_domain import Trip, TripStatus
from schemas.pre_trip_intelligence import (
    PreTripEvaluateRequest,
    PreTripIntelligenceResponse,
    RecommendationDecision,
    RiskLevel,
    ConfidenceLevel,
    SuitabilityStatus,
    SuitabilityAssessment,
    Assumption,
    CostComponent,
    RiskFactor,
    RecommendationReason
)
from services.trip_intelligence_config import intelligence_config
from services.routing_service import RoutingService
from services.vehicle_intelligence import VehicleIntelligence
from services.driver_intelligence import DriverIntelligence

import logging

logger = logging.getLogger(__name__)


class PreTripIntelligenceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.routing_service = RoutingService()
        self.vehicle_intelligence = VehicleIntelligence(db, intelligence_config)
        self.driver_intelligence = DriverIntelligence(db, intelligence_config)

    async def evaluate_trip(self, request: PreTripEvaluateRequest, company_id: int) -> PreTripIntelligenceResponse:
        # Track components
        assumptions: List[Assumption] = []
        risk_factors: List[RiskFactor] = []
        reasons: List[RecommendationReason] = []
        warnings: List[str] = []
        data_sources: set = set()
        cost_breakdown: List[CostComponent] = []

        # 1. Route Estimate (Always needed)
        route_est = await self.routing_service.estimate_route(
            origin=request.origin_location or "",
            destination=request.destination_location or "",
            planned_distance=request.planned_distance,
            origin_lat=request.origin_lat,
            origin_lng=request.origin_lng,
            destination_lat=request.destination_lat,
            destination_lng=request.destination_lng,
            pre_calculated_distance=request.route_distance_km,
            pre_calculated_duration=request.route_duration_hours
        )
        data_sources.add(route_est.source)
        
        if route_est.confidence == "INSUFFICIENT":
            warnings.append("Insufficient location data to determine route distance.")
            risk_factors.append(RiskFactor(factor="Missing Route Data", severity="HIGH", description="Distance is required for fuel and cost estimates."))
            distance_km = 0.0
        else:
            distance_km = route_est.distance_km or 0.0
            assumptions.append(Assumption(
                metric="Route Distance", value=round(distance_km, 2), unit="km",
                source=route_est.source, confidence=route_est.confidence
            ))
            if route_est.duration_hours:
                assumptions.append(Assumption(
                    metric="Route Duration", value=round(route_est.duration_hours, 2), unit="hours",
                    source=route_est.source, confidence=route_est.confidence
                ))

        # 2. Fetch Entities (if provided)
        vehicle = None
        if request.vehicle_id:
            vehicle = await self.db.get(Vehicle, request.vehicle_id)
            if vehicle and vehicle.company_id != company_id:
                vehicle = None
                
        driver = None
        if request.driver_id:
            driver = await self.db.get(Driver, request.driver_id)
            if driver and driver.company_id != company_id:
                driver = None

        # 3. Suitability Checks
        v_suit = None
        d_suit = None
        
        if vehicle:
            v_suit = await self.vehicle_intelligence.evaluate_suitability(
                vehicle, request.planned_start_time, request.planned_end_time, distance_km
            )
            if v_suit.status != SuitabilityStatus.SUITABLE:
                risk_factors.append(RiskFactor(factor="Vehicle Suitability", severity="HIGH", description=" ".join(v_suit.reasons)))
                reasons.append(RecommendationReason(factor_type="negative", description=" ".join(v_suit.reasons)))
        
        if driver:
            d_suit = await self.driver_intelligence.evaluate_suitability(
                driver, request.planned_start_time, request.planned_end_time, distance_km
            )
            if d_suit.status != SuitabilityStatus.SUITABLE:
                risk_factors.append(RiskFactor(factor="Driver Suitability", severity="HIGH", description=" ".join(d_suit.reasons)))
                reasons.append(RecommendationReason(factor_type="negative", description=" ".join(d_suit.reasons)))

        # 4. Economics Calculation
        expected_fuel_liters = 0.0
        expected_fuel_cost = 0.0
        expected_toll = 0.0
        driver_cost = 0.0
        wear_cost = 0.0
        
        if distance_km > 0:
            if vehicle:
                mileage, assumption = await self.vehicle_intelligence.get_mileage_estimate(vehicle.id)
                assumptions.append(assumption)
                data_sources.add(assumption.source)
            else:
                # No vehicle selected yet, use system default fleet average
                mileage = intelligence_config.default_fuel_efficiency_kmpl
                assumptions.append(Assumption(
                    metric="Fuel Efficiency", value=mileage, unit="km/L",
                    source="system_default", confidence="LOW"
                ))
                data_sources.add("system_default")
                
            expected_fuel_liters = distance_km / mileage if mileage > 0 else 0.0
            expected_fuel_cost = expected_fuel_liters * intelligence_config.default_fuel_price_per_liter
            
            cost_breakdown.append(CostComponent(
                category="FUEL", label="Expected Fuel Cost", amount=round(expected_fuel_cost, 2), source="calculated"
            ))
            
            # Tolls
            expected_toll = route_est.toll_estimate
            if expected_toll is None:
                # Fallback to config
                expected_toll = distance_km * intelligence_config.default_toll_rate_per_km
                cost_breakdown.append(CostComponent(
                    category="TOLL", label="Estimated Tolls", amount=round(expected_toll, 2), source="estimated"
                ))
            else:
                cost_breakdown.append(CostComponent(
                    category="TOLL", label="Toll Cost", amount=round(expected_toll, 2), source=route_est.source
                ))
                
            # Driver Cost
            driver_cost = intelligence_config.default_driver_cost_per_day
            if route_est.duration_hours and route_est.duration_hours > 12:
                driver_cost = driver_cost * (route_est.duration_hours / 12.0)
                
            cost_breakdown.append(CostComponent(
                category="DRIVER", label="Driver Allowance/Cost", amount=round(driver_cost, 2), source="estimated"
            ))
            
            # Maintenance / Wear & Tear
            wear_cost = distance_km * intelligence_config.default_operating_cost_per_km
            cost_breakdown.append(CostComponent(
                category="MAINTENANCE", label="Vehicle Wear & Tear", amount=round(wear_cost, 2), source="estimated"
            ))
            
            expected_total_cost = expected_fuel_cost + expected_toll + driver_cost + wear_cost
            
        else:
            # Cannot calculate economics without distance
            expected_total_cost = request.planned_cost or 0.0
            if expected_total_cost > 0:
                cost_breakdown.append(CostComponent(
                    category="TOTAL", label="User Provided Cost", amount=expected_total_cost, source="user_input"
                ))
                
        # 5. Profitability & Margin
        expected_revenue = request.revenue
        expected_profit = None
        expected_margin_pct = None
        min_freight = None
        
        if expected_total_cost > 0:
            min_freight = expected_total_cost * (1 + (intelligence_config.target_margin_pct / 100.0))
            
        if expected_revenue is not None and expected_total_cost > 0:
            expected_profit = expected_revenue - expected_total_cost
            expected_margin_pct = (expected_profit / expected_revenue) * 100 if expected_revenue > 0 else 0.0
            
            if expected_margin_pct < intelligence_config.review_margin_pct:
                risk_factors.append(RiskFactor(
                    factor="Low Margin", 
                    severity="HIGH" if expected_margin_pct < 0 else "MEDIUM",
                    description=f"Expected margin is {expected_margin_pct:.1f}% (target: {intelligence_config.target_margin_pct}%)."
                ))
                if expected_margin_pct < 0:
                     reasons.append(RecommendationReason(factor_type="negative", description="Trip results in a financial loss."))
                else:
                     reasons.append(RecommendationReason(factor_type="negative", description="Trip margin is below acceptable threshold."))
            else:
                reasons.append(RecommendationReason(factor_type="positive", description=f"Healthy expected margin of {expected_margin_pct:.1f}%."))

        # 6. Overall Confidence and Risk Level
        conf_level = ConfidenceLevel.HIGH
        overall_risk = RiskLevel.LOW
        conf_reasons = []

        if not distance_km:
            conf_level = ConfidenceLevel.INSUFFICIENT
            overall_risk = RiskLevel.HIGH
            conf_reasons.append("Missing distance calculation.")
        elif not vehicle:
            conf_level = ConfidenceLevel.MEDIUM
            overall_risk = RiskLevel.MEDIUM
            conf_reasons.append("No vehicle selected, using fleet average mileage.")
        else:
            conf_reasons.append("Using vehicle-specific data.")
            
        if not expected_revenue:
            conf_level = ConfidenceLevel.MEDIUM
            conf_reasons.append("No revenue provided, cannot calculate profitability.")

        has_high_risk = any(r.severity == "HIGH" for r in risk_factors)
        has_med_risk = any(r.severity == "MEDIUM" for r in risk_factors)

        if has_high_risk:
            overall_risk = RiskLevel.HIGH
        elif has_med_risk:
             overall_risk = RiskLevel.MEDIUM

        # 7. Final Recommendation Decision
        rec = RecommendationDecision.TAKE
        
        if overall_risk == RiskLevel.HIGH:
            rec = RecommendationDecision.AVOID
        elif overall_risk == RiskLevel.MEDIUM:
            rec = RecommendationDecision.REVIEW
            
        # Hard overrides
        if expected_margin_pct is not None and expected_margin_pct < 0:
            rec = RecommendationDecision.AVOID
            
        if not vehicle and rec == RecommendationDecision.TAKE:
            rec = RecommendationDecision.REVIEW # Can't blindly take without seeing the vehicle assigned

        if not reasons and rec == RecommendationDecision.TAKE:
            reasons.append(RecommendationReason(factor_type="positive", description="All factors are favorable."))

        # Check for progressive inputs missing warning
        if not request.origin_location or not request.destination_location:
            warnings.append("Enter pickup and destination to calculate route.")
        if not vehicle:
            warnings.append("Select a truck to calculate vehicle-specific profitability.")
        if not request.revenue:
            warnings.append("Enter expected freight revenue to evaluate profitability.")

        return PreTripIntelligenceResponse(
            recommendation=rec,
            recommendation_reasons=reasons,
            expected_distance=distance_km if distance_km > 0 else None,
            expected_duration_hours=route_est.duration_hours,
            route_polyline=route_est.polyline,
            expected_fuel_liters=expected_fuel_liters if expected_fuel_liters > 0 else None,
            expected_fuel_cost=expected_fuel_cost if expected_fuel_cost > 0 else None,
            expected_toll=expected_toll if expected_toll and expected_toll > 0 else None,
            expected_driver_cost=driver_cost if distance_km > 0 else None,
            expected_other_cost=wear_cost if distance_km > 0 else None,
            expected_total_cost=expected_total_cost if expected_total_cost > 0 else None,
            expected_revenue=expected_revenue,
            expected_profit=expected_profit,
            expected_margin_pct=expected_margin_pct,
            minimum_recommended_freight=min_freight,
            cost_breakdown=cost_breakdown,
            risk_level=overall_risk,
            risk_factors=risk_factors,
            confidence_level=conf_level,
            confidence_reasons=conf_reasons,
            vehicle_suitability=v_suit,
            driver_suitability=d_suit,
            assumptions=assumptions,
            data_sources=list(data_sources),
            warnings=warnings,
            intelligence_version=intelligence_config.intelligence_version,
            calculated_at=datetime.now(timezone.utc)
        )
