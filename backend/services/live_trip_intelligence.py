"""
FleetGuard — Live Trip Intelligence Service

Monitors IN_PROGRESS trips, calculates projected profitability, and
determines real-time health (ON_TRACK, AT_RISK, CRITICAL).
"""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from models.trip_domain import Trip, TripStatus
from models.expense_domain import Expense
from schemas.live_trip_intelligence import (
    LiveTripIntelligenceResponse,
    TripHealthStatus,
    Deviation,
    DeviationSeverity
)
from services.trip_intelligence_config import intelligence_config


class LiveTripIntelligenceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_live_health(self, trip: Trip) -> LiveTripIntelligenceResponse:
        # 1. Base Variables
        now = datetime.now(timezone.utc)
        deviations: List[Deviation] = []
        warnings: List[str] = []
        
        # 2. Extract original expectations from snapshot (if available)
        snapshot = trip.intelligence_snapshot or {}
        has_snapshot = bool(snapshot)
        
        expected_rev = trip.expected_revenue
        expected_cost = trip.expected_cost
        expected_profit = trip.expected_profit
        expected_duration_hours = snapshot.get("expected_duration_hours")
        expected_distance = snapshot.get("expected_distance")
        
        # 3. Calculate Actuals so far
        elapsed_hours = None
        if trip.actual_start_time:
            elapsed_td = now - trip.actual_start_time
            elapsed_hours = elapsed_td.total_seconds() / 3600.0
            
        # Actual cost so far
        stmt = select(func.sum(Expense.amount)).where(Expense.trip_id == trip.id)
        res = await self.db.execute(stmt)
        actual_cost_so_far = res.scalar() or 0.0
        
        # 4. Projections
        projected_total_cost = None
        estimated_remaining_cost = None
        projected_profit = None
        profit_erosion = None
        profit_erosion_pct = None
        
        if expected_cost is not None and expected_duration_hours is not None and elapsed_hours is not None:
            if elapsed_hours >= expected_duration_hours:
                # We are overtime. All remaining time is extra. Assume 10% extra cost minimum.
                estimated_remaining_cost = expected_cost * 0.10
            else:
                # Pro-rata remaining cost based on time
                pct_remaining = 1.0 - (elapsed_hours / expected_duration_hours)
                estimated_remaining_cost = expected_cost * pct_remaining
                
            projected_total_cost = actual_cost_so_far + estimated_remaining_cost
            
        elif expected_cost is not None:
            # No duration. Just use actual + (expected - actual) capped at 0
            estimated_remaining_cost = max(0.0, expected_cost - actual_cost_so_far)
            projected_total_cost = actual_cost_so_far + estimated_remaining_cost
            
        if projected_total_cost is not None and expected_rev is not None:
            projected_profit = expected_rev - projected_total_cost
            
            if expected_profit is not None:
                profit_erosion = expected_profit - projected_profit
                if expected_profit > 0:
                    profit_erosion_pct = (profit_erosion / expected_profit) * 100
                else:
                    profit_erosion_pct = 0.0

        # 5. Deviations
        # Cost Deviation
        if expected_cost and projected_total_cost and projected_total_cost > expected_cost:
            var_pct = ((projected_total_cost - expected_cost) / expected_cost) * 100
            if var_pct >= intelligence_config.cost_variance_warning_pct:
                sev = DeviationSeverity.CRITICAL if var_pct >= 20 else DeviationSeverity.WARNING
                deviations.append(Deviation(
                    metric="Total Cost", severity=sev, expected=expected_cost, actual=projected_total_cost,
                    variance_pct=var_pct, description=f"Projected cost exceeds expectation by {var_pct:.1f}%."
                ))
                
        # Time Deviation
        if expected_duration_hours and elapsed_hours:
            if elapsed_hours > expected_duration_hours:
                var_pct = ((elapsed_hours - expected_duration_hours) / expected_duration_hours) * 100
                sev = DeviationSeverity.CRITICAL if var_pct >= intelligence_config.duration_variance_critical_pct else DeviationSeverity.WARNING
                deviations.append(Deviation(
                    metric="Duration", severity=sev, expected=expected_duration_hours, actual=elapsed_hours,
                    variance_pct=var_pct, description=f"Trip is running behind schedule by {var_pct:.1f}%."
                ))

        # 6. Health Status Logic
        status = TripHealthStatus.ON_TRACK
        
        if not has_snapshot or profit_erosion_pct is None:
            warnings.append("Insufficient data to calculate live health accurately.")
        else:
            has_critical = any(d.severity == DeviationSeverity.CRITICAL for d in deviations)
            has_warning = any(d.severity == DeviationSeverity.WARNING for d in deviations)
            
            if profit_erosion_pct >= intelligence_config.profit_erosion_critical_pct or has_critical:
                status = TripHealthStatus.CRITICAL
            elif profit_erosion_pct >= intelligence_config.profit_erosion_warning_pct or has_warning:
                status = TripHealthStatus.AT_RISK
                
        return LiveTripIntelligenceResponse(
            trip_id=trip.id,
            trip_business_id=trip.trip_id,
            health_status=status,
            expected_duration_hours=expected_duration_hours,
            elapsed_hours=elapsed_hours,
            estimated_remaining_hours=max(0.0, expected_duration_hours - elapsed_hours) if expected_duration_hours and elapsed_hours else None,
            expected_distance=expected_distance,
            actual_distance=trip.actual_distance,
            expected_revenue=expected_rev,
            expected_total_cost=expected_cost,
            actual_cost_so_far=actual_cost_so_far,
            estimated_remaining_cost=estimated_remaining_cost,
            projected_total_cost=projected_total_cost,
            expected_profit=expected_profit,
            projected_profit=projected_profit,
            profit_erosion=profit_erosion,
            profit_erosion_pct=profit_erosion_pct,
            deviations=deviations,
            warnings=warnings,
            intelligence_version=trip.intelligence_version or intelligence_config.intelligence_version,
            snapshot_available=has_snapshot,
            calculated_at=now
        )
