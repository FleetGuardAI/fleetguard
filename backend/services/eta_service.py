from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from models.trip_domain import Trip, TripStatus
from models.vehicle_domain import Vehicle
from services.routing_service import RoutingService
from services.location_service import LocationService
from database import AsyncSessionLocal
import logging

logger = logging.getLogger(__name__)

class EtaService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.routing_service = RoutingService()

    async def calculate_eta_for_trip(self, trip: Trip) -> Optional[datetime]:
        """
        Calculates the real-time ETA for an IN_PROGRESS trip using Google Maps Routes API
        and the vehicle's last known location.
        """
        if trip.status != TripStatus.IN_PROGRESS:
            return None
            
        if not trip.vehicle_id or not trip.destination_lat or not trip.destination_lng:
            return None
            
        # Get vehicle's last location
        vehicle = await self.db.get(Vehicle, trip.vehicle_id)
        if not vehicle or not vehicle.last_location_lat or not vehicle.last_location_lng:
            return None
            
        try:
            # Query the routing provider (Google Maps) for the remaining route duration
            route_estimate = await self.routing_service.estimate_route(
                origin="Current Location",
                destination="Destination",
                origin_lat=vehicle.last_location_lat,
                origin_lng=vehicle.last_location_lng,
                destination_lat=trip.destination_lat,
                destination_lng=trip.destination_lng
            )
            
            if route_estimate.duration_hours:
                return datetime.utcnow() + timedelta(hours=route_estimate.duration_hours)
                
        except Exception as e:
            logger.error(f"Failed to calculate real-time ETA for trip {trip.id}: {e}")
            
        return None
        
    async def enrich_trip_response(self, trip: Trip) -> dict:
        """
        Returns a dict that can be used to update a TripResponse dict.
        """
        eta = await self.calculate_eta_for_trip(trip)
        return {"estimated_arrival_time": eta}
