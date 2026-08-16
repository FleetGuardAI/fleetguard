"""
Fleet Intelligence Engine - Evidence Builder
"""

from typing import List
from infrastructure.intelligence.evidence.models import (
    BaseEvidence, ReceiptEvidence, GPSEvidence, FuelSensorEvidence, VehicleEvidence, Reliability
)
from infrastructure.intelligence.evidence.package import EvidencePackage
from infrastructure.intelligence.event_processing.models import (
    BaseOperationalEvent, FuelReceiptEvent, GPSEvent, FuelSensorEvent, VehicleSnapshotEvent
)


class EvidenceBuilder:
    """
    Transforms correlated raw operational events into immutable Evidence objects.
    
    CRITICAL RESPONSIBILITY LIMITS:
    - This builder ONLY performs object mapping and transformation.
    - It NEVER validates data.
    - It NEVER checks for duplicates.
    - It NEVER applies business logic or makes intelligence decisions.
    
    Those responsibilities belong exclusively to the Validation Engine 
    and the Intelligence layers (Checks/Assessments/Risk/Decision).
    """

    def build_package(self, events: List[BaseOperationalEvent]) -> EvidencePackage:
        """
        Converts a correlated list of raw events into a strict EvidencePackage.
        """
        evidence_list: List[BaseEvidence] = []
        
        for event in events:
            # Map raw event_id directly to evidence_id to guarantee provenance
            # Map original timestamp to collected_at
            
            if isinstance(event, FuelReceiptEvent):
                meta = {}
                if event.station_lat is not None:
                    meta["station_lat"] = event.station_lat
                if event.station_lon is not None:
                    meta["station_lon"] = event.station_lon
                if event.station_name is not None:
                    meta["station_name"] = event.station_name
                    
                evidence_list.append(ReceiptEvidence(
                    evidence_id=event.event_id,
                    source="event_processing",
                    origin="external_api",
                    reliability=Reliability.MEDIUM, # Default mapping
                    collected_at=event.timestamp,
                    amount=event.amount,
                    quantity=event.quantity,
                    metadata=meta
                ))
                
            elif isinstance(event, GPSEvent):
                evidence_list.append(GPSEvidence(
                    evidence_id=event.event_id,
                    source="event_processing",
                    origin="telematics",
                    reliability=Reliability.HIGH,
                    collected_at=event.timestamp,
                    latitude=event.latitude,
                    longitude=event.longitude,
                    accuracy=event.accuracy
                ))
                
            elif isinstance(event, FuelSensorEvent):
                evidence_list.append(FuelSensorEvidence(
                    evidence_id=event.event_id,
                    source="event_processing",
                    origin="can_bus",
                    reliability=Reliability.HIGH,
                    collected_at=event.timestamp,
                    fuel_before=event.fuel_before,
                    fuel_after=event.fuel_after,
                    sensor_type="analog"
                ))
                
            elif isinstance(event, VehicleSnapshotEvent):
                evidence_list.append(VehicleEvidence(
                    evidence_id=event.event_id,
                    source="event_processing",
                    origin="master_data",
                    reliability=Reliability.VERIFIED,
                    collected_at=event.timestamp,
                    vehicle_id=event.vehicle_id,
                    tank_capacity=event.tank_capacity
                ))
                
        return EvidencePackage(evidence_list)
