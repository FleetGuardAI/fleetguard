import pytest
import uuid
from datetime import datetime, timezone, timedelta

from models.fuel_anomaly import FuelAnomaly
from models.fuel_financial_impact import FuelFinancialImpact
from models.derived_fuel_metrics import EntityTypeEnum
from models.operational_event import OperationalEvent, EventType, EntityType
from models.location_tracking import LocationAlert, AlertType
from models.maintenance_domain import MaintenanceRecord, MaintenanceStatus, MaintenanceCategory
from models.trip_domain import Trip
from models.vehicle_domain import Vehicle
from models.fuel_root_cause import RootCauseType, EvidenceStatus, EvidenceStrength

from infrastructure.intelligence.fuel_domain.root_cause.engine import FuelRootCauseEngine

class MockFuelRootCauseRepository:
    def __init__(self):
        self.analyses = []

    async def upsert_analysis(self, analysis):
        self.analyses.append(analysis)
        return analysis

class MockOperationalEventRepository:
    def __init__(self):
        self.events = []
    async def list_events_by_entity(self, entity_type, entity_id, limit=500):
        return self.events

class MockDB:
    def __init__(self):
        self.vehicles = []
        self.trips = []
        self.alerts = []
        self.maintenance = []
        
    async def execute(self, stmt):
        class Result:
            def __init__(self, data):
                self.data = data
            def scalars(self):
                return self
            def all(self):
                return self.data
            def scalar_one_or_none(self):
                return self.data[0] if self.data else None
                
        # Super simple naive matching for tests
        stmt_str = str(stmt)
        if "vehicles" in stmt_str:
            return Result(self.vehicles)
        elif "trips" in stmt_str:
            return Result(self.trips)
        elif "location_alerts" in stmt_str:
            return Result(self.alerts)
        elif "maintenance_records" in stmt_str:
            return Result(self.maintenance)
        return Result([])

class MockUOW:
    def __init__(self):
        self.db = MockDB()
        self.repositories = type('Repositories', (), {
            'fuel_root_cause': MockFuelRootCauseRepository(),
            'operational_event': MockOperationalEventRepository()
        })()


@pytest.fixture
def engine():
    return FuelRootCauseEngine()

def get_anomaly():
    return FuelAnomaly(
        entity_id="TRK-1",
        entity_type=EntityTypeEnum.TRUCK,
        observation_reference="obs-1",
        period_start=datetime(2026, 8, 1, tzinfo=timezone.utc),
        period_end=datetime(2026, 8, 10, tzinfo=timezone.utc)
    )

@pytest.mark.asyncio
async def test_no_evidence_returns_unknown(engine):
    uow = MockUOW()
    anomaly = get_anomaly()
    
    result = await engine.analyze_root_cause(uow, anomaly)
    
    assert result.status == "SUCCESS"
    assert result.candidate_causes[0].cause_type == RootCauseType.UNKNOWN
    assert result.candidate_causes[0].evidence_strength == EvidenceStrength.NO_EVIDENCE

@pytest.mark.asyncio
async def test_fuel_drain_verified_theft(engine):
    uow = MockUOW()
    anomaly = get_anomaly()
    
    uow.repositories.operational_event.events = [
        OperationalEvent(
            id=uuid.uuid4(),
            event_type=EventType.FUEL_DRAINED,
            occurred_at=datetime(2026, 8, 5, tzinfo=timezone.utc),
            payload={"liters": 50, "verified_unauthorized": True}
        )
    ]
    
    result = await engine.analyze_root_cause(uow, anomaly)
    
    # Highest ranked should be FUEL_EVENT_ANOMALY
    top_cause = result.candidate_causes[0]
    assert top_cause.cause_type == RootCauseType.FUEL_EVENT_ANOMALY
    assert top_cause.evidence_strength == EvidenceStrength.STRONG_SUPPORT
    assert top_cause.evidence_value == 50.0

@pytest.mark.asyncio
async def test_fuel_drain_unverified(engine):
    uow = MockUOW()
    anomaly = get_anomaly()
    
    uow.repositories.operational_event.events = [
        OperationalEvent(
            id=uuid.uuid4(),
            event_type=EventType.FUEL_DRAINED,
            occurred_at=datetime(2026, 8, 5, tzinfo=timezone.utc),
            payload={"liters": 25}
        )
    ]
    
    result = await engine.analyze_root_cause(uow, anomaly)
    
    top_cause = result.candidate_causes[0]
    assert top_cause.cause_type == RootCauseType.FUEL_EVENT_ANOMALY
    assert top_cause.evidence_strength == EvidenceStrength.MODERATE_SUPPORT
    assert top_cause.evidence_value == 25.0

@pytest.mark.asyncio
async def test_high_speed_evidence(engine):
    uow = MockUOW()
    anomaly = get_anomaly()
    
    v = Vehicle(id=1, registration_number="TRK-1", make="Tata")
    t = Trip(vehicle_id=1, driver_id=5, actual_start_time=datetime(2026, 8, 2, tzinfo=timezone.utc), actual_end_time=datetime(2026, 8, 3, tzinfo=timezone.utc))
    a1 = LocationAlert(id=1, driver_id=5, alert_type=AlertType.SPEED_VIOLATION, created_at=datetime(2026, 8, 2, 12, tzinfo=timezone.utc))
    a2 = LocationAlert(id=2, driver_id=5, alert_type=AlertType.SPEED_VIOLATION, created_at=datetime(2026, 8, 2, 13, tzinfo=timezone.utc))
    a3 = LocationAlert(id=3, driver_id=5, alert_type=AlertType.SPEED_VIOLATION, created_at=datetime(2026, 8, 2, 14, tzinfo=timezone.utc))
    
    uow.db.vehicles = [v]
    uow.db.trips = [t]
    uow.db.alerts = [a1, a2, a3]
    
    result = await engine.analyze_root_cause(uow, anomaly)
    
    speed_cause = next(c for c in result.candidate_causes if c.cause_type == RootCauseType.HIGH_SPEED)
    assert speed_cause.evidence_status == EvidenceStatus.SUPPORTING
    assert speed_cause.evidence_strength == EvidenceStrength.MODERATE_SUPPORT
    assert speed_cause.evidence_value == 3.0

@pytest.mark.asyncio
async def test_excess_distance_evidence(engine):
    uow = MockUOW()
    anomaly = get_anomaly()
    
    v = Vehicle(id=1, registration_number="TRK-1", make="Tata")
    t = Trip(trip_id="T1", vehicle_id=1, planned_distance=100.0, actual_distance=120.0, actual_start_time=datetime(2026, 8, 2, tzinfo=timezone.utc), actual_end_time=datetime(2026, 8, 3, tzinfo=timezone.utc))
    
    uow.db.vehicles = [v]
    uow.db.trips = [t]
    
    result = await engine.analyze_root_cause(uow, anomaly)
    
    dist_cause = next(c for c in result.candidate_causes if c.cause_type == RootCauseType.EXCESS_DISTANCE)
    assert dist_cause.evidence_status == EvidenceStatus.SUPPORTING
    assert dist_cause.evidence_strength == EvidenceStrength.MODERATE_SUPPORT
    assert dist_cause.evidence_value == 20.0
    assert dist_cause.deviation_percent == 20.0

@pytest.mark.asyncio
async def test_maintenance_evidence(engine):
    uow = MockUOW()
    anomaly = get_anomaly()
    
    v = Vehicle(id=1, registration_number="TRK-1", make="Tata")
    m = MaintenanceRecord(business_id="M1", vehicle_id=1, status=MaintenanceStatus.SCHEDULED, scheduled_date=datetime(2026, 8, 1, tzinfo=timezone.utc))
    
    uow.db.vehicles = [v]
    uow.db.maintenance = [m]
    
    result = await engine.analyze_root_cause(uow, anomaly)
    
    maint_cause = next(c for c in result.candidate_causes if c.cause_type == RootCauseType.VEHICLE_MAINTENANCE)
    assert maint_cause.evidence_status == EvidenceStatus.SUPPORTING
    assert maint_cause.evidence_strength == EvidenceStrength.WEAK_SUPPORT
    assert maint_cause.evidence_value == 1.0

@pytest.mark.asyncio
async def test_ranking(engine):
    uow = MockUOW()
    anomaly = get_anomaly()
    
    v = Vehicle(id=1, registration_number="TRK-1", make="Tata")
    
    # 1. Maintenance (Weak)
    m = MaintenanceRecord(business_id="M1", vehicle_id=1, status=MaintenanceStatus.SCHEDULED, scheduled_date=datetime(2026, 8, 1, tzinfo=timezone.utc))
    uow.db.maintenance = [m]
    
    # 2. Fuel Drain (Moderate, Unverified)
    uow.repositories.operational_event.events = [
        OperationalEvent(
            id=uuid.uuid4(),
            event_type=EventType.FUEL_DRAINED,
            occurred_at=datetime(2026, 8, 5, tzinfo=timezone.utc),
            payload={"liters": 25}
        )
    ]
    
    # 3. Speed (Weak, 1 alert)
    t = Trip(vehicle_id=1, driver_id=5, actual_start_time=datetime(2026, 8, 2, tzinfo=timezone.utc), actual_end_time=datetime(2026, 8, 3, tzinfo=timezone.utc))
    a1 = LocationAlert(id=1, driver_id=5, alert_type=AlertType.SPEED_VIOLATION, created_at=datetime(2026, 8, 2, 12, tzinfo=timezone.utc))
    uow.db.vehicles = [v]
    uow.db.trips = [t]
    uow.db.alerts = [a1]
    
    result = await engine.analyze_root_cause(uow, anomaly)
    
    # Ranks should be: 1. Fuel Drain (Moderate) 2. Speed (Weak) 3. Maintenance (Weak)
    assert result.candidate_causes[0].cause_type == RootCauseType.FUEL_EVENT_ANOMALY
    assert result.candidate_causes[1].cause_type in [RootCauseType.HIGH_SPEED, RootCauseType.VEHICLE_MAINTENANCE]
