"""
FleetGuard — Driver Vehicle Intelligence Engine
Phase 4 Deterministic Signal Calculation and Anomaly Lifecycle.
"""

import math
from typing import Optional, List, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from models.location_tracking import VehicleCurrentLocation, LocationSource, LocationAlert, AlertType
from models.intelligence_condition import IntelligenceCondition, ConditionType, ConditionStatus
from models.vehicle_domain import Vehicle
from models.driver_domain import Driver
from models.trip_domain import Trip, TripStatus
from schemas.location_intelligence import (
    DriverVehicleSignals, FreshnessState, ProximityState, 
    MovementState, DivergenceState, LocationStateInfo
)
from services.driver_vehicle_intelligence_config import intelligence_config


class DriverVehicleIntelligenceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ---------------------------------------------------------
    # 1. Signal Calculation Utilities (Step 6)
    # ---------------------------------------------------------
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Returns distance in meters between two GPS coordinates."""
        R = 6371000  # radius of Earth in meters
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0) ** 2 + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda / 2.0) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    # ---------------------------------------------------------
    # 2. Freshness / Data-Quality (Step 7)
    # ---------------------------------------------------------
    def _evaluate_freshness(self, state: VehicleCurrentLocation, now: datetime) -> LocationStateInfo:
        event_age = (now - state.last_timestamp).total_seconds()
        ingestion_age = (now - state.last_received_at).total_seconds()

        if event_age < 0 or ingestion_age < 0:
            # Future timestamps
            freshness = FreshnessState.UNKNOWN
        else:
            is_phone = (state.source == LocationSource.PHONE_GPS.value)
            stale_event_thresh = (
                intelligence_config.PHONE_GPS_EVENT_STALE_AFTER_SECONDS if is_phone
                else intelligence_config.HARDWARE_GPS_EVENT_STALE_AFTER_SECONDS
            )
            stale_ingest_thresh = (
                intelligence_config.PHONE_GPS_INGESTION_STALE_AFTER_SECONDS if is_phone
                else intelligence_config.HARDWARE_GPS_INGESTION_STALE_AFTER_SECONDS
            )

            # If both are very fresh
            if event_age <= stale_event_thresh and ingestion_age <= stale_ingest_thresh:
                freshness = FreshnessState.FRESH
            # If it hasn't communicated in a very long time
            elif ingestion_age > (stale_ingest_thresh * 3):
                freshness = FreshnessState.OFFLINE
            # If event is stale but ingestion is fresh, or vice-versa
            elif event_age > stale_event_thresh:
                freshness = FreshnessState.STALE
            else:
                freshness = FreshnessState.AGING

        return LocationStateInfo(
            timestamp=state.last_timestamp,
            received_at=state.last_received_at,
            latitude=state.latitude,
            longitude=state.longitude,
            speed=state.speed,
            heading=state.heading,
            accuracy=state.accuracy,
            event_age_seconds=event_age,
            ingestion_age_seconds=ingestion_age,
            freshness=freshness
        )

    # ---------------------------------------------------------
    # 3. Core Signal Computations (Steps 8-11)
    # ---------------------------------------------------------
    def _evaluate_proximity(self, dist: float, effective_uncert: float) -> ProximityState:
        if dist <= (intelligence_config.DRIVER_VEHICLE_PROXIMITY_METERS + effective_uncert):
            return ProximityState.WITH_VEHICLE
        elif dist <= (intelligence_config.DRIVER_VEHICLE_POSSIBLE_PROXIMITY_METERS + effective_uncert):
            return ProximityState.POSSIBLY_WITH_VEHICLE
        else:
            return ProximityState.AWAY_FROM_VEHICLE

    def _evaluate_movement(self, phone: LocationStateInfo, hw: LocationStateInfo) -> MovementState:
        p_speed = phone.speed if phone.speed is not None else 0.0
        h_speed = hw.speed if hw.speed is not None else 0.0
        
        # Assume speeds are provided in m/s, convert to km/h for thresholds
        p_kmh = p_speed * 3.6
        h_kmh = h_speed * 3.6

        v_moving = h_kmh >= intelligence_config.VEHICLE_MOVING_SPEED_THRESHOLD_KMH
        p_moving = p_kmh >= intelligence_config.VEHICLE_MOVING_SPEED_THRESHOLD_KMH
        v_stat = h_kmh <= intelligence_config.DRIVER_STATIONARY_SPEED_THRESHOLD_KMH
        p_stat = p_kmh <= intelligence_config.DRIVER_STATIONARY_SPEED_THRESHOLD_KMH

        if v_moving and p_moving:
            # We don't have complex heading math here yet, just assume they are moving together if both moving
            # You can expand heading comparison logic later.
            return MovementState.MOVING_TOGETHER
        elif v_stat and p_stat:
            return MovementState.BOTH_STATIONARY
        elif v_moving and p_stat:
            return MovementState.VEHICLE_MOVING_DRIVER_STATIONARY
        elif p_moving and v_stat:
            return MovementState.DRIVER_MOVING_VEHICLE_STATIONARY
        
        return MovementState.UNKNOWN

    def _evaluate_divergence(self, dist: float, is_compatible: bool, phone: LocationStateInfo, hw: LocationStateInfo) -> DivergenceState:
        if phone.freshness in [FreshnessState.STALE, FreshnessState.OFFLINE] or hw.freshness in [FreshnessState.STALE, FreshnessState.OFFLINE]:
            return DivergenceState.STALE_SOURCE
        
        if not is_compatible:
            return DivergenceState.UNKNOWN
            
        if dist > intelligence_config.SIGNIFICANT_SOURCE_DIVERGENCE_METERS:
            return DivergenceState.SIGNIFICANT_DIVERGENCE
        elif dist > (intelligence_config.DRIVER_VEHICLE_PROXIMITY_METERS * 2):
            return DivergenceState.MINOR_DIVERGENCE
        
        return DivergenceState.ALIGNED

    # ---------------------------------------------------------
    # 4. Context & Full Evaluation (Steps 12-13)
    # ---------------------------------------------------------
    async def compute_signals(self, vehicle_id: int, company_id: int, now: Optional[datetime] = None) -> DriverVehicleSignals:
        now = now or datetime.now(timezone.utc)
        
        # 1. Fetch Vehicle and its assignments
        vehicle = await self.db.get(Vehicle, vehicle_id)
        if not vehicle or vehicle.company_id != company_id:
            raise ValueError("Vehicle not found or unauthorized")
            
        driver = await self.db.get(Driver, vehicle.assigned_driver_id) if vehicle.assigned_driver_id else None
        
        # Fetch active trip if any
        trip = None
        if driver:
            t_query = select(Trip).where(
                and_(Trip.driver_id == driver.id, Trip.status == TripStatus.IN_PROGRESS)
            )
            t_res = await self.db.execute(t_query)
            trip = t_res.scalars().first()

        # 2. Fetch Locations
        loc_query = select(VehicleCurrentLocation).where(
            VehicleCurrentLocation.vehicle_id == vehicle_id
        )
        loc_res = await self.db.execute(loc_query)
        locs = loc_res.scalars().all()
        
        p_state_raw = next((l for l in locs if l.source == LocationSource.PHONE_GPS.value), None)
        h_state_raw = next((l for l in locs if l.source == LocationSource.HARDWARE_GPS.value), None)
        
        p_info = self._evaluate_freshness(p_state_raw, now) if p_state_raw else None
        h_info = self._evaluate_freshness(h_state_raw, now) if h_state_raw else None

        # 3. Deltas & Proximity Check
        time_delta = None
        dist = None
        is_compatible = False
        eff_uncert = None
        prox_state = ProximityState.UNKNOWN
        mov_state = MovementState.UNKNOWN
        div_state = DivergenceState.UNKNOWN

        if p_info and h_info:
            time_delta = abs((p_info.timestamp - h_info.timestamp).total_seconds())
            is_compatible = time_delta <= intelligence_config.MAX_LOCATION_COMPARISON_TIMESTAMP_DELTA_SECONDS
            
            if is_compatible:
                dist = self._haversine_distance(p_info.latitude, p_info.longitude, h_info.latitude, h_info.longitude)
                eff_uncert = (p_info.accuracy or 10.0) + (h_info.accuracy or 10.0)
                
                prox_state = self._evaluate_proximity(dist, eff_uncert)
                mov_state = self._evaluate_movement(p_info, h_info)
                div_state = self._evaluate_divergence(dist, is_compatible, p_info, h_info)

        return DriverVehicleSignals(
            company_id=company_id,
            vehicle_id=vehicle_id,
            driver_id=driver.id if driver else None,
            trip_id=trip.id if trip else None,
            phone_state=p_info,
            hardware_state=h_info,
            time_delta_seconds=time_delta,
            is_temporally_compatible=is_compatible,
            distance_meters=dist,
            effective_uncertainty_meters=eff_uncert,
            proximity_state=prox_state,
            movement_state=mov_state,
            divergence_state=div_state,
            driver_duty_status=driver.employment_status.value if driver and driver.employment_status else None,
            vehicle_status=vehicle.status.value,
            trip_status=trip.status.value if trip else None,
        )

    # ---------------------------------------------------------
    # 5. Condition Lifecycle & Persistence (Steps 14-15)
    # ---------------------------------------------------------
    def _map_condition_to_alert_type(self, ctype: ConditionType) -> AlertType:
        if ctype == ConditionType.POTENTIAL_DRIVER_VEHICLE_SEPARATION:
            return AlertType.DRIVER_VEHICLE_SEPARATION
        if ctype == ConditionType.VEHICLE_MOVING_DRIVER_STATIONARY:
            return AlertType.VEHICLE_MOVING_DRIVER_STATIONARY
        return AlertType.GPS_SOURCE_DIVERGENCE

    async def process_conditions(self, signals: DriverVehicleSignals, now: datetime):
        # 1. Determine current active condition triggers based on signals
        active_triggers = set()
        
        if signals.trip_id and signals.proximity_state == ProximityState.AWAY_FROM_VEHICLE:
            active_triggers.add(ConditionType.POTENTIAL_DRIVER_VEHICLE_SEPARATION)
            
        if signals.movement_state == MovementState.VEHICLE_MOVING_DRIVER_STATIONARY:
            active_triggers.add(ConditionType.VEHICLE_MOVING_DRIVER_STATIONARY)
            
        if signals.divergence_state == DivergenceState.SIGNIFICANT_DIVERGENCE:
            active_triggers.add(ConditionType.GPS_SOURCE_DIVERGENCE)
            
        # 2. Fetch existing active conditions for this vehicle
        cond_query = select(IntelligenceCondition).where(
            and_(
                IntelligenceCondition.vehicle_id == signals.vehicle_id,
                IntelligenceCondition.status == ConditionStatus.ACTIVE
            )
        )
        cond_res = await self.db.execute(cond_query)
        existing_conditions = {c.condition_type: c for c in cond_res.scalars().all()}
        
        # 3. Process triggers
        for ctype in ConditionType:
            is_triggered = ctype in active_triggers
            condition = existing_conditions.get(ctype)
            
            if is_triggered:
                if not condition:
                    # New condition
                    condition = IntelligenceCondition(
                        company_id=signals.company_id,
                        vehicle_id=signals.vehicle_id,
                        driver_id=signals.driver_id,
                        trip_id=signals.trip_id,
                        condition_type=ctype,
                        status=ConditionStatus.ACTIVE,
                        first_seen_at=now,
                        last_evaluated_at=now,
                        last_event_at=now,
                        last_evidence=signals.to_evidence_dict()
                    )
                    self.db.add(condition)
                else:
                    # Update existing condition
                    condition.last_evaluated_at = now
                    condition.last_event_at = now
                    condition.last_evidence = signals.to_evidence_dict()
                    
                    # Check duration
                    duration = (now - condition.first_seen_at).total_seconds()
                    if duration >= intelligence_config.MINIMUM_ANOMALY_DURATION_SECONDS and not condition.alert_id:
                        # Spawn persistent LocationAlert
                        # Note: LocationAlert schema requires driver_id.
                        driver_id = signals.driver_id or 1 # Fallback if missing
                        alert = LocationAlert(
                            driver_id=driver_id,
                            company_id=signals.company_id,
                            alert_type=self._map_condition_to_alert_type(ctype),
                            details=signals.to_evidence_dict(),
                            latitude=signals.phone_state.latitude if signals.phone_state else None,
                            longitude=signals.phone_state.longitude if signals.phone_state else None,
                            is_resolved=False
                        )
                        self.db.add(alert)
                        await self.db.flush()
                        condition.alert_id = alert.id
            else:
                if condition:
                    # Condition disappeared
                    condition.status = ConditionStatus.RESOLVED
                    condition.resolved_at = now
                    
                    if condition.alert_id:
                        alert = await self.db.get(LocationAlert, condition.alert_id)
                        if alert:
                            alert.is_resolved = True
