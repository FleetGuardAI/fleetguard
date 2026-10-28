"""
FleetGuard — Evidence-Grounded Fleet Intelligence Engine (P3)
Canonical service responsible for calculating deterministic operational metrics,
detecting threshold-based anomalies, and generating structured findings with
traceable evidence, explainable baselines, and safe action handoffs.

Strictly bounded to authenticated tenant company_id.
Never manufactures speculative baselines or autonomous write actions.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Sequence
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models.vehicle_domain import Vehicle, VehicleStatus
from models.driver_domain import Driver, DriverStatus, DutyStatus
from models.trip_domain import Trip, TripStatus
from models.location_tracking import DriverLocation, LocationSource
from models.maintenance_domain import MaintenanceRecord, MaintenanceStatus, MaintenanceCategory
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus
from schemas.fleet_intelligence import (
    FindingCategory, FindingSeverity, DataQualityStatus, ActionHandoff,
    EvidenceGroundedFinding, TelemetryHealthSummary, MaintenanceHealthSummary,
    TripHealthSummary, FleetHealthOverview, FuelVehicleMetric, FuelEfficiencyAnalysis,
    MaintenancePrioritiesResponse, TripPerformanceAnalysis, DataQualityResponse,
    FleetAnomaliesResponse
)

logger = logging.getLogger("fleetguard.intelligence.engine")


class FleetIntelligenceEngine:
    """
    Evidence-grounded fleet intelligence coordinator.
    Enforces tenant boundaries and computes deterministic operational insights.
    """

    def __init__(self, uow: Any, company_id: int):
        self.uow = uow
        self.company_id = int(company_id)
        # Thresholds from project configuration
        self.gps_stale_secs = getattr(settings, "INTELLIGENCE_GPS_STALE_MINUTES", 15) * 60.0
        self.gps_unavail_secs = getattr(settings, "INTELLIGENCE_GPS_UNAVAILABLE_HOURS", 24) * 3600.0
        self.maint_due_soon_days = getattr(settings, "INTELLIGENCE_MAINTENANCE_DUE_SOON_DAYS", 7)
        self.maint_due_soon_km = getattr(settings, "INTELLIGENCE_MAINTENANCE_DUE_SOON_KM", 500.0)
        self.trip_delay_hours = getattr(settings, "INTELLIGENCE_TRIP_DELAY_THRESHOLD_HOURS", 2.0)
        self.trip_dist_dev_pct = getattr(settings, "INTELLIGENCE_TRIP_DISTANCE_DEVIATION_PCT", 15.0)
        self.fuel_anomaly_dev_pct = getattr(settings, "INTELLIGENCE_FUEL_ANOMALY_DEVIATION_PCT", 20.0)

    def _get_session(self) -> AsyncSession:
        if hasattr(self.uow, "session") and self.uow.session is not None:
            return self.uow.session
        if hasattr(self.uow, "_session") and self.uow._session is not None:
            return self.uow._session
        if hasattr(self.uow, "repositories") and hasattr(self.uow.repositories, "vehicle"):
            return self.uow.repositories.vehicle.db
        raise RuntimeError("No active database session available in Unit of Work.")

    async def _get_vehicle_latest_location(
        self, session: AsyncSession, v: Vehicle
    ) -> Tuple[Optional[datetime], Optional[DriverLocation]]:
        """
        Resolves latest GPS telemetry and timestamp for a vehicle by checking:
        1. Driver on active in-progress trip
        2. Vehicle's assigned driver
        3. Driver's latest recorded location point in DriverLocation or last_location_at
        """
        driver_id = None
        trip_stmt = (
            select(Trip.driver_id)
            .where(
                Trip.company_id == self.company_id,
                Trip.vehicle_id == v.id,
                Trip.status == TripStatus.IN_PROGRESS
            )
            .limit(1)
        )
        trip_res = await session.execute(trip_stmt)
        active_driver_id = trip_res.scalar_one_or_none()
        if active_driver_id:
            driver_id = active_driver_id
        elif v.assigned_driver_id:
            driver_id = v.assigned_driver_id

        if driver_id:
            loc_res = await session.execute(
                select(DriverLocation)
                .where(
                    DriverLocation.company_id == self.company_id,
                    DriverLocation.driver_id == driver_id
                )
                .order_by(desc(DriverLocation.timestamp))
                .limit(1)
            )
            latest_loc = loc_res.scalar_one_or_none()
            if latest_loc and latest_loc.timestamp:
                return latest_loc.timestamp, latest_loc

            drv = await session.get(Driver, driver_id)
            if drv and drv.last_location_at:
                return drv.last_location_at, None

        return None, None

    # ==========================================================================
    # 1. FLEET HEALTH OVERVIEW
    # ==========================================================================

    async def get_fleet_health_overview(self) -> FleetHealthOverview:
        """
        Calculates authoritative fleet-level health aggregations:
        - Active vs maintenance vehicles
        - Telemetry freshness (fresh, stale, unavailable)
        - Maintenance schedules (overdue, due soon, up to date)
        - Trip states (in progress, delayed, recent completions)
        - Data quality flags and priority findings
        """
        session = self._get_session()
        now = datetime.now(timezone.utc)

        # 1. Vehicles
        v_res = await session.execute(
            select(Vehicle).where(Vehicle.company_id == self.company_id)
        )
        vehicles = v_res.scalars().all()
        total_vehicles = len(vehicles)
        active_vehicles = sum(1 for v in vehicles if v.status == VehicleStatus.ACTIVE)
        maintenance_vehicles = sum(1 for v in vehicles if v.status == VehicleStatus.MAINTENANCE)

        # 2. Telemetry freshness breakdown
        fresh_gps = 0
        stale_gps = 0
        unavailable_gps = 0
        telemetry_findings: List[EvidenceGroundedFinding] = []

        for v in vehicles:
            loc_time, latest_loc = await self._get_vehicle_latest_location(session, v)

            if not loc_time:
                unavailable_gps += 1
                telemetry_findings.append(EvidenceGroundedFinding(
                    finding_id=f"FIND-GPS-UNAVAIL-{v.id}",
                    category=FindingCategory.DATA_QUALITY,
                    severity=FindingSeverity.HIGH,
                    title=f"GPS Telemetry Unavailable: {v.registration_number}",
                    summary=f"No GPS coordinates recorded for vehicle {v.registration_number}.",
                    entity_type="VEHICLE",
                    entity_id=str(v.id),
                    entity_name=f"{v.registration_number} ({v.make or ''} {v.model or ''})".strip(),
                    observation_period="Continuous Telematics Audit",
                    measured_value="0 location points",
                    baseline_value=f"Heartbeat required within {int(self.gps_stale_secs/60)} minutes",
                    data_quality_status=DataQualityStatus.INCOMPLETE_RECORDS,
                    confidence="HIGH",
                    recommended_action=f"Inspect GPS tracking device or driver mobile companion app for vehicle {v.registration_number}.",
                    limitations="Missing telematics indicates hardware/connectivity failure, not vehicle breakdown.",
                    action_handoff=ActionHandoff(
                        screen="vehicles",
                        entity_type="VEHICLE",
                        entity_id=str(v.id),
                        route=f"/vehicles",
                        action_label="View Vehicle Details"
                    )
                ))
            else:
                if loc_time.tzinfo is None:
                    loc_time = loc_time.replace(tzinfo=timezone.utc)
                age_seconds = (now - loc_time).total_seconds()

                src = latest_loc.source.value if (latest_loc and hasattr(latest_loc.source, "value")) else (str(latest_loc.source) if latest_loc else "APP")
                ev_label = f"DriverLocation ID {latest_loc.id} ({src})" if latest_loc else "Driver Last Known"

                if age_seconds <= self.gps_stale_secs:
                    fresh_gps += 1
                elif age_seconds <= self.gps_unavail_secs:
                    stale_gps += 1
                    telemetry_findings.append(EvidenceGroundedFinding(
                        finding_id=f"FIND-GPS-STALE-{v.id}",
                        category=FindingCategory.DATA_QUALITY,
                        severity=FindingSeverity.MEDIUM,
                        title=f"Delayed Telemetry: {v.registration_number}",
                        summary=f"Last GPS update for {v.registration_number} was {int(age_seconds / 60)} minutes ago.",
                        entity_type="VEHICLE",
                        entity_id=str(v.id),
                        entity_name=v.registration_number,
                        observation_period="Continuous Telematics Audit",
                        measured_value=f"{int(age_seconds / 60)} min delay",
                        baseline_value=f"<{int(self.gps_stale_secs / 60)} min expected",
                        evidence_records=[f"{ev_label} at {loc_time.isoformat()}"],
                        data_quality_status=DataQualityStatus.STALE_TELEMETRY,
                        confidence="HIGH",
                        recommended_action=f"Verify network connectivity for vehicle {v.registration_number} tracking hardware.",
                        limitations="Vehicle position represents last-known fix, not confirmed live location."
                    ))
                else:
                    unavailable_gps += 1
                    telemetry_findings.append(EvidenceGroundedFinding(
                        finding_id=f"FIND-GPS-VERY-STALE-{v.id}",
                        category=FindingCategory.DATA_QUALITY,
                        severity=FindingSeverity.HIGH,
                        title=f"Stale Telemetry (>24h): {v.registration_number}",
                        summary=f"Vehicle {v.registration_number} has not transmitted GPS coordinates for {int(age_seconds / 3600)} hours.",
                        entity_type="VEHICLE",
                        entity_id=str(v.id),
                        entity_name=v.registration_number,
                        observation_period="Continuous Telematics Audit",
                        measured_value=f"{int(age_seconds / 3600)}h offline",
                        baseline_value="Continuous live transmission",
                        evidence_records=[f"{ev_label} at {loc_time.isoformat()}"],
                        data_quality_status=DataQualityStatus.STALE_TELEMETRY,
                        confidence="HIGH",
                        recommended_action=f"Check if vehicle {v.registration_number} device is powered off or disconnected.",
                        limitations="Device is offline. Do not assume vehicle is stationary or broken down."
                    ))

        fresh_pct = round((fresh_gps / total_vehicles * 100.0), 1) if total_vehicles > 0 else 0.0

        # 3. Maintenance breakdown
        maint_priorities = await self.get_maintenance_priorities(limit=10)
        overdue_count = maint_priorities.total_overdue
        due_soon_count = maint_priorities.total_due_soon
        up_to_date_count = max(0, total_vehicles - overdue_count - due_soon_count)

        # 4. Trip Health Breakdown
        trip_perf = await self.analyze_trip_performance(days=30, limit=10)
        in_progress_count = 0
        delayed_count = trip_perf.delayed_trips_count
        completed_last_30d = 0

        trips_res = await session.execute(
            select(Trip).where(Trip.company_id == self.company_id)
        )
        all_trips = trips_res.scalars().all()
        for t in all_trips:
            if t.status == TripStatus.IN_PROGRESS:
                in_progress_count += 1
            elif t.status == TripStatus.COMPLETED and t.actual_end_time:
                t_end = t.actual_end_time.replace(tzinfo=timezone.utc) if t.actual_end_time.tzinfo is None else t.actual_end_time
                if (now - t_end).total_seconds() <= 30 * 86400:
                    completed_last_30d += 1

        # 5. Compile top key findings
        all_key_findings: List[EvidenceGroundedFinding] = []
        all_key_findings.extend(maint_priorities.findings[:3])
        all_key_findings.extend(trip_perf.findings[:3])
        all_key_findings.extend(telemetry_findings[:2])

        # Overall Status
        has_critical = any(f.severity == FindingSeverity.CRITICAL for f in all_key_findings) or overdue_count > 0
        has_high = any(f.severity == FindingSeverity.HIGH for f in all_key_findings) or delayed_count > 0 or unavailable_gps > 0
        if has_critical:
            overall_status = "CRITICAL"
        elif has_high:
            overall_status = "ATTENTION_REQUIRED"
        else:
            overall_status = "HEALTHY"

        return FleetHealthOverview(
            company_id=self.company_id,
            generated_at=now,
            overall_health_status=overall_status,
            total_vehicles=total_vehicles,
            active_vehicles=active_vehicles,
            maintenance_vehicles=maintenance_vehicles,
            telemetry=TelemetryHealthSummary(
                fresh_count=fresh_gps,
                stale_count=stale_gps,
                unavailable_count=unavailable_gps,
                fresh_percentage=fresh_pct
            ),
            maintenance=MaintenanceHealthSummary(
                overdue_count=overdue_count,
                due_soon_count=due_soon_count,
                up_to_date_count=up_to_date_count
            ),
            trips=TripHealthSummary(
                in_progress_count=in_progress_count,
                delayed_count=delayed_count,
                completed_last_30d=completed_last_30d
            ),
            fuel_anomalies_count=0,
            data_quality_flags_count=len(telemetry_findings),
            key_findings=all_key_findings[:5]
        )

    # ==========================================================================
    # 2. FUEL & VEHICLE ECONOMICS ANALYSIS
    # ==========================================================================

    async def analyze_fuel_efficiency(
        self,
        vehicle_id: Optional[int] = None,
        period_days: int = 30,
        compare_previous: bool = True
    ) -> FuelEfficiencyAnalysis:
        """
        Authoritative fuel economics calculation using verified expenses and completed trips:
        - Current vs previous period fuel spend without double-counting
        - True consumption per km (km/L and L/100km) based strictly on paired distance & fuel
        - Flags anomalies when vehicle consumption exceeds baseline by > 20%
        - Returns INSUFFICIENT_HISTORY when distance or fuel data is absent
        """
        session = self._get_session()
        now = datetime.now(timezone.utc)
        start_curr = now - timedelta(days=period_days)
        start_prev = start_curr - timedelta(days=period_days)

        obs_period_str = f"Last {period_days} days ({start_curr.strftime('%b %d')} - {now.strftime('%b %d, %Y')})"

        # 1. Query approved fuel expenses in current and previous periods
        curr_exp_stmt = select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
            Expense.company_id == self.company_id,
            Expense.category == ExpenseCategory.FUEL,
            Expense.status == ExpenseStatus.APPROVED,
            Expense.expense_date >= start_curr,
            Expense.expense_date <= now
        )
        if vehicle_id:
            curr_exp_stmt = curr_exp_stmt.where(Expense.vehicle_id == vehicle_id)
        curr_spend = float((await session.execute(curr_exp_stmt)).scalar_one())

        prev_spend = None
        spend_change_pct = None
        if compare_previous:
            prev_exp_stmt = select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
                Expense.company_id == self.company_id,
                Expense.category == ExpenseCategory.FUEL,
                Expense.status == ExpenseStatus.APPROVED,
                Expense.expense_date >= start_prev,
                Expense.expense_date < start_curr
            )
            if vehicle_id:
                prev_exp_stmt = prev_exp_stmt.where(Expense.vehicle_id == vehicle_id)
            prev_spend = float((await session.execute(prev_exp_stmt)).scalar_one())
            if prev_spend > 0:
                spend_change_pct = round(((curr_spend - prev_spend) / prev_spend) * 100.0, 1)

        # 2. Query completed trips in current period for distance and fuel
        trip_stmt = select(Trip).where(
            Trip.company_id == self.company_id,
            Trip.status == TripStatus.COMPLETED,
            Trip.actual_end_time >= start_curr,
            Trip.actual_end_time <= now
        )
        if vehicle_id:
            trip_stmt = trip_stmt.where(Trip.vehicle_id == vehicle_id)
        trips = (await session.execute(trip_stmt)).scalars().all()

        total_distance = sum(float(t.actual_distance or 0.0) for t in trips if t.actual_distance and t.actual_distance > 0)
        total_fuel = sum(float(t.actual_fuel_liters or 0.0) for t in trips if t.actual_fuel_liters and t.actual_fuel_liters > 0)

        # 3. Aggregate paired telemetry per vehicle
        # Paired: Trip has both actual_distance > 0 and actual_fuel_liters > 0
        vehicle_agg: Dict[int, Dict[str, Any]] = {}
        for t in trips:
            if not t.vehicle_id:
                continue
            if t.vehicle_id not in vehicle_agg:
                v_obj = t.vehicle
                reg = v_obj.registration_number if v_obj else f"Vehicle {t.vehicle_id}"
                make_model = f"{v_obj.make or ''} {v_obj.model or ''}".strip() if v_obj else "Commercial Truck"
                vehicle_agg[t.vehicle_id] = {
                    "vehicle_id": t.vehicle_id,
                    "registration_number": reg,
                    "make_model": make_model,
                    "distance": 0.0,
                    "fuel": 0.0,
                    "trip_count": 0,
                    "trip_ids": []
                }
            if t.actual_distance and t.actual_distance > 0 and t.actual_fuel_liters and t.actual_fuel_liters > 0:
                vehicle_agg[t.vehicle_id]["distance"] += float(t.actual_distance)
                vehicle_agg[t.vehicle_id]["fuel"] += float(t.actual_fuel_liters)
                vehicle_agg[t.vehicle_id]["trip_count"] += 1
                vehicle_agg[t.vehicle_id]["trip_ids"].append(t.trip_id)

        # Also get vehicle-specific expenses
        for vid, vdata in vehicle_agg.items():
            ve_res = await session.execute(
                select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
                    Expense.company_id == self.company_id,
                    Expense.vehicle_id == vid,
                    Expense.category == ExpenseCategory.FUEL,
                    Expense.status == ExpenseStatus.APPROVED,
                    Expense.expense_date >= start_curr
                )
            )
            vdata["expense"] = float(ve_res.scalar_one())

        # 4. Compute fleet averages
        total_paired_dist = sum(v["distance"] for v in vehicle_agg.values())
        total_paired_fuel = sum(v["fuel"] for v in vehicle_agg.values())

        fleet_km_per_l = round(total_paired_dist / total_paired_fuel, 2) if total_paired_fuel > 0 else None
        fleet_l_per_100km = round((total_paired_fuel / total_paired_dist) * 100.0, 2) if total_paired_dist > 0 else None

        findings: List[EvidenceGroundedFinding] = []
        vehicle_metrics: List[FuelVehicleMetric] = []

        # Check for Spend Increase Anomaly
        if spend_change_pct is not None and spend_change_pct >= 25.0 and curr_spend >= 5000:
            findings.append(EvidenceGroundedFinding(
                finding_id="FIND-FUEL-SPEND-SURGE",
                category=FindingCategory.FUEL_EFFICIENCY,
                severity=FindingSeverity.HIGH,
                title=f"Fuel Spend Increased by {spend_change_pct}%",
                summary=f"Fuel expenditure rose from ₹{prev_spend:,.0f} in the prior period to ₹{curr_spend:,.0f} ({spend_change_pct:+.1f}%).",
                observation_period=obs_period_str,
                measured_value=f"₹{curr_spend:,.0f}",
                baseline_value=f"₹{prev_spend:,.0f} (previous {period_days} days)",
                deviation_percent=spend_change_pct,
                data_quality_status=DataQualityStatus.RELIABLE,
                confidence="HIGH",
                recommended_action="Review approved fuel expense receipts and verify if fleet distance or active trips increased proportionally.",
                limitations="Calculated from approved fuel expenses. Does not account for fuel price inflation or wholesale tariff shifts.",
                action_handoff=ActionHandoff(
                    screen="expenses",
                    entity_type="EXPENSE",
                    route="/expenses",
                    action_label="Review Fuel Expenses"
                )
            ))

        # Check for Vehicle-level consumption anomalies
        for vid, vdata in vehicle_agg.items():
            dist = vdata["distance"]
            fuel = vdata["fuel"]
            kpl = round(dist / fuel, 2) if fuel > 0 else None
            lp100 = round((fuel / dist) * 100.0, 2) if dist > 0 else None
            is_anomaly = False
            anomaly_reason = None

            if lp100 is not None and fleet_l_per_100km is not None and vdata["trip_count"] >= 2:
                pct_worse = ((lp100 - fleet_l_per_100km) / fleet_l_per_100km) * 100.0
                if pct_worse >= self.fuel_anomaly_dev_pct:
                    is_anomaly = True
                    anomaly_reason = f"Consumption {lp100} L/100km exceeds fleet average ({fleet_l_per_100km} L/100km) by {pct_worse:.1f}%"
                    findings.append(EvidenceGroundedFinding(
                        finding_id=f"FIND-FUEL-HIGH-CONSUMPTION-{vid}",
                        category=FindingCategory.FUEL_EFFICIENCY,
                        severity=FindingSeverity.HIGH,
                        title=f"Excess Fuel Consumption: {vdata['registration_number']}",
                        summary=f"Vehicle {vdata['registration_number']} consumed {lp100} L/100km ({kpl} km/L), which is {pct_worse:.1f}% higher than fleet baseline.",
                        entity_type="VEHICLE",
                        entity_id=str(vid),
                        entity_name=vdata["registration_number"],
                        observation_period=obs_period_str,
                        measured_value=f"{lp100} L/100km ({kpl} km/L)",
                        baseline_value=f"{fleet_l_per_100km} L/100km (Fleet Average)",
                        deviation_percent=round(pct_worse, 1),
                        evidence_records=[f"Trips: {', '.join(vdata['trip_ids'][:3])} (total paired: {int(dist)} km, {int(fuel)} L)"],
                        data_quality_status=DataQualityStatus.RELIABLE,
                        confidence="HIGH",
                        recommended_action=f"Inspect engine fuel injectors and air filters for {vdata['registration_number']}, and check driver idling patterns.",
                        limitations="Comparison uses fleet-wide average. Heavy terrain or high cargo payload can legitimately increase consumption.",
                        action_handoff=ActionHandoff(
                            screen="vehicles",
                            entity_type="VEHICLE",
                            entity_id=str(vid),
                            route="/vehicles",
                            action_label="Inspect Vehicle"
                        )
                    ))

            vehicle_metrics.append(FuelVehicleMetric(
                vehicle_id=vid,
                registration_number=vdata["registration_number"],
                make_model=vdata["make_model"],
                distance_km=dist,
                fuel_liters=fuel,
                km_per_liter=kpl,
                liters_per_100km=lp100,
                expense_amount=vdata.get("expense", 0.0),
                is_anomaly=is_anomaly,
                anomaly_reason=anomaly_reason
            ))

        # Check data quality:
        dq_status = DataQualityStatus.RELIABLE
        if total_paired_dist == 0 or total_paired_fuel == 0:
            dq_status = DataQualityStatus.INSUFFICIENT_HISTORY
            findings.append(EvidenceGroundedFinding(
                finding_id="FIND-FUEL-DATA-INSUFFICIENT",
                category=FindingCategory.DATA_QUALITY,
                severity=FindingSeverity.MEDIUM,
                title="Insufficient Paired Telemetry for Fuel Consumption",
                summary="Completed trips during this period lack paired distance and fuel measurements required for km/L calculation.",
                observation_period=obs_period_str,
                measured_value="0 paired trip records",
                baseline_value="At least 2 completed trips with distance & fuel telemetry",
                data_quality_status=DataQualityStatus.INSUFFICIENT_HISTORY,
                confidence="HIGH",
                recommended_action="Ensure drivers log actual trip fuel or connect vehicle CAN/telematics sensors.",
                limitations="Fuel expenditure was tracked from approved expenses, but efficiency metrics cannot be estimated without paired distance."
            ))

        return FuelEfficiencyAnalysis(
            company_id=self.company_id,
            observation_period=obs_period_str,
            current_period_spend=curr_spend,
            previous_period_spend=prev_spend,
            spend_change_pct=spend_change_pct,
            total_distance_km=total_distance,
            total_fuel_liters=total_fuel,
            fleet_avg_km_per_liter=fleet_km_per_l,
            fleet_avg_liters_per_100km=fleet_l_per_100km,
            data_quality_status=dq_status,
            findings=findings,
            vehicle_metrics=vehicle_metrics,
            limitations="Metrics use approved expenses and completed trips with paired actual distance and fuel. No speculative values were manufactured."
        )

    # ==========================================================================
    # 3. MAINTENANCE & RELIABILITY INTELLIGENCE
    # ==========================================================================

    async def get_maintenance_priorities(
        self,
        status_filter: Optional[str] = None,
        limit: int = 15
    ) -> MaintenancePrioritiesResponse:
        """
        Evaluates vehicles for:
        - Overdue maintenance (by odometer or date)
        - Due-soon maintenance (within 500 km or 7 days)
        - Repeated maintenance patterns (>= 2 records in past 60 days)
        - Odometer inconsistencies (current < service odometer)
        """
        session = self._get_session()
        now = datetime.now(timezone.utc)

        v_res = await session.execute(
            select(Vehicle).where(Vehicle.company_id == self.company_id)
        )
        vehicles = v_res.scalars().all()

        findings: List[EvidenceGroundedFinding] = []
        total_overdue = 0
        total_due_soon = 0
        total_repeat = 0

        # 1. Vehicle-level schedule evaluations
        for v in vehicles:
            is_overdue = False
            is_due_soon = False
            overdue_reasons = []
            due_soon_reasons = []

            # By Odometer
            if v.current_odometer and v.last_service_odometer and v.maintenance_interval_km:
                next_km = v.last_service_odometer + v.maintenance_interval_km
                rem_km = next_km - v.current_odometer
                if rem_km < 0:
                    is_overdue = True
                    overdue_reasons.append(f"Odometer exceeded by {abs(int(rem_km)):,} km (Current: {int(v.current_odometer):,} km vs Next Due: {int(next_km):,} km)")
                elif rem_km <= self.maint_due_soon_km:
                    is_due_soon = True
                    due_soon_reasons.append(f"Due within {int(rem_km):,} km (Current: {int(v.current_odometer):,} km vs Next Due: {int(next_km):,} km)")

            # By Date
            if v.last_service_date and v.maintenance_interval_days:
                svc_date = v.last_service_date.replace(tzinfo=timezone.utc) if v.last_service_date.tzinfo is None else v.last_service_date
                next_date = svc_date + timedelta(days=v.maintenance_interval_days)
                diff_seconds = (next_date - now).total_seconds()
                diff_days = int(round(diff_seconds / 86400.0))
                if diff_seconds < 0:
                    is_overdue = True
                    overdue_reasons.append(f"Date exceeded by {abs(diff_days)} days (Due: {next_date.strftime('%b %d, %Y')})")
                elif diff_days <= self.maint_due_soon_days:
                    is_due_soon = True
                    due_soon_reasons.append(f"Due in {diff_days} days (Due: {next_date.strftime('%b %d, %Y')})")

            # Check explicit status
            if v.maintenance_status == "OVERDUE" and not is_overdue:
                is_overdue = True
                overdue_reasons.append("Vehicle flag explicitly set to OVERDUE in maintenance ledger.")
            elif v.maintenance_status == "DUE_SOON" and not is_due_soon and not is_overdue:
                is_due_soon = True
                due_soon_reasons.append("Vehicle flag set to DUE_SOON.")

            # Odometer inconsistency check
            if v.current_odometer and v.last_service_odometer and v.current_odometer < v.last_service_odometer:
                findings.append(EvidenceGroundedFinding(
                    finding_id=f"FIND-MAINT-ODO-INCONSISTENCY-{v.id}",
                    category=FindingCategory.DATA_QUALITY,
                    severity=FindingSeverity.HIGH,
                    title=f"Odometer Reading Inconsistency: {v.registration_number}",
                    summary=f"Current odometer ({int(v.current_odometer):,} km) is less than recorded last service odometer ({int(v.last_service_odometer):,} km).",
                    entity_type="VEHICLE",
                    entity_id=str(v.id),
                    entity_name=v.registration_number,
                    observation_period="Current Registry Audit",
                    measured_value=f"{int(v.current_odometer):,} km",
                    baseline_value=f"Last service: {int(v.last_service_odometer):,} km",
                    data_quality_status=DataQualityStatus.INCOMPLETE_RECORDS,
                    confidence="HIGH",
                    recommended_action="Inspect vehicle dashboard and correct odometer telemetry entry.",
                    limitations="Represents data entry error or sensor replacement without calibration."
                ))

            if is_overdue:
                total_overdue += 1
                findings.append(EvidenceGroundedFinding(
                    finding_id=f"FIND-MAINT-OVERDUE-{v.id}",
                    category=FindingCategory.MAINTENANCE,
                    severity=FindingSeverity.CRITICAL,
                    title=f"Overdue Maintenance: {v.registration_number}",
                    summary=f"Vehicle {v.registration_number} has exceeded its scheduled service window: {'; '.join(overdue_reasons)}.",
                    entity_type="VEHICLE",
                    entity_id=str(v.id),
                    entity_name=f"{v.registration_number} ({v.make or ''} {v.model or ''})".strip(),
                    observation_period="Active Schedule Evaluation",
                    measured_value="OVERDUE",
                    baseline_value=f"Service interval: {v.maintenance_interval_km or 'N/A'} km / {v.maintenance_interval_days or 'N/A'} days",
                    data_quality_status=DataQualityStatus.RELIABLE,
                    confidence="HIGH",
                    recommended_action=f"Do not dispatch {v.registration_number} on long-haul routes; schedule workshop service immediately.",
                    limitations="Evaluated using vehicle odometer and service date intervals.",
                    action_handoff=ActionHandoff(
                        screen="maintenance",
                        entity_type="VEHICLE",
                        entity_id=str(v.id),
                        route="/maintenance",
                        action_label="Schedule Service"
                    )
                ))
            elif is_due_soon:
                total_due_soon += 1
                findings.append(EvidenceGroundedFinding(
                    finding_id=f"FIND-MAINT-DUE-SOON-{v.id}",
                    category=FindingCategory.MAINTENANCE,
                    severity=FindingSeverity.MEDIUM,
                    title=f"Maintenance Due Soon: {v.registration_number}",
                    summary=f"Vehicle {v.registration_number} service window approaching: {'; '.join(due_soon_reasons)}.",
                    entity_type="VEHICLE",
                    entity_id=str(v.id),
                    entity_name=v.registration_number,
                    observation_period="Active Schedule Evaluation",
                    measured_value="DUE_SOON",
                    baseline_value=f"Threshold: <{int(self.maint_due_soon_km)} km or <{self.maint_due_soon_days} days",
                    data_quality_status=DataQualityStatus.RELIABLE,
                    confidence="HIGH",
                    recommended_action=f"Plan upcoming maintenance for {v.registration_number} before next scheduled trip.",
                    action_handoff=ActionHandoff(
                        screen="maintenance",
                        entity_type="VEHICLE",
                        entity_id=str(v.id),
                        route="/maintenance",
                        action_label="View Maintenance"
                    )
                ))

        # 2. Check for Chronic / Repeated Maintenance records in past 60 days
        sixty_days_ago = now - timedelta(days=60)
        rec_stmt = select(MaintenanceRecord).where(
            MaintenanceRecord.company_id == self.company_id,
            MaintenanceRecord.scheduled_date >= sixty_days_ago
        )
        records = (await session.execute(rec_stmt)).scalars().all()

        v_maint_count: Dict[int, List[MaintenanceRecord]] = {}
        for r in records:
            if r.vehicle_id:
                v_maint_count.setdefault(r.vehicle_id, []).append(r)

        for vid, m_list in v_maint_count.items():
            if len(m_list) >= 2:
                total_repeat += 1
                v_obj = await session.get(Vehicle, vid)
                reg = v_obj.registration_number if v_obj else f"Vehicle {vid}"
                costs = sum(float(r.cost or 0.0) for r in m_list)
                cats = list(set(r.category.value if hasattr(r.category, "value") else str(r.category) for r in m_list))

                findings.append(EvidenceGroundedFinding(
                    finding_id=f"FIND-MAINT-REPEAT-{vid}",
                    category=FindingCategory.MAINTENANCE,
                    severity=FindingSeverity.HIGH,
                    title=f"Repeated Maintenance Events: {reg}",
                    summary=f"Vehicle {reg} underwent {len(m_list)} maintenance events in the last 60 days (total cost: ₹{costs:,.0f}). Categories: {', '.join(cats)}.",
                    entity_type="VEHICLE",
                    entity_id=str(vid),
                    entity_name=reg,
                    observation_period="Last 60 days",
                    measured_value=f"{len(m_list)} maintenance records",
                    baseline_value="Max 1 maintenance event per 60-day window",
                    evidence_records=[f"Record {r.business_id} ({r.category}) cost ₹{float(r.cost or 0.0):,.0f}" for r in m_list[:3]],
                    data_quality_status=DataQualityStatus.RELIABLE,
                    confidence="HIGH",
                    recommended_action=f"Perform a comprehensive root-cause diagnostic for {reg} to prevent chronic breakdown cycles.",
                    limitations="Based on recorded maintenance entries. Excludes unrecorded roadside fixes."
                ))

        # Sort findings: CRITICAL > HIGH > MEDIUM > LOW
        findings.sort(key=lambda f: (
            0 if f.severity == FindingSeverity.CRITICAL else
            1 if f.severity == FindingSeverity.HIGH else
            2 if f.severity == FindingSeverity.MEDIUM else 3
        ))

        return MaintenancePrioritiesResponse(
            company_id=self.company_id,
            total_overdue=total_overdue,
            total_due_soon=total_due_soon,
            total_repeat_issues=total_repeat,
            findings=findings[:limit],
            limitations="Evaluated using vehicle odometer thresholds, scheduled dates, and recorded maintenance history."
        )

    # ==========================================================================
    # 4. TRIP & OPERATIONAL INTELLIGENCE
    # ==========================================================================

    async def analyze_trip_performance(
        self,
        trip_id: Optional[int] = None,
        status: Optional[str] = None,
        days: int = 30,
        limit: int = 15
    ) -> TripPerformanceAnalysis:
        """
        Analyzes trips for:
        - Significant departure delays (status CREATED, planned_start_time passed > 1h)
        - Arrival delays (status IN_PROGRESS, planned_end_time passed)
        - Route distance deviations (> 15% difference between actual and planned km)
        - Unclosed / prolonged trips (> 48 hours without completion)
        """
        session = self._get_session()
        now = datetime.now(timezone.utc)
        since_date = now - timedelta(days=days)

        query = select(Trip).where(
            Trip.company_id == self.company_id
        )
        if trip_id:
            query = query.where(Trip.id == trip_id)
        if status and status != "ALL":
            query = query.where(Trip.status == status)

        trips = (await session.execute(query)).scalars().all()

        findings: List[EvidenceGroundedFinding] = []
        delayed_trips_count = 0
        distance_anomalies_count = 0
        unclosed_trips_count = 0

        for t in trips:
            # 1. Departure Delay check
            if t.status == TripStatus.CREATED and t.planned_start_time:
                p_start = t.planned_start_time.replace(tzinfo=timezone.utc) if t.planned_start_time.tzinfo is None else t.planned_start_time
                if p_start < (now - timedelta(hours=1)):
                    delay_hrs = round((now - p_start).total_seconds() / 3600.0, 1)
                    delayed_trips_count += 1
                    severity = FindingSeverity.CRITICAL if delay_hrs >= 4.0 else FindingSeverity.HIGH if delay_hrs >= self.trip_delay_hours else FindingSeverity.MEDIUM
                    findings.append(EvidenceGroundedFinding(
                        finding_id=f"FIND-TRIP-DEP-DELAY-{t.id}",
                        category=FindingCategory.TRIP_OPERATIONS,
                        severity=severity,
                        title=f"Dispatch Delay: {t.trip_id} ({delay_hrs}h overdue)",
                        summary=f"Trip {t.trip_id} ({t.origin_location} -> {t.destination_location}) was scheduled to depart at {p_start.strftime('%b %d, %H:%M')} but is still in CREATED status.",
                        entity_type="TRIP",
                        entity_id=str(t.id),
                        entity_name=f"{t.trip_id} ({t.origin_location} to {t.destination_location})",
                        observation_period=f"Scheduled {p_start.strftime('%b %d')}",
                        measured_value=f"{delay_hrs} hours overdue",
                        baseline_value=f"Scheduled departure: {p_start.isoformat()}",
                        evidence_records=[f"Trip {t.trip_id}, vehicle_id={t.vehicle_id}, driver_id={t.driver_id}"],
                        data_quality_status=DataQualityStatus.RELIABLE,
                        confidence="HIGH",
                        recommended_action=f"Confirm driver availability or assign an available relief driver to trip {t.trip_id}.",
                        limitations="Based on planned departure timestamp in system.",
                        action_handoff=ActionHandoff(
                            screen="trips",
                            entity_type="TRIP",
                            entity_id=str(t.id),
                            route="/trips",
                            action_label="Dispatch Trip"
                        )
                    ))

            # 2. Arrival Delay check (En-route)
            elif t.status == TripStatus.IN_PROGRESS and t.planned_end_time:
                p_end = t.planned_end_time.replace(tzinfo=timezone.utc) if t.planned_end_time.tzinfo is None else t.planned_end_time
                if p_end < now:
                    delay_hrs = round((now - p_end).total_seconds() / 3600.0, 1)
                    delayed_trips_count += 1
                    severity = FindingSeverity.CRITICAL if delay_hrs >= 6.0 else FindingSeverity.HIGH if delay_hrs >= self.trip_delay_hours else FindingSeverity.MEDIUM
                    findings.append(EvidenceGroundedFinding(
                        finding_id=f"FIND-TRIP-ARR-DELAY-{t.id}",
                        category=FindingCategory.TRIP_OPERATIONS,
                        severity=severity,
                        title=f"Arrival Delayed: {t.trip_id} (+{delay_hrs}h)",
                        summary=f"Trip {t.trip_id} en route to {t.destination_location} has passed its scheduled delivery time ({p_end.strftime('%b %d, %H:%M')}).",
                        entity_type="TRIP",
                        entity_id=str(t.id),
                        entity_name=t.trip_id,
                        observation_period=f"In Transit to {t.destination_location}",
                        measured_value=f"{delay_hrs} hours delayed",
                        baseline_value=f"Scheduled arrival: {p_end.isoformat()}",
                        evidence_records=[f"Trip {t.trip_id}, actual_start={t.actual_start_time}"],
                        data_quality_status=DataQualityStatus.RELIABLE,
                        confidence="HIGH",
                        recommended_action=f"Check latest GPS location for vehicle assigned to {t.trip_id} to ascertain en-route bottlenecks.",
                        limitations="Traffic congestion, highway tolls, or weather may cause delays beyond driver control."
                    ))

            # 3. Distance Deviation check
            if t.actual_distance and t.planned_distance and t.actual_distance > 0 and t.planned_distance > 0:
                diff_pct = round(((t.actual_distance - t.planned_distance) / t.planned_distance) * 100.0, 1)
                if abs(diff_pct) >= self.trip_dist_dev_pct:
                    distance_anomalies_count += 1
                    severity = FindingSeverity.HIGH if abs(diff_pct) >= 25.0 else FindingSeverity.MEDIUM
                    findings.append(EvidenceGroundedFinding(
                        finding_id=f"FIND-TRIP-DIST-DEV-{t.id}",
                        category=FindingCategory.TRIP_OPERATIONS,
                        severity=severity,
                        title=f"Route Distance Deviation: {t.trip_id} ({diff_pct:+.1f}%)",
                        summary=f"Trip {t.trip_id} recorded {int(t.actual_distance)} km actual distance vs {int(t.planned_distance)} km planned ({diff_pct:+.1f}% deviation).",
                        entity_type="TRIP",
                        entity_id=str(t.id),
                        entity_name=t.trip_id,
                        observation_period=f"Trip execution {t.trip_id}",
                        measured_value=f"{int(t.actual_distance)} km",
                        baseline_value=f"{int(t.planned_distance)} km (Planned Route)",
                        deviation_percent=diff_pct,
                        evidence_records=[f"Trip {t.trip_id} ({t.origin_location} -> {t.destination_location})"],
                        data_quality_status=DataQualityStatus.RELIABLE,
                        confidence="HIGH",
                        recommended_action=f"Audit GPS route trail for trip {t.trip_id} for unapproved detours or inaccurate odometer entries.",
                        limitations="Actual distance deviations may result from official highway diversions, road construction, or odometer inaccuracy."
                    ))

            # 4. Prolonged Unclosed Trip
            if t.status == TripStatus.IN_PROGRESS and t.actual_start_time:
                act_start = t.actual_start_time.replace(tzinfo=timezone.utc) if t.actual_start_time.tzinfo is None else t.actual_start_time
                duration_hrs = (now - act_start).total_seconds() / 3600.0
                if duration_hrs >= 48.0:
                    unclosed_trips_count += 1
                    findings.append(EvidenceGroundedFinding(
                        finding_id=f"FIND-TRIP-UNCLOSED-{t.id}",
                        category=FindingCategory.TRIP_OPERATIONS,
                        severity=FindingSeverity.HIGH,
                        title=f"Prolonged Unclosed Trip: {t.trip_id} ({int(duration_hrs / 24)}d in progress)",
                        summary=f"Trip {t.trip_id} has remained in IN_PROGRESS status for {int(duration_hrs)} hours without completion.",
                        entity_type="TRIP",
                        entity_id=str(t.id),
                        entity_name=t.trip_id,
                        observation_period=f"Active since {act_start.strftime('%b %d')}",
                        measured_value=f"{int(duration_hrs)} hours",
                        baseline_value="Max 48 hours typical long-haul window",
                        evidence_records=[f"Trip {t.trip_id}, driver_id={t.driver_id}"],
                        data_quality_status=DataQualityStatus.RELIABLE,
                        confidence="HIGH",
                        recommended_action=f"Verify delivery with consignee and mark trip {t.trip_id} completed to release driver and truck.",
                        limitations="Driver may have delivered cargo but neglected to mark completion on mobile app."
                    ))

        # Sort findings: CRITICAL > HIGH > MEDIUM > LOW
        findings.sort(key=lambda f: (
            0 if f.severity == FindingSeverity.CRITICAL else
            1 if f.severity == FindingSeverity.HIGH else
            2 if f.severity == FindingSeverity.MEDIUM else 3
        ))

        return TripPerformanceAnalysis(
            company_id=self.company_id,
            observation_period=f"Last {days} days",
            total_trips_analyzed=len(trips),
            delayed_trips_count=delayed_trips_count,
            distance_anomalies_count=distance_anomalies_count,
            unclosed_trips_count=unclosed_trips_count,
            findings=findings[:limit],
            limitations="Analyzed against scheduled departure/arrival timestamps and planned route distances."
        )

    # ==========================================================================
    # 5. DATA QUALITY FINDINGS
    # ==========================================================================

    async def get_data_quality_findings(self, limit: int = 20) -> DataQualityResponse:
        """
        Identifies data-quality and instrumentation deficiencies:
        - Vehicles with missing or very stale GPS
        - Missing or zero odometer readings
        - Completed trips with 0 actual distance
        - Fuel expenses without volume measurements
        Clearly labels data gaps as instrumentation issues, NOT mechanical defects.
        """
        session = self._get_session()
        now = datetime.now(timezone.utc)

        v_res = await session.execute(
            select(Vehicle).where(Vehicle.company_id == self.company_id)
        )
        vehicles = v_res.scalars().all()

        findings: List[EvidenceGroundedFinding] = []
        fresh_gps = 0
        stale_gps = 0
        no_gps = 0
        missing_odo = 0
        distance_gaps = 0

        # Audit Vehicles
        for v in vehicles:
            # Odometer audit
            if not v.current_odometer or v.current_odometer <= 0:
                missing_odo += 1
                findings.append(EvidenceGroundedFinding(
                    finding_id=f"FIND-DQ-ODO-MISSING-{v.id}",
                    category=FindingCategory.DATA_QUALITY,
                    severity=FindingSeverity.MEDIUM,
                    title=f"Missing Odometer Reading: {v.registration_number}",
                    summary=f"Vehicle {v.registration_number} has an uninitialized or zero odometer reading.",
                    entity_type="VEHICLE",
                    entity_id=str(v.id),
                    entity_name=v.registration_number,
                    observation_period="Current Registry Audit",
                    measured_value=str(v.current_odometer or 0),
                    baseline_value="Valid positive integer odometer",
                    data_quality_status=DataQualityStatus.INCOMPLETE_RECORDS,
                    confidence="HIGH",
                    recommended_action=f"Update current odometer for {v.registration_number} in Vehicle settings.",
                    limitations="Maintenance intervals cannot be calculated by odometer without an initial reading."
                ))

            # GPS audit
            loc_time, loc = await self._get_vehicle_latest_location(session, v)
            if not loc_time:
                no_gps += 1
                findings.append(EvidenceGroundedFinding(
                    finding_id=f"FIND-DQ-NO-GPS-{v.id}",
                    category=FindingCategory.DATA_QUALITY,
                    severity=FindingSeverity.HIGH,
                    title=f"Missing GPS Telemetry: {v.registration_number}",
                    summary=f"Vehicle {v.registration_number} has no GPS location records on file.",
                    entity_type="VEHICLE",
                    entity_id=str(v.id),
                    entity_name=v.registration_number,
                    observation_period="Continuous Telematics Audit",
                    measured_value="0 location records",
                    baseline_value="Live GPS streaming",
                    data_quality_status=DataQualityStatus.INCOMPLETE_RECORDS,
                    confidence="HIGH",
                    recommended_action=f"Pair a tracking device or driver mobile app with vehicle {v.registration_number}.",
                    limitations="Missing telematics indicates hardware/connectivity failure, not vehicle breakdown."
                ))
            else:
                loc_t = loc_time.replace(tzinfo=timezone.utc) if loc_time.tzinfo is None else loc_time
                age_s = (now - loc_t).total_seconds()
                if age_s <= self.gps_stale_secs:
                    fresh_gps += 1
                else:
                    stale_gps += 1

        # Audit Trips for Distance Gaps
        trip_res = await session.execute(
            select(Trip).where(
                Trip.company_id == self.company_id,
                Trip.status == TripStatus.COMPLETED
            ).limit(50)
        )
        completed_trips = trip_res.scalars().all()
        for t in completed_trips:
            if not t.actual_distance or t.actual_distance <= 0:
                distance_gaps += 1
                findings.append(EvidenceGroundedFinding(
                    finding_id=f"FIND-DQ-TRIP-DIST-ZERO-{t.id}",
                    category=FindingCategory.DATA_QUALITY,
                    severity=FindingSeverity.MEDIUM,
                    title=f"Zero Distance on Completed Trip: {t.trip_id}",
                    summary=f"Trip {t.trip_id} was marked COMPLETED but recorded 0 actual distance.",
                    entity_type="TRIP",
                    entity_id=str(t.id),
                    entity_name=t.trip_id,
                    observation_period=f"Trip {t.trip_id}",
                    measured_value="0 km",
                    baseline_value=f"Planned: {t.planned_distance or 'N/A'} km",
                    data_quality_status=DataQualityStatus.INCOMPLETE_RECORDS,
                    confidence="HIGH",
                    recommended_action=f"Record odometer reading or GPS distance for trip {t.trip_id} to preserve mileage accuracy.",
                    limitations="Instrumentation gap only: does not indicate mechanical failure. Trip was completed without odometer entry or GPS stream."
                ))

        total_audits = (len(vehicles) * 2) + len(completed_trips)
        failed_audits = no_gps + missing_odo + distance_gaps
        score = max(0.0, round(((total_audits - failed_audits) / total_audits) * 100.0, 1)) if total_audits > 0 else 100.0

        return DataQualityResponse(
            company_id=self.company_id,
            total_vehicles_audited=len(vehicles),
            vehicles_with_fresh_gps=fresh_gps,
            vehicles_with_stale_gps=stale_gps,
            vehicles_with_no_gps=no_gps,
            vehicles_with_missing_odometer=missing_odo,
            trips_with_distance_gaps=distance_gaps,
            findings=findings[:limit],
            data_completeness_score=score
        )

    # ==========================================================================
    # 6. ALL FLEET ANOMALIES (RANKED)
    # ==========================================================================

    async def get_fleet_anomalies(
        self,
        category: Optional[str] = None,
        min_severity: Optional[str] = None,
        limit: int = 20
    ) -> FleetAnomaliesResponse:
        """
        Collects, filters, and ranks anomalies across all operational domains:
        - Critical: Overdue maintenance, major dispatch delay (>4h), arrival delay (>6h)
        - High: Fuel consumption surge (>20%), repeated maintenance (>2x/60d), stale GPS (>24h)
        - Medium: Due soon maintenance, moderate trip delay, missing odometer
        - Low / Info: General telemetry observations
        """
        all_findings: List[EvidenceGroundedFinding] = []

        # 1. Gather from domains
        fuel_analysis = await self.analyze_fuel_efficiency(period_days=30, compare_previous=True)
        all_findings.extend(fuel_analysis.findings)

        maint_analysis = await self.get_maintenance_priorities(limit=20)
        all_findings.extend(maint_analysis.findings)

        trip_analysis = await self.analyze_trip_performance(days=30, limit=20)
        all_findings.extend(trip_analysis.findings)

        dq_analysis = await self.get_data_quality_findings(limit=20)
        all_findings.extend(dq_analysis.findings)

        # 2. Filter by Category
        if category and category != "ALL":
            all_findings = [f for f in all_findings if f.category.value == category or f.category == category]

        # 3. Filter by Severity
        severity_order = {
            FindingSeverity.CRITICAL: 0,
            FindingSeverity.HIGH: 1,
            FindingSeverity.MEDIUM: 2,
            FindingSeverity.LOW: 3,
            FindingSeverity.INFO: 4
        }
        if min_severity and min_severity != "ALL":
            try:
                min_rank = severity_order[FindingSeverity(min_severity)]
                all_findings = [f for f in all_findings if severity_order[f.severity] <= min_rank]
            except Exception:
                pass

        # 4. Deterministic Sort: Severity rank first, then ID
        all_findings.sort(key=lambda f: (severity_order.get(f.severity, 5), f.finding_id))

        # Deduplicate by finding_id
        seen_ids = set()
        deduped: List[EvidenceGroundedFinding] = []
        for f in all_findings:
            if f.finding_id not in seen_ids:
                seen_ids.add(f.finding_id)
                deduped.append(f)

        crit_count = sum(1 for f in deduped if f.severity == FindingSeverity.CRITICAL)
        high_count = sum(1 for f in deduped if f.severity == FindingSeverity.HIGH)
        med_count = sum(1 for f in deduped if f.severity == FindingSeverity.MEDIUM)
        low_count = sum(1 for f in deduped if f.severity in (FindingSeverity.LOW, FindingSeverity.INFO))

        return FleetAnomaliesResponse(
            company_id=self.company_id,
            total_anomalies=len(deduped),
            critical_count=crit_count,
            high_count=high_count,
            medium_count=med_count,
            low_count=low_count,
            anomalies=deduped[:limit]
        )
