"""
FleetGuard — Route Versioning and Persistence Service
Manages immutable route versions, approvals, recalculations, and route history.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy import select, func, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.route_domain import RouteVersion, RouteVersionStatus, RouteType
from models.trip_domain import Trip, TripStatus
from models.user import User

logger = logging.getLogger("fleetguard.routing.version_service")


class RouteVersionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def persist_route_version(
        self,
        trip_id: int,
        company_id: int,
        route_option_data: Dict[str, Any],
        status: RouteVersionStatus = RouteVersionStatus.APPROVED,
        approved_by_user_id: Optional[int] = None,
        reason_for_change: Optional[str] = None,
        selection_reason: Optional[str] = None
    ) -> RouteVersion:
        """
        Creates and persists a new route version for a trip.
        If approved/active, supersedes prior versions and updates the parent Trip record.
        """
        trip = await self.db.get(Trip, trip_id)
        if not trip or trip.company_id != company_id:
            raise ValueError(f"Trip #{trip_id} not found in company #{company_id}")

        # Compute next version number
        version_stmt = select(func.coalesce(func.max(RouteVersion.version_number), 0)).where(
            RouteVersion.trip_id == trip_id
        )
        version_res = await self.db.execute(version_stmt)
        next_version = version_res.scalar_one() + 1

        # If this new version is APPROVED or ACTIVE, supersede prior active versions
        if status in [RouteVersionStatus.APPROVED, RouteVersionStatus.ACTIVE]:
            await self.db.execute(
                update(RouteVersion)
                .where(
                    RouteVersion.trip_id == trip_id,
                    RouteVersion.status.in_([RouteVersionStatus.APPROVED, RouteVersionStatus.ACTIVE])
                )
                .values(status=RouteVersionStatus.SUPERSEDED)
            )

        cost_est = route_option_data.get("cost_estimate")
        fuel_liters = getattr(cost_est, "fuel_liters", None) if cost_est else route_option_data.get("fuel_liters_estimate")
        fuel_cost = getattr(cost_est, "fuel_cost", None) if cost_est else route_option_data.get("fuel_cost_estimate")
        toll_cost = getattr(cost_est, "toll_estimate", None) if cost_est else route_option_data.get("toll_cost_estimate")
        total_cost = getattr(cost_est, "direct_travel_cost", None) if cost_est else route_option_data.get("total_cost_estimate")
        currency = getattr(cost_est, "currency", "INR") if cost_est else route_option_data.get("currency", "INR")
        mileage_used = getattr(cost_est, "vehicle_mileage_km_per_liter", None) if cost_est else route_option_data.get("vehicle_mileage_used")
        fuel_price_used = getattr(cost_est, "fuel_price_per_liter", None) if cost_est else route_option_data.get("fuel_price_used")

        route_type_val = route_option_data.get("category", RouteType.RECOMMENDED.value)
        if hasattr(route_type_val, "value"):
            route_type_val = route_type_val.value
        try:
            route_type_enum = RouteType(route_type_val)
        except ValueError:
            route_type_enum = RouteType.RECOMMENDED

        new_version = RouteVersion(
            trip_id=trip_id,
            company_id=company_id,
            version_number=next_version,
            route_type=route_type_enum,
            status=status,
            origin_lat=trip.origin_lat or route_option_data.get("origin_lat", 0.0),
            origin_lng=trip.origin_lng or route_option_data.get("origin_lng", 0.0),
            origin_address=trip.origin_address or trip.origin_location,
            destination_lat=trip.destination_lat or route_option_data.get("destination_lat", 0.0),
            destination_lng=trip.destination_lng or route_option_data.get("destination_lng", 0.0),
            destination_address=trip.destination_address or trip.destination_location,
            polyline=route_option_data.get("polyline", ""),
            distance_km=route_option_data.get("distance_km", 0.0),
            duration_hours=route_option_data.get("duration_hours", 0.0),
            duration_seconds=route_option_data.get("duration_seconds", int(route_option_data.get("duration_hours", 0.0) * 3600)),
            fuel_liters_estimate=fuel_liters,
            fuel_cost_estimate=fuel_cost,
            toll_cost_estimate=toll_cost,
            total_cost_estimate=total_cost,
            currency=currency,
            vehicle_mileage_used=mileage_used,
            fuel_price_used=fuel_price_used,
            routing_provider=route_option_data.get("provider", trip.route_provider or "google"),
            selection_reason=selection_reason or route_option_data.get("selection_reason"),
            reason_for_change=reason_for_change,
            approved_by_user_id=approved_by_user_id,
            approved_at=datetime.now(timezone.utc) if status in [RouteVersionStatus.APPROVED, RouteVersionStatus.ACTIVE] else None
        )

        self.db.add(new_version)
        await self.db.flush()  # assign new_version.id

        if status in [RouteVersionStatus.APPROVED, RouteVersionStatus.ACTIVE]:
            trip.approved_route_version_id = new_version.id
            trip.route_distance_km = new_version.distance_km
            trip.route_duration_hours = new_version.duration_hours
            trip.route_toll_estimate = new_version.toll_cost_estimate
            trip.route_provider = new_version.routing_provider
            trip.route_polyline = new_version.polyline
            trip.route_status = "APPROVED"

        await self.db.commit()
        await self.db.refresh(new_version)
        logger.info(f"Trip #{trip_id}: Persisted RouteVersion #{new_version.version_number} (ID: {new_version.id}, Status: {status.value})")
        return new_version

    async def get_active_route_version(self, trip_id: int, company_id: int) -> Optional[RouteVersion]:
        """Returns the currently approved/active route version for a trip."""
        stmt = (
            select(RouteVersion)
            .where(
                RouteVersion.trip_id == trip_id,
                RouteVersion.company_id == company_id,
                RouteVersion.status.in_([RouteVersionStatus.APPROVED, RouteVersionStatus.ACTIVE])
            )
            .order_by(RouteVersion.version_number.desc())
            .limit(1)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_route_versions_for_trip(self, trip_id: int, company_id: int) -> List[RouteVersion]:
        """Returns complete historical route versions for auditing."""
        stmt = (
            select(RouteVersion)
            .where(RouteVersion.trip_id == trip_id, RouteVersion.company_id == company_id)
            .order_by(RouteVersion.version_number.asc())
        )
        res = await self.db.execute(stmt)
        return res.scalars().all()
