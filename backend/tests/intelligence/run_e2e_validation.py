import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./e2e_test.db"

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

import models # Ensures Base.metadata contains all tables
from database import Base, engine, async_session_factory
from infrastructure.uow import SqlAlchemyUnitOfWork
from infrastructure.intelligence.fuel_domain.orchestrator import FuelIntelligenceOrchestrator
from infrastructure.intelligence.fuel_domain.consumer import FuelIntelligenceConsumer

from models.company import Company
from models.vehicle_domain import Vehicle
from models.trip_domain import Trip, TripStatus
from models.operational_event import EventType, EntityType, CaptureMethod
from schemas.operational_event import OperationalEventCreate, OperationalEventResponse
from services.operational_event_service import OperationalEventService

from infrastructure.intelligence.fuel_domain.financial.summary_service import FleetFinancialIntelligenceService

logging.basicConfig(level=logging.WARNING) # Suppress noisy logs
logger = logging.getLogger("validation")

async def reset_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

async def simulate_pipeline(uow: SqlAlchemyUnitOfWork, event_create: OperationalEventCreate, consumer: FuelIntelligenceConsumer):
    service = OperationalEventService(uow)
    # 1. Operational Event -> Operations Engine -> Outbox
    response = await service.create_event(event_create)
    await uow.commit() # Commit so outbox event is persisted and visible to consumer if it checks db, but it doesn't need to.
    
    # 2. Extract Payload from Outbox (Simulation)
    # In reality, outbox worker reads it and publishes to Kafka. We bypass Kafka and invoke Consumer directly.
    # The consumer will open its OWN uow.
    await consumer.handle(response)

async def run_scenarios():
    await reset_db()
    
    orchestrator = FuelIntelligenceOrchestrator()
    consumer = FuelIntelligenceConsumer(orchestrator)
    fleet_service = FleetFinancialIntelligenceService()

    # Setup base entities
    uow = SqlAlchemyUnitOfWork(async_session_factory)
    async with uow:
        company = Company(id=1, company_name="Test Fleet", owner_name="Admin", mobile_number="1234567890")
        uow.session.add(company)
        
        # Scenario A & B & C Truck
        v1 = Vehicle(id=1, company_id=1, registration_number="TRK-A", make="Volvo", model="FH16", year=2024)
        uow.session.add(v1)
        
        # Scenario E (Late Arrival) Truck
        v2 = Vehicle(id=2, company_id=1, registration_number="TRK-E", make="Volvo", model="FH16", year=2024)
        uow.session.add(v2)
        
        # Scenario G (No Baseline) Truck
        v3 = Vehicle(id=3, company_id=1, registration_number="TRK-G", make="Volvo", model="FH16", year=2024)
        uow.session.add(v3)
        
        # Scenario H (No Price) Truck
        v4 = Vehicle(id=4, company_id=1, registration_number="TRK-H", make="Volvo", model="FH16", year=2024)
        uow.session.add(v4)
        
        # Scenario I (Evidence) Truck
        v5 = Vehicle(id=5, company_id=1, registration_number="TRK-I", make="Volvo", model="FH16", year=2024)
        uow.session.add(v5)

        await uow.commit()

    print("===========================================")
    print("SCENARIO A - HEALTHY TRUCK")
    print("===========================================")
    # 5 full observations to establish a baseline of 3.0 km/L. 1000km / 333.33L = 3.0
    for i in range(5):
        uow = SqlAlchemyUnitOfWork(async_session_factory)
        async with uow:
            start_time = datetime(2026, 7, 1 + i, 10, 0, tzinfo=timezone.utc)
            end_time = datetime(2026, 7, 1 + i, 18, 0, tzinfo=timezone.utc)
            
            trip = Trip(trip_id=f"TRIP-A{i}", status=TripStatus.COMPLETED, vehicle_id=1, company_id=1, actual_start_time=start_time, actual_end_time=end_time, actual_distance=1000.0)
            uow.session.add(trip)
            await uow.commit()
            
        uow = SqlAlchemyUnitOfWork(async_session_factory)
        async with uow:
            await simulate_pipeline(uow, OperationalEventCreate(
                event_type=EventType.FUEL_FILLED, entity_type=EntityType.VEHICLE, entity_id="TRK-A", occurred_at=start_time, capture_method=CaptureMethod.MANUAL_ENTRY, payload={"liters": 0.0, "odometer_km": i*1000}
            ), consumer)
            await simulate_pipeline(uow, OperationalEventCreate(
                event_type=EventType.FUEL_FILLED, entity_type=EntityType.VEHICLE, entity_id="TRK-A", occurred_at=end_time, capture_method=CaptureMethod.MANUAL_ENTRY, payload={"liters": 333.33, "cost_inr": 333.33*90, "odometer_km": (i+1)*1000}
            ), consumer)
            await simulate_pipeline(uow, OperationalEventCreate(
                event_type=EventType.TRIP_COMPLETED, entity_type=EntityType.TRIP, entity_id=f"TRIP-A{i}", occurred_at=end_time, capture_method=CaptureMethod.SYSTEM_GENERATED
            ), consumer)
    
    # Assert Scenario A
    uow = SqlAlchemyUnitOfWork(async_session_factory)
    async with uow:
        baseline = await uow.repositories.entity_baseline.get_baseline("TRK-A", "TRUCK", "FUEL_EFFICIENCY", datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc), datetime(2026, 7, 5, 18, 0, tzinfo=timezone.utc))
        print(f"Scenario A Baseline: {baseline.baseline_value if baseline else 'None'}")
            
    print("===========================================")
    print("SCENARIO B & C - GRADUAL DEGRADATION & FINANCIAL IMPACT")
    print("===========================================")
    # 6th observation is degraded. 1000km / 400L = 2.5 km/L. Price = 90.
    uow = SqlAlchemyUnitOfWork(async_session_factory)
    async with uow:
        start_time = datetime(2026, 7, 6, 10, 0, tzinfo=timezone.utc)
        end_time = datetime(2026, 7, 6, 18, 0, tzinfo=timezone.utc)
        trip = Trip(trip_id=f"TRIP-A5", status=TripStatus.COMPLETED, vehicle_id=1, company_id=1, actual_start_time=start_time, actual_end_time=end_time, actual_distance=1000.0)
        uow.session.add(trip)
        await uow.commit()

    uow = SqlAlchemyUnitOfWork(async_session_factory)
    async with uow:
        await simulate_pipeline(uow, OperationalEventCreate(event_type=EventType.FUEL_FILLED, entity_type=EntityType.VEHICLE, entity_id="TRK-A", occurred_at=start_time, capture_method=CaptureMethod.MANUAL_ENTRY, payload={"liters": 0.0, "odometer_km": 5000}), consumer)
        await simulate_pipeline(uow, OperationalEventCreate(event_type=EventType.FUEL_FILLED, entity_type=EntityType.VEHICLE, entity_id="TRK-A", occurred_at=end_time, capture_method=CaptureMethod.MANUAL_ENTRY, payload={"liters": 400.0, "cost_inr": 400.0*90, "odometer_km": 6000}), consumer)
        await simulate_pipeline(uow, OperationalEventCreate(event_type=EventType.TRIP_COMPLETED, entity_type=EntityType.TRIP, entity_id=f"TRIP-A5", occurred_at=end_time, capture_method=CaptureMethod.SYSTEM_GENERATED), consumer)

    uow = SqlAlchemyUnitOfWork(async_session_factory)
    async with uow:
        # Check Anomaly
        res = await uow.session.execute(models.fuel_anomaly.FuelAnomaly.__table__.select())
        anomalies = res.fetchall()
        print(f"Anomalies found: {len(anomalies)}")
        if anomalies:
            print(f"Anomaly: {anomalies[0].severity} / {anomalies[0].deviation_percent}% / Observed: {anomalies[0].observed_value}")
        
        # Check Impact
        res = await uow.session.execute(models.fuel_financial_impact.FuelFinancialImpact.__table__.select())
        impacts = res.fetchall()
        print(f"Impacts found: {len(impacts)}")
        if impacts:
            print(f"Impact: Excess Liters: {impacts[0].excess_fuel_liters} / Financial Exposure: {impacts[0].estimated_financial_exposure}")

    print("===========================================")
    print("SCENARIO E - LATE FUEL_FILLED")
    print("===========================================")
    # TRK-E. 5 valid trips to establish baseline.
    for i in range(5):
        uow = SqlAlchemyUnitOfWork(async_session_factory)
        async with uow:
            start_time = datetime(2026, 7, 1 + i, 10, 0, tzinfo=timezone.utc)
            end_time = datetime(2026, 7, 1 + i, 18, 0, tzinfo=timezone.utc)
            trip = Trip(trip_id=f"TRIP-E{i}", status=TripStatus.COMPLETED, vehicle_id=2, company_id=1, actual_start_time=start_time, actual_end_time=end_time, actual_distance=1000.0)
            uow.session.add(trip)
            await uow.commit()
            
        uow = SqlAlchemyUnitOfWork(async_session_factory)
        async with uow:
            await simulate_pipeline(uow, OperationalEventCreate(event_type=EventType.FUEL_FILLED, entity_type=EntityType.VEHICLE, entity_id="TRK-E", occurred_at=start_time, capture_method=CaptureMethod.MANUAL_ENTRY, payload={"liters": 0.0, "odometer_km": i*1000}), consumer)
            await simulate_pipeline(uow, OperationalEventCreate(event_type=EventType.FUEL_FILLED, entity_type=EntityType.VEHICLE, entity_id="TRK-E", occurred_at=end_time, capture_method=CaptureMethod.MANUAL_ENTRY, payload={"liters": 333.33, "cost_inr": 333.33*90, "odometer_km": (i+1)*1000}), consumer)
            await simulate_pipeline(uow, OperationalEventCreate(event_type=EventType.TRIP_COMPLETED, entity_type=EntityType.TRIP, entity_id=f"TRIP-E{i}", occurred_at=end_time, capture_method=CaptureMethod.SYSTEM_GENERATED), consumer)

    # Late Arrival scenario
    uow = SqlAlchemyUnitOfWork(async_session_factory)
    async with uow:
        start_time = datetime(2026, 7, 6, 10, 0, tzinfo=timezone.utc)
        end_time = datetime(2026, 7, 6, 18, 0, tzinfo=timezone.utc)
        trip = Trip(trip_id=f"TRIP-E5", status=TripStatus.COMPLETED, vehicle_id=2, company_id=1, actual_start_time=start_time, actual_end_time=end_time, actual_distance=1000.0)
        uow.session.add(trip)
        await uow.commit()
        
    # Process TRIP_COMPLETED first
    uow = SqlAlchemyUnitOfWork(async_session_factory)
    async with uow:
        # FUEL_FILLED A (Start boundary)
        await simulate_pipeline(uow, OperationalEventCreate(event_type=EventType.FUEL_FILLED, entity_type=EntityType.VEHICLE, entity_id="TRK-E", occurred_at=start_time, capture_method=CaptureMethod.MANUAL_ENTRY, payload={"liters": 0.0, "odometer_km": 5000}), consumer)
        # TRIP_COMPLETED
        await simulate_pipeline(uow, OperationalEventCreate(event_type=EventType.TRIP_COMPLETED, entity_type=EntityType.TRIP, entity_id=f"TRIP-E5", occurred_at=end_time, capture_method=CaptureMethod.SYSTEM_GENERATED), consumer)
        
        # Wait, no metric should exist yet
        metrics = await uow.session.execute(models.derived_fuel_metrics.DerivedFuelMetric.__table__.select().where(models.derived_fuel_metrics.DerivedFuelMetric.entity_id == 'TRK-E'))
        print(f"Metrics before late arrival: {len(metrics.fetchall())}")

        # Late FUEL_FILLED B (End boundary)
        await simulate_pipeline(uow, OperationalEventCreate(event_type=EventType.FUEL_FILLED, entity_type=EntityType.VEHICLE, entity_id="TRK-E", occurred_at=end_time - timedelta(minutes=1), capture_method=CaptureMethod.MANUAL_ENTRY, payload={"liters": 333.33, "cost_inr": 333.33*90, "odometer_km": 6000}), consumer)
        
        metrics = await uow.session.execute(models.derived_fuel_metrics.DerivedFuelMetric.__table__.select().where(models.derived_fuel_metrics.DerivedFuelMetric.entity_id == 'TRK-E'))
        print(f"Metrics after late arrival: {len(metrics.fetchall())}")
    
    print("===========================================")
    print("SCENARIO F - DUPLICATE EVENT IDEMPOTENCY")
    print("===========================================")
    # Re-send exactly the same TRIP_COMPLETED for TRK-A5
    uow = SqlAlchemyUnitOfWork(async_session_factory)
    async with uow:
        end_time = datetime(2026, 7, 6, 18, 0, tzinfo=timezone.utc)
        # Find the existing TRK-A5 outbox payload or recreate identical
        # Since the Orchestrator checks source_reference, we just simulate the exact same payload.
        event_id = "duplicate-simulation"
        await simulate_pipeline(uow, OperationalEventCreate(event_type=EventType.TRIP_COMPLETED, entity_type=EntityType.TRIP, entity_id=f"TRIP-A5", occurred_at=end_time, capture_method=CaptureMethod.SYSTEM_GENERATED), consumer)
        
        anomalies = await uow.session.execute(models.fuel_anomaly.FuelAnomaly.__table__.select())
        print(f"Anomalies after duplicate execution: {len(anomalies.fetchall())}") # Should still be 1 (TRK-A had 1)
        
    print("===========================================")
    print("SCENARIO G - INSUFFICIENT DATA (NO BASELINE)")
    print("===========================================")
    # TRK-G. Only 2 trips (less than 5 needed for baseline)
    for i in range(2):
        uow = SqlAlchemyUnitOfWork(async_session_factory)
        async with uow:
            start_time = datetime(2026, 7, 1 + i, 10, 0, tzinfo=timezone.utc)
            end_time = datetime(2026, 7, 1 + i, 18, 0, tzinfo=timezone.utc)
            trip = Trip(trip_id=f"TRIP-G{i}", status=TripStatus.COMPLETED, vehicle_id=3, company_id=1, actual_start_time=start_time, actual_end_time=end_time, actual_distance=1000.0)
            uow.session.add(trip)
            await uow.commit()
            
        uow = SqlAlchemyUnitOfWork(async_session_factory)
        async with uow:
            await simulate_pipeline(uow, OperationalEventCreate(event_type=EventType.FUEL_FILLED, entity_type=EntityType.VEHICLE, entity_id="TRK-G", occurred_at=start_time, capture_method=CaptureMethod.MANUAL_ENTRY, payload={"liters": 0.0, "odometer_km": i*1000}), consumer)
            await simulate_pipeline(uow, OperationalEventCreate(event_type=EventType.FUEL_FILLED, entity_type=EntityType.VEHICLE, entity_id="TRK-G", occurred_at=end_time, capture_method=CaptureMethod.MANUAL_ENTRY, payload={"liters": 333.33, "cost_inr": 333.33*90, "odometer_km": (i+1)*1000}), consumer)
            await simulate_pipeline(uow, OperationalEventCreate(event_type=EventType.TRIP_COMPLETED, entity_type=EntityType.TRIP, entity_id=f"TRIP-G{i}", occurred_at=end_time, capture_method=CaptureMethod.SYSTEM_GENERATED), consumer)

    uow = SqlAlchemyUnitOfWork(async_session_factory)
    async with uow:
        anomalies = await uow.session.execute(models.fuel_anomaly.FuelAnomaly.__table__.select().where(models.fuel_anomaly.FuelAnomaly.entity_id == 'TRK-G'))
        print(f"Anomalies for TRK-G: {len(anomalies.fetchall())}")

    print("===========================================")
    print("SCENARIO J - FLEET SUMMARY API")
    print("===========================================")
    uow = SqlAlchemyUnitOfWork(async_session_factory)
    async with uow:
        start = datetime(2026, 7, 1, tzinfo=timezone.utc)
        end = datetime(2026, 7, 10, tzinfo=timezone.utc)
        summary = await fleet_service.get_fleet_summary(uow, 1, start, end)
        print(f"Total Trucks: {summary.total_trucks}")
        print(f"Affected Trucks: {summary.affected_trucks}")
        print(f"Sufficient Intelligence: {summary.trucks_with_sufficient_intelligence}")
        print(f"Insufficient Intelligence: {summary.trucks_with_insufficient_data}")
        print(f"Total Exposure: {summary.total_estimated_exposure}")
        print(f"Top Exposures: {len(summary.top_exposures)}")
        if summary.top_exposures:
            print(f"Top Truck: {summary.top_exposures[0].truck_id} / Exposure: {summary.top_exposures[0].estimated_exposure}")

if __name__ == "__main__":
    asyncio.run(run_scenarios())
