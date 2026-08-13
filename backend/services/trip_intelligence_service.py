"""
FleetGuard — Trip Intelligence Service

Core intelligence engine that computes profitability analysis, anomaly
detection, efficiency scoring, historical comparison, and actionable
insights for a single trip.

Design principles:
  • Never fabricates data — returns None or "Data unavailable" markers
  • Distinguishes actual values from estimates (is_estimate flag)
  • All calculations from real trip + expense + fuel data
  • Modular: each section is an independent method
  • Extensible: new data sources slot in without restructuring
"""

from __future__ import annotations

import logging
from typing import Optional, Sequence, List
from datetime import datetime

from infrastructure.uow import AbstractUnitOfWork
from models.trip_domain import Trip, TripStatus
from models.expense_domain import Expense, ExpenseStatus
from models.fuel_domain import FuelTransaction
from schemas.trip_intelligence import (
    TripIntelligenceResponse,
    FinancialSummary,
    CostBreakdownItem,
    PlannedVsActualItem,
    ProfitLossContributor,
    TripEfficiencyScore,
    EfficiencySubScore,
    HistoricalComparison,
    Insight,
    EvidenceRef,
    Recommendation,
    InsightSeverity,
    InsightType,
    DataQuality,
)

logger = logging.getLogger("fleetguard.trip_intelligence")


# Thresholds for anomaly detection
FUEL_VARIANCE_WARNING_PCT = 8.0
FUEL_VARIANCE_CRITICAL_PCT = 15.0
DURATION_VARIANCE_WARNING_PCT = 15.0
DURATION_VARIANCE_CRITICAL_PCT = 30.0
DISTANCE_VARIANCE_WARNING_PCT = 10.0
EXPENSE_VARIANCE_WARNING_PCT = 15.0
COST_VARIANCE_WARNING_PCT = 10.0

# Category display labels
CATEGORY_LABELS = {
    "FUEL": "Fuel",
    "MAINTENANCE": "Maintenance",
    "TYRE": "Tyre",
    "TOLL": "Toll",
    "PARKING": "Parking",
    "SALARY": "Driver Salary",
    "ALLOWANCE": "Driver Allowance",
    "PENALTY": "Penalty/Fine",
    "LOADING": "Loading",
    "UNLOADING": "Unloading",
    "DRIVER_ADVANCE": "Driver Advance",
    "DETENTION": "Detention",
    "MISCELLANEOUS": "Miscellaneous",
}


class TripIntelligenceService:
    """
    Computes Trip Intelligence for a single trip.
    Orchestrates data gathering and delegates to calculation methods.
    """

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    async def compute_intelligence(self, trip: Trip) -> TripIntelligenceResponse:
        """
        Main entry point: gather data, compute all sections, return response.
        """
        # ── Gather data ──────────────────────────────────────────
        expenses = await self._get_trip_expenses(trip)
        fuel_transactions = await self._get_trip_fuel_transactions(trip)
        historical_vehicle_trips = await self._get_historical_trips_by_vehicle(trip)
        historical_driver_trips = await self._get_historical_trips_by_driver(trip)
        historical_route_trips = self._filter_same_route_trips(
            historical_vehicle_trips + historical_driver_trips, trip
        )

        # Track which data sources were used
        data_sources: List[str] = ["trip_record"]
        if expenses:
            data_sources.append("expense_records")
        if fuel_transactions:
            data_sources.append("fuel_transactions")
        if historical_vehicle_trips:
            data_sources.append("vehicle_trip_history")
        if historical_driver_trips:
            data_sources.append("driver_trip_history")

        # ── Compute sections ─────────────────────────────────────
        active_expenses = [e for e in expenses if e.status == ExpenseStatus.RECORDED]

        financial_summary = self._compute_financial_summary(trip, active_expenses)
        cost_breakdown = self._compute_cost_breakdown(active_expenses, trip.revenue)
        planned_vs_actual = self._compute_planned_vs_actual(trip, active_expenses, fuel_transactions)
        insights = self._generate_insights(trip, active_expenses, fuel_transactions, historical_vehicle_trips)
        profit_loss_contributors = self._compute_profit_loss_contributors(
            trip, active_expenses, insights
        )
        efficiency_score = self._compute_efficiency_score(
            trip, active_expenses, fuel_transactions, financial_summary
        )
        historical_comparisons = self._compute_historical_comparisons(
            trip, active_expenses, historical_vehicle_trips, historical_driver_trips, historical_route_trips
        )
        recommendations = self._generate_recommendations(insights)

        # Overall data quality
        data_quality = self._assess_data_quality(trip, active_expenses, fuel_transactions)

        return TripIntelligenceResponse(
            trip_id=trip.id,
            trip_business_id=trip.trip_id,
            trip_status=trip.status.value,
            financial_summary=financial_summary,
            cost_breakdown=cost_breakdown,
            planned_vs_actual=planned_vs_actual,
            profit_loss_contributors=profit_loss_contributors,
            efficiency_score=efficiency_score,
            insights=insights,
            historical_comparisons=historical_comparisons,
            recommendations=recommendations,
            data_quality=data_quality,
            data_sources_used=data_sources,
        )

    # ══════════════════════════════════════════════════════════════
    # Data Gathering
    # ══════════════════════════════════════════════════════════════

    async def _get_trip_expenses(self, trip: Trip) -> Sequence[Expense]:
        try:
            return await self.uow.repositories.expense.get_expenses_by_trip(trip.id)
        except Exception:
            logger.warning(f"Failed to load expenses for trip {trip.id}")
            return []

    async def _get_trip_fuel_transactions(self, trip: Trip) -> Sequence[FuelTransaction]:
        """Get fuel transactions for the trip's vehicle during the trip time window."""
        if not trip.vehicle_id:
            return []
        try:
            all_txns = await self.uow.repositories.fuel.get_fuel_transactions_by_truck(
                trip.vehicle_id, limit=500
            )
            # Filter to trip time window
            start = trip.actual_start_time or trip.planned_start_time
            end = trip.actual_end_time or trip.planned_end_time
            if not start:
                return all_txns[:20]  # No time filter available, return recent

            filtered = []
            for txn in all_txns:
                txn_time = txn.timestamp
                # Make both naive for comparison if needed
                if start and txn_time:
                    s = start.replace(tzinfo=None) if start.tzinfo else start
                    t = txn_time.replace(tzinfo=None) if txn_time.tzinfo else txn_time
                    e = end.replace(tzinfo=None) if end and end.tzinfo else (end if end else None)
                    if t >= s and (e is None or t <= e):
                        filtered.append(txn)
            return filtered
        except Exception:
            logger.warning(f"Failed to load fuel transactions for trip {trip.id}")
            return []

    async def _get_historical_trips_by_vehicle(self, trip: Trip) -> List[Trip]:
        if not trip.vehicle_id:
            return []
        try:
            trips = await self.uow.repositories.trip.get_trips_by_vehicle(
                trip.vehicle_id, limit=20
            )
            return [t for t in trips if t.id != trip.id and t.status == TripStatus.COMPLETED]
        except Exception:
            return []

    async def _get_historical_trips_by_driver(self, trip: Trip) -> List[Trip]:
        if not trip.driver_id:
            return []
        try:
            trips = await self.uow.repositories.trip.get_trips_by_driver(
                trip.driver_id, limit=20
            )
            return [t for t in trips if t.id != trip.id and t.status == TripStatus.COMPLETED]
        except Exception:
            return []

    def _filter_same_route_trips(self, trips: List[Trip], current: Trip) -> List[Trip]:
        """Filter trips with same origin+destination (case-insensitive)."""
        if not current.origin_location or not current.destination_location:
            return []
        origin = current.origin_location.strip().lower()
        dest = current.destination_location.strip().lower()
        seen_ids = set()
        result = []
        for t in trips:
            if t.id in seen_ids or t.id == current.id:
                continue
            seen_ids.add(t.id)
            if (t.origin_location and t.destination_location
                    and t.origin_location.strip().lower() == origin
                    and t.destination_location.strip().lower() == dest):
                result.append(t)
        return result

    # ══════════════════════════════════════════════════════════════
    # Section 1: Financial Summary
    # ══════════════════════════════════════════════════════════════

    def _compute_financial_summary(
        self, trip: Trip, expenses: Sequence[Expense]
    ) -> FinancialSummary:
        revenue = trip.revenue
        total_cost = sum(e.amount for e in expenses) if expenses else None
        distance = trip.actual_distance or trip.planned_distance

        net_profit = None
        profit_margin_pct = None
        cost_per_km = None
        revenue_per_km = None
        has_data = False

        if revenue is not None and total_cost is not None:
            net_profit = revenue - total_cost
            has_data = True
            if revenue > 0:
                profit_margin_pct = round((net_profit / revenue) * 100, 1)

        if total_cost is not None and distance and distance > 0:
            cost_per_km = round(total_cost / distance, 2)

        if revenue is not None and distance and distance > 0:
            revenue_per_km = round(revenue / distance, 2)

        if revenue is not None or total_cost is not None:
            has_data = True

        return FinancialSummary(
            revenue=revenue,
            total_cost=round(total_cost, 2) if total_cost is not None else None,
            net_profit=round(net_profit, 2) if net_profit is not None else None,
            profit_margin_pct=profit_margin_pct,
            cost_per_km=cost_per_km,
            revenue_per_km=revenue_per_km,
            has_sufficient_data=has_data,
        )

    # ══════════════════════════════════════════════════════════════
    # Section 2: Cost Breakdown
    # ══════════════════════════════════════════════════════════════

    def _compute_cost_breakdown(
        self, expenses: Sequence[Expense], revenue: Optional[float]
    ) -> List[CostBreakdownItem]:
        if not expenses:
            return []

        category_totals: dict[str, float] = {}
        for e in expenses:
            cat = e.category.value if e.category else "MISCELLANEOUS"
            category_totals[cat] = category_totals.get(cat, 0) + e.amount

        total_cost = sum(category_totals.values())
        if total_cost <= 0:
            return []

        items = []
        for cat, amount in sorted(category_totals.items(), key=lambda x: -x[1]):
            items.append(CostBreakdownItem(
                category=cat,
                category_label=CATEGORY_LABELS.get(cat, cat.replace("_", " ").title()),
                amount=round(amount, 2),
                percentage=round((amount / total_cost) * 100, 1),
            ))
        return items

    # ══════════════════════════════════════════════════════════════
    # Section 3: Planned vs Actual
    # ══════════════════════════════════════════════════════════════

    def _compute_planned_vs_actual(
        self, trip: Trip, expenses: Sequence[Expense],
        fuel_transactions: Sequence[FuelTransaction]
    ) -> List[PlannedVsActualItem]:
        items = []

        # Distance
        if trip.planned_distance is not None or trip.actual_distance is not None:
            variance, variance_pct, severity = self._calc_variance(
                trip.planned_distance, trip.actual_distance, DISTANCE_VARIANCE_WARNING_PCT
            )
            items.append(PlannedVsActualItem(
                metric="distance", metric_label="Distance",
                planned=trip.planned_distance, actual=trip.actual_distance,
                variance=variance, variance_pct=variance_pct,
                unit="km", severity=severity,
                has_data=trip.planned_distance is not None and trip.actual_distance is not None,
            ))

        # Duration (hours)
        planned_duration = self._calc_duration_hours(trip.planned_start_time, trip.planned_end_time)
        actual_duration = self._calc_duration_hours(trip.actual_start_time, trip.actual_end_time)
        if planned_duration is not None or actual_duration is not None:
            variance, variance_pct, severity = self._calc_variance(
                planned_duration, actual_duration, DURATION_VARIANCE_WARNING_PCT,
                critical_pct=DURATION_VARIANCE_CRITICAL_PCT,
            )
            items.append(PlannedVsActualItem(
                metric="duration", metric_label="Duration",
                planned=round(planned_duration, 1) if planned_duration else None,
                actual=round(actual_duration, 1) if actual_duration else None,
                variance=round(variance, 1) if variance is not None else None,
                variance_pct=variance_pct,
                unit="hours", severity=severity,
                has_data=planned_duration is not None and actual_duration is not None,
            ))

        # Fuel (liters)
        actual_fuel = sum(t.amount_liters for t in fuel_transactions) if fuel_transactions else None
        if trip.planned_fuel_liters is not None or actual_fuel is not None:
            variance, variance_pct, severity = self._calc_variance(
                trip.planned_fuel_liters, actual_fuel,
                FUEL_VARIANCE_WARNING_PCT, FUEL_VARIANCE_CRITICAL_PCT,
            )
            items.append(PlannedVsActualItem(
                metric="fuel", metric_label="Fuel Consumption",
                planned=trip.planned_fuel_liters,
                actual=round(actual_fuel, 1) if actual_fuel is not None else None,
                variance=round(variance, 1) if variance is not None else None,
                variance_pct=variance_pct,
                unit="liters", severity=severity,
                has_data=trip.planned_fuel_liters is not None and actual_fuel is not None,
            ))

        # Cost
        total_cost = sum(e.amount for e in expenses) if expenses else None
        if trip.planned_cost is not None or total_cost is not None:
            variance, variance_pct, severity = self._calc_variance(
                trip.planned_cost, total_cost, COST_VARIANCE_WARNING_PCT,
            )
            items.append(PlannedVsActualItem(
                metric="cost", metric_label="Total Cost",
                planned=trip.planned_cost,
                actual=round(total_cost, 2) if total_cost is not None else None,
                variance=round(variance, 2) if variance is not None else None,
                variance_pct=variance_pct,
                unit="₹", severity=severity,
                has_data=trip.planned_cost is not None and total_cost is not None,
            ))

        # Revenue
        if trip.revenue is not None:
            items.append(PlannedVsActualItem(
                metric="revenue", metric_label="Revenue",
                planned=trip.revenue, actual=trip.revenue,
                variance=0, variance_pct=0,
                unit="₹", severity=InsightSeverity.INFO,
                has_data=True,
            ))

        return items

    # ══════════════════════════════════════════════════════════════
    # Section 4: Insights / Root-Cause Analysis
    # ══════════════════════════════════════════════════════════════

    def _generate_insights(
        self, trip: Trip, expenses: Sequence[Expense],
        fuel_transactions: Sequence[FuelTransaction],
        historical_trips: List[Trip],
    ) -> List[Insight]:
        insights = []

        # ── Fuel anomaly ──
        actual_fuel = sum(t.amount_liters for t in fuel_transactions) if fuel_transactions else None
        if trip.planned_fuel_liters and actual_fuel:
            variance_pct = ((actual_fuel - trip.planned_fuel_liters) / trip.planned_fuel_liters) * 100
            if variance_pct > FUEL_VARIANCE_WARNING_PCT:
                severity = (InsightSeverity.CRITICAL if variance_pct > FUEL_VARIANCE_CRITICAL_PCT
                            else InsightSeverity.WARNING)
                insights.append(Insight(
                    insight_type=InsightType.FUEL_ANOMALY,
                    severity=severity,
                    title="Above-expected fuel consumption",
                    description=(
                        f"Fuel consumption was {variance_pct:.1f}% higher than the planned "
                        f"baseline ({trip.planned_fuel_liters:.0f}L planned vs "
                        f"{actual_fuel:.0f}L actual)."
                    ),
                    impact_amount=self._estimate_fuel_cost_impact(
                        actual_fuel - trip.planned_fuel_liters, expenses
                    ),
                    is_estimate=True,
                    evidence=[
                        EvidenceRef(evidence_type="fuel_transactions",
                                    label="Fuel transaction records",
                                    detail=f"{len(fuel_transactions)} transactions during trip"),
                        EvidenceRef(evidence_type="trip_record",
                                    label="Planned fuel baseline",
                                    detail=f"{trip.planned_fuel_liters:.0f}L planned"),
                    ],
                ))

        # ── Duration / delay anomaly ──
        planned_duration = self._calc_duration_hours(trip.planned_start_time, trip.planned_end_time)
        actual_duration = self._calc_duration_hours(trip.actual_start_time, trip.actual_end_time)
        if planned_duration and actual_duration:
            duration_variance_pct = ((actual_duration - planned_duration) / planned_duration) * 100
            if duration_variance_pct > DURATION_VARIANCE_WARNING_PCT:
                excess_hours = actual_duration - planned_duration
                severity = (InsightSeverity.CRITICAL if duration_variance_pct > DURATION_VARIANCE_CRITICAL_PCT
                            else InsightSeverity.WARNING)
                insights.append(Insight(
                    insight_type=InsightType.DURATION_ANOMALY,
                    severity=severity,
                    title="Trip exceeded expected duration",
                    description=(
                        f"The trip exceeded the expected duration by {duration_variance_pct:.0f}% "
                        f"({excess_hours:.1f} additional hours). "
                        f"Planned: {planned_duration:.1f}h, Actual: {actual_duration:.1f}h."
                    ),
                    evidence=[
                        EvidenceRef(evidence_type="trip_timeline",
                                    label="Trip start/end timestamps",
                                    detail=f"Actual duration: {actual_duration:.1f}h"),
                    ],
                ))

        # ── Distance deviation ──
        if trip.planned_distance and trip.actual_distance:
            dist_variance = trip.actual_distance - trip.planned_distance
            dist_variance_pct = (dist_variance / trip.planned_distance) * 100
            if dist_variance_pct > DISTANCE_VARIANCE_WARNING_PCT:
                insights.append(Insight(
                    insight_type=InsightType.DISTANCE_ANOMALY,
                    severity=InsightSeverity.WARNING,
                    title="Route deviation detected",
                    description=(
                        f"The vehicle travelled {dist_variance:.0f} km above the planned route "
                        f"({trip.planned_distance:.0f} km planned vs {trip.actual_distance:.0f} km actual)."
                    ),
                    evidence=[
                        EvidenceRef(evidence_type="trip_record",
                                    label="Planned vs actual distance",
                                    detail=f"+{dist_variance:.0f} km deviation"),
                    ],
                ))

        # ── Detention (check for detention expenses) ──
        detention_expenses = [e for e in expenses if e.category and e.category.value == "DETENTION"]
        if detention_expenses:
            detention_total = sum(e.amount for e in detention_expenses)
            insights.append(Insight(
                insight_type=InsightType.DETENTION,
                severity=InsightSeverity.WARNING,
                title="Detention charges incurred",
                description=(
                    f"₹{detention_total:,.0f} in detention charges were recorded for this trip "
                    f"across {len(detention_expenses)} expense entry(ies)."
                ),
                impact_amount=detention_total,
                is_estimate=False,
                evidence=[
                    EvidenceRef(evidence_type="expense_records",
                                label="Detention expense entries",
                                detail=f"{len(detention_expenses)} records totalling ₹{detention_total:,.0f}"),
                ],
            ))

        # ── Expense anomaly (compare to historical average) ──
        if expenses and historical_trips:
            avg_historical_cost = self._calc_avg_trip_cost_from_history(historical_trips)
            if avg_historical_cost and avg_historical_cost > 0:
                current_cost = sum(e.amount for e in expenses)
                expense_variance_pct = ((current_cost - avg_historical_cost) / avg_historical_cost) * 100
                if expense_variance_pct > EXPENSE_VARIANCE_WARNING_PCT:
                    insights.append(Insight(
                        insight_type=InsightType.EXPENSE_ANOMALY,
                        severity=InsightSeverity.WARNING,
                        title="Expenses above historical average",
                        description=(
                            f"Total expenses were {expense_variance_pct:.0f}% higher than the "
                            f"historical average for similar trips (₹{current_cost:,.0f} vs "
                            f"avg ₹{avg_historical_cost:,.0f})."
                        ),
                        impact_amount=round(current_cost - avg_historical_cost, 2),
                        is_estimate=True,
                        evidence=[
                            EvidenceRef(evidence_type="expense_records",
                                        label="Current trip expenses",
                                        detail=f"₹{current_cost:,.0f} total"),
                            EvidenceRef(evidence_type="historical_data",
                                        label="Historical average",
                                        detail=f"₹{avg_historical_cost:,.0f} across {len(historical_trips)} trips"),
                        ],
                    ))

        # ── Cost overrun ──
        if trip.planned_cost and expenses:
            total_cost = sum(e.amount for e in expenses)
            cost_overrun = total_cost - trip.planned_cost
            cost_overrun_pct = (cost_overrun / trip.planned_cost) * 100
            if cost_overrun_pct > COST_VARIANCE_WARNING_PCT:
                insights.append(Insight(
                    insight_type=InsightType.COST_OVERRUN,
                    severity=InsightSeverity.WARNING,
                    title="Cost exceeded budget",
                    description=(
                        f"Actual cost exceeded the planned budget by {cost_overrun_pct:.0f}% "
                        f"(₹{cost_overrun:,.0f} overrun)."
                    ),
                    impact_amount=round(cost_overrun, 2),
                    is_estimate=False,
                    evidence=[
                        EvidenceRef(evidence_type="trip_record",
                                    label="Planned cost",
                                    detail=f"₹{trip.planned_cost:,.0f}"),
                        EvidenceRef(evidence_type="expense_records",
                                    label="Actual cost",
                                    detail=f"₹{total_cost:,.0f}"),
                    ],
                ))

        return insights

    # ══════════════════════════════════════════════════════════════
    # Section 5: Profit Loss Contributors
    # ══════════════════════════════════════════════════════════════

    def _compute_profit_loss_contributors(
        self, trip: Trip, expenses: Sequence[Expense], insights: List[Insight]
    ) -> List[ProfitLossContributor]:
        """Rank the biggest contributors to profit loss using insights."""
        contributors = []
        for insight in insights:
            if insight.impact_amount and insight.impact_amount > 0:
                contributors.append(ProfitLossContributor(
                    rank=0,
                    title=insight.title,
                    description=insight.description,
                    impact_amount=round(insight.impact_amount, 2),
                    is_estimate=insight.is_estimate,
                    severity=insight.severity,
                    evidence_refs=[e.label for e in insight.evidence],
                ))

        # Sort by impact descending, assign ranks
        contributors.sort(key=lambda c: c.impact_amount or 0, reverse=True)
        for i, c in enumerate(contributors):
            c.rank = i + 1

        return contributors

    # ══════════════════════════════════════════════════════════════
    # Section 6: Trip Efficiency Score
    # ══════════════════════════════════════════════════════════════

    def _compute_efficiency_score(
        self, trip: Trip, expenses: Sequence[Expense],
        fuel_transactions: Sequence[FuelTransaction],
        financial_summary: FinancialSummary,
    ) -> TripEfficiencyScore:
        sub_scores = []
        available_scores = []

        # Fuel efficiency (100 = on target, penalty for excess)
        fuel_score = self._score_fuel_efficiency(trip, fuel_transactions)
        sub_scores.append(EfficiencySubScore(
            name="fuel_efficiency", label="Fuel Efficiency",
            score=fuel_score, has_data=fuel_score is not None,
        ))
        if fuel_score is not None:
            available_scores.append(fuel_score)

        # Cost efficiency (100 = at or below planned cost)
        cost_score = self._score_cost_efficiency(trip, expenses)
        sub_scores.append(EfficiencySubScore(
            name="cost_efficiency", label="Cost Efficiency",
            score=cost_score, has_data=cost_score is not None,
        ))
        if cost_score is not None:
            available_scores.append(cost_score)

        # Time efficiency (100 = on time)
        time_score = self._score_time_efficiency(trip)
        sub_scores.append(EfficiencySubScore(
            name="time_efficiency", label="Time Efficiency",
            score=time_score, has_data=time_score is not None,
        ))
        if time_score is not None:
            available_scores.append(time_score)

        # Route efficiency (100 = no deviation)
        route_score = self._score_route_efficiency(trip)
        sub_scores.append(EfficiencySubScore(
            name="route_efficiency", label="Route Efficiency",
            score=route_score, has_data=route_score is not None,
        ))
        if route_score is not None:
            available_scores.append(route_score)

        # Profitability (100 = high margin)
        profit_score = self._score_profitability(financial_summary)
        sub_scores.append(EfficiencySubScore(
            name="profitability", label="Profitability",
            score=profit_score, has_data=profit_score is not None,
        ))
        if profit_score is not None:
            available_scores.append(profit_score)

        # Overall
        if len(available_scores) >= 2:
            overall = round(sum(available_scores) / len(available_scores), 0)
            grade = self._score_to_grade(overall)
            explanation = self._build_score_explanation(overall, grade, sub_scores)
            data_quality = DataQuality.HIGH if len(available_scores) >= 4 else DataQuality.MEDIUM
            return TripEfficiencyScore(
                overall_score=overall,
                grade=grade,
                explanation=explanation,
                sub_scores=sub_scores,
                data_quality=data_quality,
                has_sufficient_data=True,
            )
        else:
            return TripEfficiencyScore(
                overall_score=None,
                grade=None,
                explanation="Score unavailable — insufficient trip data to compute a reliable efficiency score.",
                sub_scores=sub_scores,
                data_quality=DataQuality.INSUFFICIENT,
                has_sufficient_data=False,
            )

    def _score_fuel_efficiency(self, trip: Trip, fuel_txns: Sequence[FuelTransaction]) -> Optional[float]:
        if not trip.planned_fuel_liters or not fuel_txns:
            return None
        actual = sum(t.amount_liters for t in fuel_txns)
        if actual <= 0:
            return None
        ratio = actual / trip.planned_fuel_liters
        # 1.0 = 100, 1.15 = 70, 1.30+ = 40
        score = max(0, min(100, 100 - (ratio - 1.0) * 200))
        return round(score)

    def _score_cost_efficiency(self, trip: Trip, expenses: Sequence[Expense]) -> Optional[float]:
        if not trip.planned_cost or not expenses:
            return None
        actual = sum(e.amount for e in expenses)
        if actual <= 0:
            return None
        ratio = actual / trip.planned_cost
        score = max(0, min(100, 100 - (ratio - 1.0) * 200))
        return round(score)

    def _score_time_efficiency(self, trip: Trip) -> Optional[float]:
        planned = self._calc_duration_hours(trip.planned_start_time, trip.planned_end_time)
        actual = self._calc_duration_hours(trip.actual_start_time, trip.actual_end_time)
        if not planned or not actual:
            return None
        ratio = actual / planned
        score = max(0, min(100, 100 - (ratio - 1.0) * 150))
        return round(score)

    def _score_route_efficiency(self, trip: Trip) -> Optional[float]:
        if not trip.planned_distance or not trip.actual_distance:
            return None
        ratio = trip.actual_distance / trip.planned_distance
        score = max(0, min(100, 100 - (ratio - 1.0) * 300))
        return round(score)

    def _score_profitability(self, summary: FinancialSummary) -> Optional[float]:
        if summary.profit_margin_pct is None:
            return None
        margin = summary.profit_margin_pct
        # 60%+ margin = 100, 0% margin = 40, negative = 0-40 scaled
        if margin >= 60:
            return 100
        elif margin >= 0:
            return round(40 + (margin / 60) * 60)
        else:
            return round(max(0, 40 + margin))  # Negative margin reduces from 40

    def _score_to_grade(self, score: float) -> str:
        if score >= 90:
            return "Excellent"
        elif score >= 75:
            return "Good"
        elif score >= 60:
            return "Fair"
        elif score >= 40:
            return "Poor"
        else:
            return "Critical"

    def _build_score_explanation(
        self, score: float, grade: str, sub_scores: List[EfficiencySubScore]
    ) -> str:
        explanation = f"{score:.0f}/100 — {grade}. "
        weaknesses = [s for s in sub_scores if s.has_data and s.score is not None and s.score < 70]
        strengths = [s for s in sub_scores if s.has_data and s.score is not None and s.score >= 85]

        if strengths:
            explanation += f"Strong performance in {', '.join(s.label.lower() for s in strengths)}. "
        if weaknesses:
            explanation += f"Below target in {', '.join(s.label.lower() for s in weaknesses)}."
        elif not weaknesses and not strengths:
            explanation += "Overall balanced performance across available metrics."

        return explanation.strip()

    # ══════════════════════════════════════════════════════════════
    # Section 7: Historical Comparisons
    # ══════════════════════════════════════════════════════════════

    def _compute_historical_comparisons(
        self, trip: Trip, expenses: Sequence[Expense],
        vehicle_trips: List[Trip], driver_trips: List[Trip],
        route_trips: List[Trip],
    ) -> List[HistoricalComparison]:
        comparisons = []
        current_cost = sum(e.amount for e in expenses) if expenses else None
        distance = trip.actual_distance or trip.planned_distance
        actual_duration = self._calc_duration_hours(trip.actual_start_time, trip.actual_end_time)

        # ── vs Same Vehicle ──
        if vehicle_trips and current_cost is not None:
            vehicle_costs = [self._estimate_trip_cost(t) for t in vehicle_trips]
            vehicle_costs = [c for c in vehicle_costs if c is not None and c > 0]
            if vehicle_costs:
                avg = sum(vehicle_costs) / len(vehicle_costs)
                variance_pct = ((current_cost - avg) / avg) * 100 if avg else None
                comparisons.append(HistoricalComparison(
                    metric="cost_vs_vehicle",
                    metric_label="Trip cost vs this vehicle's history",
                    current_value=round(current_cost, 2),
                    comparison_value=round(avg, 2),
                    comparison_label=f"Average of {len(vehicle_costs)} previous trips",
                    variance_pct=round(variance_pct, 1) if variance_pct is not None else None,
                    unit="₹",
                    is_favorable=variance_pct is not None and variance_pct < 0,
                    sample_size=len(vehicle_costs),
                ))

        # ── vs Same Driver ──
        if driver_trips and actual_duration is not None:
            driver_durations = [
                self._calc_duration_hours(t.actual_start_time, t.actual_end_time)
                for t in driver_trips
            ]
            driver_durations = [d for d in driver_durations if d is not None and d > 0]
            if driver_durations:
                avg_dur = sum(driver_durations) / len(driver_durations)
                variance_pct = ((actual_duration - avg_dur) / avg_dur) * 100 if avg_dur else None
                comparisons.append(HistoricalComparison(
                    metric="duration_vs_driver",
                    metric_label="Trip duration vs this driver's history",
                    current_value=round(actual_duration, 1),
                    comparison_value=round(avg_dur, 1),
                    comparison_label=f"Average of {len(driver_durations)} previous trips",
                    variance_pct=round(variance_pct, 1) if variance_pct is not None else None,
                    unit="hours",
                    is_favorable=variance_pct is not None and variance_pct < 0,
                    sample_size=len(driver_durations),
                ))

        # ── vs Same Route ──
        if route_trips and current_cost is not None:
            route_costs = [self._estimate_trip_cost(t) for t in route_trips]
            route_costs = [c for c in route_costs if c is not None and c > 0]
            if route_costs:
                avg = sum(route_costs) / len(route_costs)
                variance_pct = ((current_cost - avg) / avg) * 100 if avg else None
                comparisons.append(HistoricalComparison(
                    metric="cost_vs_route",
                    metric_label="Trip cost vs same route history",
                    current_value=round(current_cost, 2),
                    comparison_value=round(avg, 2),
                    comparison_label=f"Average of {len(route_costs)} trips on this route",
                    variance_pct=round(variance_pct, 1) if variance_pct is not None else None,
                    unit="₹",
                    is_favorable=variance_pct is not None and variance_pct < 0,
                    sample_size=len(route_costs),
                ))

        return comparisons

    def _estimate_trip_cost(self, trip: Trip) -> Optional[float]:
        """Estimate a historical trip's cost from its planned_cost field."""
        return trip.planned_cost

    async def _get_historical_expenses_for_trip(self, trip_id: int) -> float:
        """Load actual expenses for a historical trip. Used sparingly."""
        try:
            expenses = await self.uow.repositories.expense.get_expenses_by_trip(trip_id)
            return sum(e.amount for e in expenses if e.status == ExpenseStatus.RECORDED)
        except Exception:
            return 0

    def _calc_avg_trip_cost_from_history(self, trips: List[Trip]) -> Optional[float]:
        """Calculate average planned cost from historical trips."""
        costs = [t.planned_cost for t in trips if t.planned_cost is not None and t.planned_cost > 0]
        if not costs:
            return None
        return sum(costs) / len(costs)

    # ══════════════════════════════════════════════════════════════
    # Section 8: Recommendations
    # ══════════════════════════════════════════════════════════════

    def _generate_recommendations(self, insights: List[Insight]) -> List[Recommendation]:
        """Generate actionable recommendations from detected anomalies."""
        recommendations = []
        priority = 1

        for insight in sorted(insights, key=lambda i: (
            0 if i.severity == InsightSeverity.CRITICAL else
            1 if i.severity == InsightSeverity.WARNING else 2
        )):
            rec = self._insight_to_recommendation(insight, priority)
            if rec:
                recommendations.append(rec)
                priority += 1

        return recommendations

    def _insight_to_recommendation(self, insight: Insight, priority: int) -> Optional[Recommendation]:
        """Map an insight to an actionable recommendation."""
        templates = {
            InsightType.FUEL_ANOMALY: (
                "Investigate fuel consumption",
                "Review fuel transactions, sensor data, and driver behaviour for this trip. "
                "Compare with the vehicle's baseline consumption on similar routes."
            ),
            InsightType.DURATION_ANOMALY: (
                "Review trip delays",
                "Investigate the cause of the extended trip duration. Check for detention at "
                "loading/unloading points, route delays, or driver rest violations."
            ),
            InsightType.DISTANCE_ANOMALY: (
                "Review route deviation",
                "Verify if the additional distance was due to road closures, GPS inaccuracy, "
                "or unauthorized route changes."
            ),
            InsightType.DETENTION: (
                "Address detention charges",
                "Review detention events at loading/unloading points. Consider negotiating "
                "better unloading schedules or detention fee terms with the client."
            ),
            InsightType.EXPENSE_ANOMALY: (
                "Review submitted expenses",
                "Driver-reported expenses were significantly above historical averages. "
                "Verify receipts and cross-check with fuel/toll records."
            ),
            InsightType.COST_OVERRUN: (
                "Analyse cost overrun",
                "Total trip cost exceeded the planned budget. Review the cost breakdown "
                "to identify the largest contributing categories."
            ),
        }

        template = templates.get(insight.insight_type)
        if not template:
            return None

        return Recommendation(
            priority=priority,
            title=template[0],
            description=template[1],
            related_insight_type=insight.insight_type,
        )

    # ══════════════════════════════════════════════════════════════
    # Data Quality Assessment
    # ══════════════════════════════════════════════════════════════

    def _assess_data_quality(
        self, trip: Trip, expenses: Sequence[Expense],
        fuel_transactions: Sequence[FuelTransaction],
    ) -> DataQuality:
        signals = 0
        if trip.revenue is not None:
            signals += 1
        if expenses:
            signals += 1
        if trip.planned_distance and trip.actual_distance:
            signals += 1
        if trip.planned_start_time and trip.actual_end_time:
            signals += 1
        if fuel_transactions:
            signals += 1
        if trip.planned_cost:
            signals += 1

        if signals >= 5:
            return DataQuality.HIGH
        elif signals >= 3:
            return DataQuality.MEDIUM
        elif signals >= 1:
            return DataQuality.LOW
        else:
            return DataQuality.INSUFFICIENT

    # ══════════════════════════════════════════════════════════════
    # Utility Helpers
    # ══════════════════════════════════════════════════════════════

    @staticmethod
    def _calc_duration_hours(
        start: Optional[datetime], end: Optional[datetime]
    ) -> Optional[float]:
        if not start or not end:
            return None
        s = start.replace(tzinfo=None) if start.tzinfo else start
        e = end.replace(tzinfo=None) if end.tzinfo else end
        delta = e - s
        return delta.total_seconds() / 3600

    @staticmethod
    def _calc_variance(
        planned: Optional[float], actual: Optional[float],
        warning_pct: float = 10.0, critical_pct: float = 25.0,
    ) -> tuple[Optional[float], Optional[float], InsightSeverity]:
        if planned is None or actual is None:
            return None, None, InsightSeverity.INFO
        variance = actual - planned
        variance_pct = (variance / planned * 100) if planned != 0 else None
        severity = InsightSeverity.INFO
        if variance_pct is not None:
            if abs(variance_pct) > critical_pct:
                severity = InsightSeverity.CRITICAL
            elif abs(variance_pct) > warning_pct:
                severity = InsightSeverity.WARNING
            variance_pct = round(variance_pct, 1)
        return variance, variance_pct, severity

    @staticmethod
    def _estimate_fuel_cost_impact(
        excess_liters: float, expenses: Sequence[Expense]
    ) -> Optional[float]:
        """Estimate the cost impact of excess fuel consumption."""
        fuel_expenses = [e for e in expenses if e.category and e.category.value == "FUEL"]
        if fuel_expenses:
            total_fuel_cost = sum(e.amount for e in fuel_expenses)
            total_fuel_liters = sum(e.amount for e in fuel_expenses)  # rough
            # Try to derive per-liter cost from fuel expenses
            if total_fuel_cost > 0 and len(fuel_expenses) > 0:
                avg_per_liter = total_fuel_cost / max(len(fuel_expenses), 1)
                # Rough estimate: assume ~100 INR/liter as fallback
                per_liter = 100.0
                return round(excess_liters * per_liter, 2)
        # Fallback: estimate at ₹100/liter
        return round(excess_liters * 100, 2)
