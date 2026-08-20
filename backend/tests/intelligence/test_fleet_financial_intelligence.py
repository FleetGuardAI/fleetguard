import pytest
from datetime import datetime, timezone

from models.vehicle_domain import Vehicle
from models.fuel_financial_impact import FuelFinancialImpact
from models.fuel_anomaly import FuelAnomaly, AnomalySeverity, AnomalyStatus
from models.fuel_root_cause import FuelRootCauseAnalysis, FuelRootCauseEvidence, RootCauseType, EvidenceStrength
from infrastructure.intelligence.fuel_domain.financial.summary_service import FleetFinancialIntelligenceService

class MockDB:
    def __init__(self, vehicles):
        self.vehicles = vehicles
    async def execute(self, stmt):
        class Result:
            def __init__(self, data):
                self.data = data
            def scalars(self):
                return self
            def all(self):
                return self.data
        return Result(self.vehicles)

class MockImpactRepo:
    def __init__(self, impacts):
        self.impacts = impacts
    async def get_impacts_for_entities(self, ids, start, end):
        return [i for i in self.impacts if i.entity_id in ids and i.period_start >= start and i.period_end <= end]

class MockAnomalyRepo:
    def __init__(self, anomalies):
        self.anomalies = anomalies
    async def get_anomalies_for_entities(self, ids, start, end):
        return [a for a in self.anomalies if a.entity_id in ids and a.period_start >= start and a.period_end <= end]

class MockRootCauseRepo:
    def __init__(self, analyses):
        self.analyses = analyses
    async def get_analyses_by_references(self, refs):
        return [a for a in self.analyses if a.anomaly_reference in refs]

class MockUOW:
    def __init__(self, vehicles=[], impacts=[], anomalies=[], analyses=[]):
        self.session = MockDB(vehicles)
        self.repositories = type('Repositories', (), {
            'fuel_financial_impact': MockImpactRepo(impacts),
            'fuel_anomaly': MockAnomalyRepo(anomalies),
            'fuel_root_cause': MockRootCauseRepo(analyses)
        })()

@pytest.fixture
def service():
    return FleetFinancialIntelligenceService()

@pytest.mark.asyncio
async def test_empty_fleet(service):
    uow = MockUOW(vehicles=[])
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    end = datetime(2026, 8, 10, tzinfo=timezone.utc)
    
    summary = await service.get_fleet_summary(uow, 1, start, end)
    
    assert summary.total_trucks == 0
    assert summary.affected_trucks == 0
    assert summary.total_estimated_exposure == 0.0

@pytest.mark.asyncio
async def test_fleet_entity_mapping(service):
    # Fleet 1 has TRK-1 and TRK-2. Fleet 2 has TRK-3.
    v1 = Vehicle(company_id=1, registration_number="TRK-1")
    v2 = Vehicle(company_id=1, registration_number="TRK-2")
    
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    end = datetime(2026, 8, 10, tzinfo=timezone.utc)
    
    i1 = FuelFinancialImpact(entity_id="TRK-1", period_start=start, period_end=end, estimated_financial_exposure=100.0, excess_fuel_liters=10.0, anomaly_reference="a1")
    i2 = FuelFinancialImpact(entity_id="TRK-3", period_start=start, period_end=end, estimated_financial_exposure=200.0, excess_fuel_liters=20.0, anomaly_reference="a3")
    
    a1 = FuelAnomaly(entity_id="TRK-1", period_start=start, period_end=end, status=AnomalyStatus.ANOMALY, observation_reference="a1", severity=AnomalySeverity.WARNING, deviation_percent=-10.0)
    
    uow = MockUOW(vehicles=[v1, v2], impacts=[i1, i2], anomalies=[a1])
    
    summary = await service.get_fleet_summary(uow, 1, start, end)
    
    # TRK-3 impact should be isolated/ignored because it's not in the fleet's vehicle list
    assert summary.total_trucks == 2
    assert summary.affected_trucks == 1
    assert summary.total_estimated_exposure == 100.0
    assert summary.top_exposures[0].truck_id == "TRK-1"

@pytest.mark.asyncio
async def test_overlap_rejection(service):
    v1 = Vehicle(company_id=1, registration_number="TRK-1")
    
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    end = datetime(2026, 8, 10, tzinfo=timezone.utc)
    
    # Overlapping intervals: August 1-5 and August 3-7
    i1 = FuelFinancialImpact(entity_id="TRK-1", period_start=datetime(2026, 8, 1, tzinfo=timezone.utc), period_end=datetime(2026, 8, 5, tzinfo=timezone.utc), estimated_financial_exposure=100.0, excess_fuel_liters=10.0, anomaly_reference="a1")
    i2 = FuelFinancialImpact(entity_id="TRK-1", period_start=datetime(2026, 8, 3, tzinfo=timezone.utc), period_end=datetime(2026, 8, 7, tzinfo=timezone.utc), estimated_financial_exposure=200.0, excess_fuel_liters=20.0, anomaly_reference="a2")
    
    uow = MockUOW(vehicles=[v1], impacts=[i1, i2])
    
    summary = await service.get_fleet_summary(uow, 1, start, end)
    
    assert summary.affected_trucks == 0
    assert summary.total_estimated_exposure == 0.0
    assert len(summary.top_exposures) == 1
    assert summary.top_exposures[0].data_conflict is True
    assert summary.top_exposures[0].estimated_exposure == 0.0

@pytest.mark.asyncio
async def test_touching_intervals_allowed(service):
    v1 = Vehicle(company_id=1, registration_number="TRK-1")
    
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    end = datetime(2026, 8, 10, tzinfo=timezone.utc)
    
    # Touching boundaries are allowed
    i1 = FuelFinancialImpact(entity_id="TRK-1", period_start=datetime(2026, 8, 1, tzinfo=timezone.utc), period_end=datetime(2026, 8, 5, tzinfo=timezone.utc), estimated_financial_exposure=100.0, excess_fuel_liters=10.0, anomaly_reference="a1")
    i2 = FuelFinancialImpact(entity_id="TRK-1", period_start=datetime(2026, 8, 5, tzinfo=timezone.utc), period_end=datetime(2026, 8, 7, tzinfo=timezone.utc), estimated_financial_exposure=200.0, excess_fuel_liters=20.0, anomaly_reference="a2")
    
    uow = MockUOW(vehicles=[v1], impacts=[i1, i2])
    
    summary = await service.get_fleet_summary(uow, 1, start, end)
    
    assert summary.affected_trucks == 1
    assert summary.total_estimated_exposure == 300.0
    assert summary.top_exposures[0].data_conflict is False

@pytest.mark.asyncio
async def test_truck_severity_and_deviation(service):
    v1 = Vehicle(company_id=1, registration_number="TRK-1")
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    end = datetime(2026, 8, 10, tzinfo=timezone.utc)
    
    i1 = FuelFinancialImpact(entity_id="TRK-1", period_start=datetime(2026, 8, 1, tzinfo=timezone.utc), period_end=datetime(2026, 8, 3, tzinfo=timezone.utc), estimated_financial_exposure=100.0, anomaly_reference="a1")
    i2 = FuelFinancialImpact(entity_id="TRK-1", period_start=datetime(2026, 8, 4, tzinfo=timezone.utc), period_end=datetime(2026, 8, 5, tzinfo=timezone.utc), estimated_financial_exposure=50.0, anomaly_reference="a2")
    
    a1 = FuelAnomaly(entity_id="TRK-1", period_start=datetime(2026, 8, 1, tzinfo=timezone.utc), period_end=datetime(2026, 8, 3, tzinfo=timezone.utc), observation_reference="a1", severity=AnomalySeverity.WARNING, deviation_percent=-10.0, status=AnomalyStatus.ANOMALY)
    a2 = FuelAnomaly(entity_id="TRK-1", period_start=datetime(2026, 8, 4, tzinfo=timezone.utc), period_end=datetime(2026, 8, 5, tzinfo=timezone.utc), observation_reference="a2", severity=AnomalySeverity.CRITICAL, deviation_percent=-20.0, status=AnomalyStatus.ANOMALY)
    
    uow = MockUOW(vehicles=[v1], impacts=[i1, i2], anomalies=[a1, a2])
    
    summary = await service.get_fleet_summary(uow, 1, start, end)
    
    t1 = summary.top_exposures[0]
    assert t1.severity == AnomalySeverity.CRITICAL
    assert t1.worst_deviation_percent == -20.0

@pytest.mark.asyncio
async def test_fleet_coverage_definitions(service):
    v1 = Vehicle(company_id=1, registration_number="TRK-1") # Affected
    v2 = Vehicle(company_id=1, registration_number="TRK-2") # Insufficient
    v3 = Vehicle(company_id=1, registration_number="TRK-3") # Sufficient but normal (not affected)
    
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    end = datetime(2026, 8, 10, tzinfo=timezone.utc)
    
    i1 = FuelFinancialImpact(entity_id="TRK-1", period_start=start, period_end=end, estimated_financial_exposure=100.0, anomaly_reference="a1")
    
    a1 = FuelAnomaly(entity_id="TRK-1", period_start=start, period_end=end, observation_reference="a1", severity=AnomalySeverity.WARNING, status=AnomalyStatus.ANOMALY)
    a2 = FuelAnomaly(entity_id="TRK-2", period_start=start, period_end=end, observation_reference="a2", status=AnomalyStatus.INSUFFICIENT_DATA)
    a3 = FuelAnomaly(entity_id="TRK-3", period_start=start, period_end=end, observation_reference="a3", status=AnomalyStatus.NORMAL)
    
    uow = MockUOW(vehicles=[v1, v2, v3], impacts=[i1], anomalies=[a1, a2, a3])
    
    summary = await service.get_fleet_summary(uow, 1, start, end)
    
    assert summary.total_trucks == 3
    assert summary.trucks_with_sufficient_intelligence == 2 # TRK-1, TRK-3
    assert summary.trucks_with_insufficient_data == 1 # TRK-2
    assert summary.affected_trucks == 1 # TRK-1
    assert summary.trucks_without_anomaly == 1 # TRK-3

@pytest.mark.asyncio
async def test_contributing_factor_aggregation(service):
    v1 = Vehicle(company_id=1, registration_number="TRK-1")
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    end = datetime(2026, 8, 10, tzinfo=timezone.utc)
    
    i1 = FuelFinancialImpact(entity_id="TRK-1", period_start=start, period_end=end, estimated_financial_exposure=500.0, anomaly_reference="a1")
    a1 = FuelAnomaly(entity_id="TRK-1", period_start=start, period_end=end, observation_reference="a1", status=AnomalyStatus.ANOMALY)
    
    ev1 = FuelRootCauseEvidence(cause_type=RootCauseType.EXCESS_DISTANCE, evidence_strength=EvidenceStrength.STRONG_SUPPORT, rank=1)
    rc1 = FuelRootCauseAnalysis(anomaly_reference="a1")
    rc1.evidence_items = [ev1]
    
    uow = MockUOW(vehicles=[v1], impacts=[i1], anomalies=[a1], analyses=[rc1])
    
    summary = await service.get_fleet_summary(uow, 1, start, end)
    
    factor = summary.contributing_factor_summary[0]
    assert factor.cause_type == RootCauseType.EXCESS_DISTANCE
    assert factor.affected_truck_count == 1
    assert factor.total_estimated_exposure == 500.0
    assert factor.highest_observed_strength == EvidenceStrength.STRONG_SUPPORT
    assert factor.strength_counts[EvidenceStrength.STRONG_SUPPORT] == 1
