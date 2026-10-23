"""
FleetGuard — Vehicle Economics & Fleet Roll-Up Service
Canonical engine responsible for aggregating trip revenue, approved costs,
actual distance, actual fuel telemetry, and maintenance into vehicle-level and
fleet-level economics.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession

from models.vehicle_domain import Vehicle, VehicleStatus
from models.trip_domain import Trip, TripStatus
from models.expense_domain import Expense, ExpenseStatus, ExpenseCategory
from schemas.vehicle_economics import VehicleEconomicsResponse, FleetRollUpResponse


class VehicleEconomicsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_vehicle_economics(
        self,
        vehicle_id: int,
        company_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[VehicleEconomicsResponse]:
        """
        Calculate canonical economics for a single vehicle.
        Ensures strict tenant isolation by scoping to company_id.
        """
        vehicle = await self.db.get(Vehicle, vehicle_id)
        if not vehicle or vehicle.company_id != company_id:
            return None

        # 1. Query approved expenses for this vehicle
        exp_stmt = (
            select(
                func.coalesce(func.sum(case((Expense.trip_id.isnot(None), Expense.amount), else_=0.0)), 0.0).label("trip_linked_costs"),
                func.coalesce(func.sum(case((Expense.trip_id.is_(None), Expense.amount), else_=0.0)), 0.0).label("vehicle_only_costs")
            )
            .outerjoin(Trip, Expense.trip_id == Trip.id)
            .where(
                Expense.company_id == company_id,
                or_(
                    Expense.vehicle_id == vehicle_id,
                    and_(Expense.trip_id.isnot(None), Trip.vehicle_id == vehicle_id)
                ),
                Expense.status == ExpenseStatus.APPROVED
            )
        )
        if start_date:
            exp_stmt = exp_stmt.where(Expense.expense_date >= start_date)
        if end_date:
            exp_stmt = exp_stmt.where(Expense.expense_date <= end_date)

        exp_res = await self.db.execute(exp_stmt)
        exp_row = exp_res.one()
        trip_linked_costs = float(exp_row.trip_linked_costs or 0.0)
        vehicle_only_costs = float(exp_row.vehicle_only_costs or 0.0)
        total_operating_costs = trip_linked_costs + vehicle_only_costs

        # 2. Query completed trips for realized revenue and authoritative telemetry
        trip_stmt = (
            select(
                func.count(Trip.id).label("completed_count"),
                func.coalesce(func.sum(Trip.revenue), 0.0).label("realized_revenue"),
                func.coalesce(func.sum(case((Trip.actual_distance > 0, Trip.actual_distance), else_=0.0)), 0.0).label("total_distance"),
                func.coalesce(func.sum(case((Trip.actual_fuel_liters > 0, Trip.actual_fuel_liters), else_=0.0)), 0.0).label("total_fuel"),
                func.coalesce(func.sum(case((and_(Trip.actual_distance > 0, Trip.actual_fuel_liters > 0), Trip.actual_distance), else_=0.0)), 0.0).label("paired_distance"),
                func.coalesce(func.sum(case((and_(Trip.actual_distance > 0, Trip.actual_fuel_liters > 0), Trip.actual_fuel_liters), else_=0.0)), 0.0).label("paired_fuel")
            )
            .where(
                Trip.company_id == company_id,
                Trip.vehicle_id == vehicle_id,
                Trip.status == TripStatus.COMPLETED
            )
        )
        if start_date:
            trip_stmt = trip_stmt.where(Trip.actual_end_time >= start_date)
        if end_date:
            trip_stmt = trip_stmt.where(Trip.actual_end_time <= end_date)

        trip_res = await self.db.execute(trip_stmt)
        trip_row = trip_res.one()

        completed_count = int(trip_row.completed_count or 0)
        realized_revenue = float(trip_row.realized_revenue or 0.0)
        total_distance = float(trip_row.total_distance or 0.0)
        total_fuel = float(trip_row.total_fuel or 0.0)
        paired_distance = float(trip_row.paired_distance or 0.0)
        paired_fuel = float(trip_row.paired_fuel or 0.0)

        # 3. Active trips count
        active_stmt = (
            select(func.count(Trip.id))
            .where(
                Trip.company_id == company_id,
                Trip.vehicle_id == vehicle_id,
                Trip.status == TripStatus.IN_PROGRESS
            )
        )
        active_count = int((await self.db.execute(active_stmt)).scalar() or 0)

        # 4. Computed Metrics
        operating_profit = realized_revenue - total_operating_costs
        operating_margin_pct = (
            round((operating_profit / realized_revenue) * 100.0, 2)
            if realized_revenue > 0 else None
        )

        cost_per_km = (
            round(total_operating_costs / total_distance, 2)
            if total_distance > 0 else None
        )
        revenue_per_km = (
            round(realized_revenue / total_distance, 2)
            if total_distance > 0 else None
        )
        fuel_efficiency_kmpl = (
            round(paired_distance / paired_fuel, 2)
            if paired_distance > 0 and paired_fuel > 0 else None
        )

        # Utilization & Activity calculation
        utilization_rate_pct = None
        activity_score = None
        if start_date and end_date and end_date > start_date:
            # Bounded reporting window: compute elapsed-time utilization from trips intersecting the window
            all_in_window_stmt = (
                select(Trip.id, Trip.actual_start_time, Trip.actual_end_time)
                .where(
                    Trip.company_id == company_id,
                    Trip.vehicle_id == vehicle_id,
                    Trip.status == TripStatus.COMPLETED,
                    or_(
                        and_(Trip.actual_start_time <= end_date, Trip.actual_end_time >= start_date),
                        and_(Trip.actual_start_time.is_(None), Trip.actual_end_time >= start_date, Trip.actual_end_time <= end_date),
                        and_(Trip.actual_end_time.is_(None), Trip.actual_start_time >= start_date, Trip.actual_start_time <= end_date)
                    )
                )
            )
            all_trips_res = await self.db.execute(all_in_window_stmt)
            trips_time = all_trips_res.all()

            def _to_utc(dt):
                if dt is None:
                    return None
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)

            w_start = _to_utc(start_date)
            w_end = _to_utc(end_date)
            window_seconds = (w_end - w_start).total_seconds()

            if len(trips_time) == 0:
                # Vehicle was completely idle during this window
                utilization_rate_pct = 0.0
            elif any(s is None or e is None for _, s, e in trips_time):
                # Completed trips exist in the window, but timestamps are unavailable.
                # Do not fabricate utilization when timestamps are unavailable.
                utilization_rate_pct = None
            else:
                total_seconds = 0.0
                for _, s, e in trips_time:
                    s_utc = _to_utc(s)
                    e_utc = _to_utc(e)
                    ts = max(s_utc, w_start)
                    te = min(e_utc, w_end)
                    if te > ts:
                        total_seconds += (te - ts).total_seconds()
                if window_seconds > 0:
                    utilization_rate_pct = round(min(100.0, max(0.0, (total_seconds / window_seconds) * 100.0)), 1)
        else:
            # Unbounded window: do not expose trip-count heuristic as utilization_pct
            utilization_rate_pct = None
            if active_count > 0:
                activity_score = 100.0
            elif completed_count > 0:
                activity_score = min(100.0, completed_count * 10.0)
            else:
                activity_score = 0.0

        return VehicleEconomicsResponse(
            vehicle_id=vehicle.id,
            registration_number=vehicle.registration_number,
            reporting_period_start=start_date,
            reporting_period_end=end_date,
            realized_revenue=round(realized_revenue, 2),
            trip_linked_costs=round(trip_linked_costs, 2),
            vehicle_only_costs=round(vehicle_only_costs, 2),
            total_operating_costs=round(total_operating_costs, 2),
            operating_profit=round(operating_profit, 2),
            operating_margin_pct=operating_margin_pct,
            total_actual_distance_km=round(total_distance, 2) if total_distance > 0 else None,
            total_actual_fuel_liters=round(total_fuel, 2) if total_fuel > 0 else None,
            cost_per_km=cost_per_km,
            revenue_per_km=revenue_per_km,
            fuel_efficiency_kmpl=fuel_efficiency_kmpl,
            completed_trips_count=completed_count,
            active_trips_count=active_count,
            utilization_rate_pct=utilization_rate_pct,
            activity_score=activity_score,
            maintenance_status=vehicle.maintenance_status or "NOT_DUE",
            last_service_date=vehicle.last_service_date,
            last_service_odometer=vehicle.last_service_odometer,
            current_odometer=vehicle.current_odometer
        )

    async def get_fleet_roll_up(
        self,
        company_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_vehicles: bool = True
    ) -> FleetRollUpResponse:
        """
        Roll up fleet financial and operational metrics without N+1 queries.
        Reconciles vehicle totals, company overhead, and fleet profitability.
        """
        # 1. Query all vehicles for this company
        v_stmt = (
            select(Vehicle)
            .where(Vehicle.company_id == company_id)
            .order_by(Vehicle.id.asc())
        )
        vehicles = (await self.db.execute(v_stmt)).scalars().all()
        total_vehicles = len(vehicles)
        active_vehicles = sum(1 for v in vehicles if v.status == VehicleStatus.ACTIVE)

        # 2. Database-side expense aggregation per vehicle (resolving trip-linked vehicle if missing)
        exp_stmt = (
            select(
                func.coalesce(Expense.vehicle_id, Trip.vehicle_id).label("resolved_vehicle_id"),
                func.coalesce(func.sum(case((Expense.trip_id.isnot(None), Expense.amount), else_=0.0)), 0.0).label("trip_linked"),
                func.coalesce(func.sum(case((Expense.trip_id.is_(None), Expense.amount), else_=0.0)), 0.0).label("vehicle_only")
            )
            .outerjoin(Trip, Expense.trip_id == Trip.id)
            .where(
                Expense.company_id == company_id,
                Expense.status == ExpenseStatus.APPROVED,
                or_(Expense.vehicle_id.isnot(None), Expense.trip_id.isnot(None))
            )
            .group_by(func.coalesce(Expense.vehicle_id, Trip.vehicle_id))
        )
        if start_date:
            exp_stmt = exp_stmt.where(Expense.expense_date >= start_date)
        if end_date:
            exp_stmt = exp_stmt.where(Expense.expense_date <= end_date)

        exp_map: Dict[int, Dict[str, float]] = {}
        for row in (await self.db.execute(exp_stmt)).all():
            if row.resolved_vehicle_id is not None:
                exp_map[row.resolved_vehicle_id] = {
                    "trip_linked": float(row.trip_linked or 0.0),
                    "vehicle_only": float(row.vehicle_only or 0.0)
                }

        # 3. Company-only overhead (unattributed to any vehicle or trip)
        oh_stmt = (
            select(func.coalesce(func.sum(Expense.amount), 0.0))
            .where(
                Expense.company_id == company_id,
                Expense.status == ExpenseStatus.APPROVED,
                Expense.vehicle_id.is_(None),
                Expense.trip_id.is_(None)
            )
        )
        if start_date:
            oh_stmt = oh_stmt.where(Expense.expense_date >= start_date)
        if end_date:
            oh_stmt = oh_stmt.where(Expense.expense_date <= end_date)

        company_overhead = float((await self.db.execute(oh_stmt)).scalar() or 0.0)

        # 4. Database-side trip aggregation per vehicle
        trip_stmt = (
            select(
                Trip.vehicle_id,
                func.count(Trip.id).label("completed_count"),
                func.coalesce(func.sum(Trip.revenue), 0.0).label("realized_revenue"),
                func.coalesce(func.sum(case((Trip.actual_distance > 0, Trip.actual_distance), else_=0.0)), 0.0).label("total_distance"),
                func.coalesce(func.sum(case((Trip.actual_fuel_liters > 0, Trip.actual_fuel_liters), else_=0.0)), 0.0).label("total_fuel"),
                func.coalesce(func.sum(case((and_(Trip.actual_distance > 0, Trip.actual_fuel_liters > 0), Trip.actual_distance), else_=0.0)), 0.0).label("paired_distance"),
                func.coalesce(func.sum(case((and_(Trip.actual_distance > 0, Trip.actual_fuel_liters > 0), Trip.actual_fuel_liters), else_=0.0)), 0.0).label("paired_fuel")
            )
            .where(
                Trip.company_id == company_id,
                Trip.status == TripStatus.COMPLETED,
                Trip.vehicle_id.isnot(None)
            )
            .group_by(Trip.vehicle_id)
        )
        if start_date:
            trip_stmt = trip_stmt.where(Trip.actual_end_time >= start_date)
        if end_date:
            trip_stmt = trip_stmt.where(Trip.actual_end_time <= end_date)

        trip_map: Dict[int, Dict[str, float]] = {}
        for row in (await self.db.execute(trip_stmt)).all():
            trip_map[row.vehicle_id] = {
                "completed_count": int(row.completed_count or 0),
                "realized_revenue": float(row.realized_revenue or 0.0),
                "total_distance": float(row.total_distance or 0.0),
                "total_fuel": float(row.total_fuel or 0.0),
                "paired_distance": float(row.paired_distance or 0.0),
                "paired_fuel": float(row.paired_fuel or 0.0),
            }

        # 5. Active trips count per vehicle
        active_stmt = (
            select(Trip.vehicle_id, func.count(Trip.id).label("active_count"))
            .where(
                Trip.company_id == company_id,
                Trip.status == TripStatus.IN_PROGRESS,
                Trip.vehicle_id.isnot(None)
            )
            .group_by(Trip.vehicle_id)
        )
        active_map: Dict[int, int] = {
            row.vehicle_id: int(row.active_count or 0)
            for row in (await self.db.execute(active_stmt)).all()
        }

        # 6. Duration aggregation for bounded utilization
        is_bounded = bool(start_date and end_date and end_date > start_date)
        durations_by_vehicle: Dict[int, float] = {}
        missing_timestamps_vehicles: set[int] = set()
        vehicles_with_trips_in_window: set[int] = set()
        window_seconds = 0.0

        if is_bounded:
            def _to_utc(dt):
                if dt is None:
                    return None
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)

            w_start = _to_utc(start_date)
            w_end = _to_utc(end_date)
            window_seconds = (w_end - w_start).total_seconds()

            dur_stmt = (
                select(Trip.vehicle_id, Trip.actual_start_time, Trip.actual_end_time)
                .where(
                    Trip.company_id == company_id,
                    Trip.status == TripStatus.COMPLETED,
                    Trip.vehicle_id.isnot(None),
                    or_(
                        and_(Trip.actual_start_time <= end_date, Trip.actual_end_time >= start_date),
                        and_(Trip.actual_start_time.is_(None), Trip.actual_end_time >= start_date, Trip.actual_end_time <= end_date),
                        and_(Trip.actual_end_time.is_(None), Trip.actual_start_time >= start_date, Trip.actual_start_time <= end_date)
                    )
                )
            )
            for vid, s, e in (await self.db.execute(dur_stmt)).all():
                vehicles_with_trips_in_window.add(vid)
                if s is None or e is None:
                    missing_timestamps_vehicles.add(vid)
                else:
                    s_utc = _to_utc(s)
                    e_utc = _to_utc(e)
                    ts = max(s_utc, w_start)
                    te = min(e_utc, w_end)
                    if te > ts:
                        durations_by_vehicle[vid] = durations_by_vehicle.get(vid, 0.0) + (te - ts).total_seconds()

        # 7. Assemble vehicle economics
        vehicle_responses: List[VehicleEconomicsResponse] = []
        fleet_realized_revenue = 0.0
        fleet_trip_linked_costs = 0.0
        fleet_vehicle_only_costs = 0.0
        fleet_actual_distance = 0.0
        fleet_actual_fuel = 0.0
        fleet_paired_distance = 0.0
        fleet_paired_fuel = 0.0
        fleet_completed_trips = 0

        for v in vehicles:
            exp_info = exp_map.get(v.id, {"trip_linked": 0.0, "vehicle_only": 0.0})
            trip_info = trip_map.get(v.id, {
                "completed_count": 0, "realized_revenue": 0.0,
                "total_distance": 0.0, "total_fuel": 0.0,
                "paired_distance": 0.0, "paired_fuel": 0.0
            })
            act_count = active_map.get(v.id, 0)

            v_rev = trip_info["realized_revenue"]
            v_trip_cost = exp_info["trip_linked"]
            v_veh_cost = exp_info["vehicle_only"]
            v_total_cost = v_trip_cost + v_veh_cost
            v_profit = v_rev - v_total_cost
            v_margin = round((v_profit / v_rev) * 100.0, 2) if v_rev > 0 else None

            v_dist = trip_info["total_distance"]
            v_fuel = trip_info["total_fuel"]
            v_cost_per_km = round(v_total_cost / v_dist, 2) if v_dist > 0 else None
            v_rev_per_km = round(v_rev / v_dist, 2) if v_dist > 0 else None

            p_dist = trip_info["paired_distance"]
            p_fuel = trip_info["paired_fuel"]
            v_efficiency = round(p_dist / p_fuel, 2) if p_dist > 0 and p_fuel > 0 else None

            # Utilization & Activity
            if is_bounded:
                if v.id in missing_timestamps_vehicles:
                    v_util = None
                elif v.id in vehicles_with_trips_in_window:
                    tot_sec = durations_by_vehicle.get(v.id, 0.0)
                    v_util = round(min(100.0, max(0.0, (tot_sec / window_seconds) * 100.0)), 1) if window_seconds > 0 else None
                else:
                    v_util = 0.0
                v_activity = None
            else:
                v_util = None
                if act_count > 0:
                    v_activity = 100.0
                elif trip_info["completed_count"] > 0:
                    v_activity = min(100.0, trip_info["completed_count"] * 10.0)
                else:
                    v_activity = 0.0

            # Roll into fleet aggregates
            fleet_realized_revenue += v_rev
            fleet_trip_linked_costs += v_trip_cost
            fleet_vehicle_only_costs += v_veh_cost
            fleet_actual_distance += v_dist
            fleet_actual_fuel += v_fuel
            fleet_paired_distance += p_dist
            fleet_paired_fuel += p_fuel
            fleet_completed_trips += trip_info["completed_count"]

            v_resp = VehicleEconomicsResponse(
                vehicle_id=v.id,
                registration_number=v.registration_number,
                reporting_period_start=start_date,
                reporting_period_end=end_date,
                realized_revenue=round(v_rev, 2),
                trip_linked_costs=round(v_trip_cost, 2),
                vehicle_only_costs=round(v_veh_cost, 2),
                total_operating_costs=round(v_total_cost, 2),
                operating_profit=round(v_profit, 2),
                operating_margin_pct=v_margin,
                total_actual_distance_km=round(v_dist, 2) if v_dist > 0 else None,
                total_actual_fuel_liters=round(v_fuel, 2) if v_fuel > 0 else None,
                cost_per_km=v_cost_per_km,
                revenue_per_km=v_rev_per_km,
                fuel_efficiency_kmpl=v_efficiency,
                completed_trips_count=trip_info["completed_count"],
                active_trips_count=act_count,
                utilization_rate_pct=v_util,
                activity_score=v_activity,
                maintenance_status=v.maintenance_status or "NOT_DUE",
                last_service_date=v.last_service_date,
                last_service_odometer=v.last_service_odometer,
                current_odometer=v.current_odometer
            )
            vehicle_responses.append(v_resp)

        # 8. Fleet totals
        total_fleet_costs = fleet_trip_linked_costs + fleet_vehicle_only_costs + company_overhead
        fleet_operating_profit = fleet_realized_revenue - (fleet_trip_linked_costs + fleet_vehicle_only_costs)
        fleet_net_profit = fleet_realized_revenue - total_fleet_costs
        fleet_margin = (
            round((fleet_net_profit / fleet_realized_revenue) * 100.0, 2)
            if fleet_realized_revenue > 0 else None
        )

        fleet_cost_per_km = (
            round(total_fleet_costs / fleet_actual_distance, 2)
            if fleet_actual_distance > 0 else None
        )
        fleet_rev_per_km = (
            round(fleet_realized_revenue / fleet_actual_distance, 2)
            if fleet_actual_distance > 0 else None
        )
        fleet_efficiency = (
            round(fleet_paired_distance / fleet_paired_fuel, 2)
            if fleet_paired_distance > 0 and fleet_paired_fuel > 0 else None
        )

        if total_vehicles == 0:
            fleet_utilization = None
            fleet_activity = None
        elif is_bounded:
            valid_utils = [v.utilization_rate_pct for v in vehicle_responses if v.utilization_rate_pct is not None]
            fleet_utilization = (
                round(sum(valid_utils) / total_vehicles, 1)
                if len(valid_utils) == total_vehicles and total_vehicles > 0
                else (round(sum(valid_utils) / len(valid_utils), 1) if valid_utils else None)
            )
            fleet_activity = None
        else:
            fleet_utilization = None
            fleet_activity = (
                round(sum((v.activity_score or 0.0) for v in vehicle_responses) / total_vehicles, 1)
                if total_vehicles > 0 else None
            )

        return FleetRollUpResponse(
            company_id=company_id,
            reporting_period_start=start_date,
            reporting_period_end=end_date,
            total_vehicles=total_vehicles,
            active_vehicles=active_vehicles,
            fleet_realized_revenue=round(fleet_realized_revenue, 2),
            fleet_trip_linked_costs=round(fleet_trip_linked_costs, 2),
            fleet_vehicle_only_costs=round(fleet_vehicle_only_costs, 2),
            company_overhead_costs=round(company_overhead, 2),
            total_fleet_costs=round(total_fleet_costs, 2),
            fleet_operating_profit=round(fleet_operating_profit, 2),
            fleet_net_profit=round(fleet_net_profit, 2),
            fleet_profit_margin_pct=fleet_margin,
            total_actual_distance_km=round(fleet_actual_distance, 2) if fleet_actual_distance > 0 else None,
            total_actual_fuel_liters=round(fleet_actual_fuel, 2) if fleet_actual_fuel > 0 else None,
            fleet_cost_per_km=fleet_cost_per_km,
            fleet_revenue_per_km=fleet_rev_per_km,
            fleet_fuel_efficiency_kmpl=fleet_efficiency,
            total_completed_trips=fleet_completed_trips,
            fleet_utilization_rate_pct=fleet_utilization,
            fleet_activity_score=fleet_activity,
            vehicles=vehicle_responses if include_vehicles else []
        )
