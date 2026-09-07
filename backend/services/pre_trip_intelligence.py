"""
FleetGuard — Pre-Trip Intelligence Service

Deterministic decision engine for evaluating trips before dispatch.
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


class PreTripIntelligenceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.routing_service = RoutingService()

    async def evaluate_trip(self, request: PreTripEvaluateRequest, company_id: int) -> PreTripIntelligenceResponse:
        # 1. Fetch entities
        vehicle = await self.db.get(Vehicle, request.vehicle_id)
        driver = await self.db.get(Driver, request.driver_id)
        
        # 2. Track assumptions, risks, reasons, warnings, sources
        assumptions: List[Assumption] = []
        risk_factors: List[RiskFactor] = []
        reasons: List[RecommendationReason] = []
        warnings: List[str] = []
        data_sources: set = set()
        
        # 3. Suitability Checks
        v_suit, d_suit = await self._evaluate_suitability(vehicle, driver, company_id, risk_factors, reasons)
        
        # 4. Route Estimate
        route_est = await self.routing_service.estimate_route(
            request.origin_location, request.destination_location, request.planned_distance
        )
        data_sources.add(route_est.source)
        if route_est.confidence == "INSUFFICIENT":
            warnings.append("No planned distance provided. Distance-based calculations disabled.")
            risk_factors.append(RiskFactor(factor="Missing Distance", severity="HIGH", description="Distance is required for fuel and cost estimates."))
        else:
            assumptions.append(Assumption(
                metric="distance", value=route_est.distance_km, unit="km",
                source=route_est.source, confidence=route_est.confidence
            ))
            
        # 5. Economics Calculation
        cost_breakdown: List[CostComponent] = []
        
        # Fuel
        fuel_liters, fuel_cost = await self._calculate_expected_fuel(
            request.planned_fuel_liters, route_est.distance_km, vehicle, company_id, 
            assumptions, data_sources, cost_breakdown
        )
        
        # Other user-provided costs
        if request.planned_cost and not fuel_cost:
             # If user just gave total cost but we don't have fuel cost broken out
             total_cost = request.planned_cost
             cost_breakdown.append(CostComponent(
                 category="TOTAL_PLANNED", label="User Provided Cost", amount=total_cost, source="user_input"
             ))
             data_sources.add("user_input_cost")
        elif request.planned_cost and fuel_cost:
            # We have fuel cost and a total cost. Let's trust user total cost if it's bigger
            other_cost = max(0, request.planned_cost - fuel_cost)
            total_cost = fuel_cost + other_cost
            if other_cost > 0:
                cost_breakdown.append(CostComponent(
                    category="OTHER", label="Other Planned Costs", amount=other_cost, source="user_input"
                ))
            data_sources.add("user_input_cost")
        else:
            # No user cost provided. Estimate based on fuel and driver defaults
            other_cost = 0.0
            
            # Simple driver cost estimate (e.g. 1 day default if no duration)
            driver_cost = intelligence_config.default_driver_cost_per_day
            cost_breakdown.append(CostComponent(
                category="DRIVER", label="Estimated Driver Cost (Default 1 Day)", amount=driver_cost, source="system_default"
            ))
            assumptions.append(Assumption(
                metric="driver_cost", value=driver_cost, unit="INR", source="system_default", confidence="LOW"
            ))
            data_sources.add("system_default_driver")
            total_cost = (fuel_cost or 0.0) + driver_cost

        # Profit & Margin
        expected_profit = None
        expected_margin_pct = None
        min_freight = None
        
        if total_cost > 0:
            min_freight = total_cost / (1 - (intelligence_config.target_margin_pct / 100))
            
        if request.revenue is not None:
            expected_profit = request.revenue - total_cost
            if request.revenue > 0:
                expected_margin_pct = (expected_profit / request.revenue) * 100
            data_sources.add("user_input_revenue")
        else:
            warnings.append("No revenue provided. Profitability cannot be calculated.")
            risk_factors.append(RiskFactor(factor="Missing Revenue", severity="HIGH", description="Cannot determine profit or margin."))
            
        # 6. Data Confidence
        confidence, confidence_reasons = self._assess_confidence(request, route_est, expected_profit, data_sources)
        
        # 7. Risk Level
        risk_level = self._assess_risk_level(risk_factors)
        
        # 8. Recommendation Decision
        recommendation = self._decide_recommendation(
            v_suit, d_suit, expected_margin_pct, expected_profit, confidence, risk_level, reasons
        )
        
        # Assemble Response
        return PreTripIntelligenceResponse(
            recommendation=recommendation,
            recommendation_reasons=reasons,
            expected_distance=route_est.distance_km,
            expected_duration_hours=route_est.duration_hours,
            expected_fuel_liters=fuel_liters,
            expected_fuel_cost=fuel_cost,
            expected_total_cost=total_cost,
            expected_revenue=request.revenue,
            expected_profit=expected_profit,
            expected_margin_pct=expected_margin_pct,
            minimum_recommended_freight=min_freight,
            cost_breakdown=cost_breakdown,
            risk_level=risk_level,
            risk_factors=risk_factors,
            confidence_level=confidence,
            confidence_reasons=confidence_reasons,
            vehicle_suitability=v_suit,
            driver_suitability=d_suit,
            assumptions=assumptions,
            data_sources=list(data_sources),
            warnings=warnings,
            intelligence_version=intelligence_config.intelligence_version,
            calculated_at=datetime.now(timezone.utc)
        )

    async def _evaluate_suitability(self, vehicle: Optional[Vehicle], driver: Optional[Driver], company_id: int, risk_factors: List[RiskFactor], reasons: List[RecommendationReason]) -> Tuple[SuitabilityAssessment, SuitabilityAssessment]:
        # Vehicle Suitability
        v_status = SuitabilityStatus.SUITABLE
        v_reasons = []
        if not vehicle or vehicle.company_id != company_id:
            v_status = SuitabilityStatus.UNSUITABLE
            v_reasons.append("Vehicle not found or unauthorized.")
            risk_factors.append(RiskFactor(factor="Invalid Vehicle", severity="HIGH", description="Vehicle does not exist in fleet."))
        else:
            if vehicle.status == VehicleStatus.MAINTENANCE:
                v_status = SuitabilityStatus.UNSUITABLE
                v_reasons.append("Vehicle is currently in maintenance.")
                risk_factors.append(RiskFactor(factor="Vehicle in Maintenance", severity="HIGH", description="Vehicle cannot be dispatched."))
            elif vehicle.status == VehicleStatus.INACTIVE:
                v_status = SuitabilityStatus.MARGINAL
                v_reasons.append("Vehicle is marked as inactive.")
                risk_factors.append(RiskFactor(factor="Inactive Vehicle", severity="MEDIUM", description="Verify vehicle readiness before dispatch."))
            else:
                v_reasons.append("Vehicle is active and available.")
                
            # Check for active trips (simple conflict check)
            active_trip = await self.db.execute(
                select(Trip).where(Trip.vehicle_id == vehicle.id, Trip.status.in_([TripStatus.IN_PROGRESS, TripStatus.PAUSED]))
            )
            if active_trip.scalars().first():
                v_status = SuitabilityStatus.UNSUITABLE
                v_reasons.append("Vehicle is currently on another active trip.")
                risk_factors.append(RiskFactor(factor="Vehicle Conflict", severity="HIGH", description="Vehicle is already dispatched."))
        
        # Driver Suitability
        d_status = SuitabilityStatus.SUITABLE
        d_reasons = []
        if not driver or driver.company_id != company_id:
            d_status = SuitabilityStatus.UNSUITABLE
            d_reasons.append("Driver not found or unauthorized.")
            risk_factors.append(RiskFactor(factor="Invalid Driver", severity="HIGH", description="Driver does not exist in fleet."))
        else:
            if driver.status != DriverStatus.ACTIVE:
                d_status = SuitabilityStatus.MARGINAL
                d_reasons.append(f"Driver status is {driver.status.value}.")
                risk_factors.append(RiskFactor(factor="Driver Status", severity="MEDIUM", description=f"Driver is {driver.status.value}."))
            else:
                d_reasons.append("Driver is active and available.")
                
            active_trip = await self.db.execute(
                select(Trip).where(Trip.driver_id == driver.id, Trip.status.in_([TripStatus.IN_PROGRESS, TripStatus.PAUSED]))
            )
            if active_trip.scalars().first():
                d_status = SuitabilityStatus.UNSUITABLE
                d_reasons.append("Driver is currently on another active trip.")
                risk_factors.append(RiskFactor(factor="Driver Conflict", severity="HIGH", description="Driver is already dispatched."))

        return (
            SuitabilityAssessment(status=v_status, reasons=v_reasons),
            SuitabilityAssessment(status=d_status, reasons=d_reasons)
        )

    async def _calculate_expected_fuel(
        self, user_fuel: Optional[float], distance: Optional[float], vehicle: Optional[Vehicle], 
        company_id: int, assumptions: List[Assumption], data_sources: set, cost_breakdown: List[CostComponent]
    ) -> Tuple[Optional[float], Optional[float]]:
        
        fuel_liters = None
        fuel_cost = None
        
        if user_fuel is not None and user_fuel > 0:
            fuel_liters = user_fuel
            data_sources.add("user_input_fuel")
            assumptions.append(Assumption(metric="fuel_liters", value=fuel_liters, unit="L", source="user_input", confidence="HIGH"))
        elif distance and distance > 0:
            # Need to estimate fuel efficiency
            efficiency = intelligence_config.default_fuel_efficiency_kmpl
            source = "system_default"
            conf = "LOW"
            
            # Try to get vehicle historical avg
            if vehicle:
                # very simplified check for past trips actual distance / fuel
                stmt = select(func.avg(Trip.actual_distance / Trip.planned_fuel_liters)).where(
                    Trip.vehicle_id == vehicle.id, Trip.status == TripStatus.COMPLETED, 
                    Trip.actual_distance > 0, Trip.planned_fuel_liters > 0
                )
                res = await self.db.execute(stmt)
                v_avg = res.scalar()
                if v_avg:
                    efficiency = float(v_avg)
                    source = "vehicle_historical"
                    conf = "HIGH"
            
            fuel_liters = distance / efficiency
            data_sources.add(source)
            assumptions.append(Assumption(metric="fuel_efficiency", value=efficiency, unit="km/L", source=source, confidence=conf))
            assumptions.append(Assumption(metric="fuel_liters", value=fuel_liters, unit="L", source="calculated", confidence=conf))

        # Fuel Price
        if fuel_liters:
            price_per_liter = intelligence_config.default_fuel_price_per_liter
            price_source = "system_default"
            price_conf = "LOW"
            
            # Try historical fuel expense
            stmt = select(func.avg(Expense.amount)).where(
                Expense.company_id == company_id, Expense.category == ExpenseCategory.FUEL
            )
            res = await self.db.execute(stmt)
            avg_expense = res.scalar()
            
            # We would need to divide by liters, but Expense doesn't have liters.
            # For this MVP, if we don't have a configured price, we use system default, but label it!
            
            fuel_cost = fuel_liters * price_per_liter
            data_sources.add(price_source)
            assumptions.append(Assumption(metric="fuel_price", value=price_per_liter, unit="INR/L", source=price_source, confidence=price_conf))
            cost_breakdown.append(CostComponent(
                category="FUEL", label="Expected Fuel Cost", amount=fuel_cost, source="calculated"
            ))

        return fuel_liters, fuel_cost

    def _assess_confidence(self, request: PreTripEvaluateRequest, route_est, expected_profit, data_sources: set) -> Tuple[ConfidenceLevel, List[str]]:
        reasons = []
        if expected_profit is None or route_est.confidence == "INSUFFICIENT":
            reasons.append("Missing critical inputs (Revenue or Distance).")
            return ConfidenceLevel.INSUFFICIENT, reasons
            
        system_defaults = [s for s in data_sources if "default" in s]
        
        if len(system_defaults) == 0:
            reasons.append("Calculated using primarily user inputs and historical data.")
            return ConfidenceLevel.HIGH, reasons
        elif len(system_defaults) <= 1:
            reasons.append("Calculated using some system defaults.")
            return ConfidenceLevel.MEDIUM, reasons
        else:
            reasons.append("Calculated heavily relying on system defaults.")
            return ConfidenceLevel.LOW, reasons

    def _assess_risk_level(self, risk_factors: List[RiskFactor]) -> RiskLevel:
        if any(r.severity == "HIGH" for r in risk_factors):
            return RiskLevel.HIGH
        if any(r.severity == "MEDIUM" for r in risk_factors):
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _decide_recommendation(
        self, v_suit: SuitabilityAssessment, d_suit: SuitabilityAssessment,
        margin_pct: Optional[float], profit: Optional[float],
        confidence: ConfidenceLevel, risk_level: RiskLevel,
        reasons: List[RecommendationReason]
    ) -> RecommendationDecision:
        
        # 1. Fatal Feasibility/Risk
        if v_suit.status == SuitabilityStatus.UNSUITABLE:
            reasons.append(RecommendationReason(factor_type="negative", description="Vehicle is unsuitable or unavailable."))
            return RecommendationDecision.AVOID
            
        if d_suit.status == SuitabilityStatus.UNSUITABLE:
            reasons.append(RecommendationReason(factor_type="negative", description="Driver is unsuitable or unavailable."))
            return RecommendationDecision.AVOID
            
        if confidence == ConfidenceLevel.INSUFFICIENT:
            reasons.append(RecommendationReason(factor_type="negative", description="Insufficient data to make a reliable recommendation."))
            return RecommendationDecision.REVIEW
            
        # 2. Economics
        if margin_pct is None or profit is None:
            reasons.append(RecommendationReason(factor_type="negative", description="Cannot evaluate economics without revenue and cost."))
            return RecommendationDecision.REVIEW
            
        if margin_pct < 0:
            reasons.append(RecommendationReason(factor_type="negative", description=f"Expected loss of INR {abs(profit):.2f}."))
            return RecommendationDecision.AVOID
            
        if margin_pct < intelligence_config.review_margin_pct:
            reasons.append(RecommendationReason(factor_type="negative", description=f"Margin ({margin_pct:.1f}%) is below the minimum threshold ({intelligence_config.review_margin_pct}%)."))
            return RecommendationDecision.AVOID
            
        if margin_pct < intelligence_config.take_margin_pct:
            reasons.append(RecommendationReason(factor_type="negative", description=f"Margin ({margin_pct:.1f}%) is acceptable but below target. Review economics."))
            if risk_level == RiskLevel.HIGH:
                 reasons.append(RecommendationReason(factor_type="negative", description="High risk factors present."))
            return RecommendationDecision.REVIEW
            
        # 3. Good Economics but High Risk
        if risk_level == RiskLevel.HIGH:
            reasons.append(RecommendationReason(factor_type="negative", description="Profitable, but high operational risk."))
            return RecommendationDecision.REVIEW
            
        # 4. Take
        reasons.append(RecommendationReason(factor_type="positive", description=f"Strong expected margin ({margin_pct:.1f}%)."))
        reasons.append(RecommendationReason(factor_type="positive", description="Operational feasibility confirmed."))
        return RecommendationDecision.TAKE
