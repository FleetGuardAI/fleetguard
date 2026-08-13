"""
FleetGuard — Fleet Intelligence Application Service

Connects the infrastructure Intelligence Engine to the API layer.
Delegates all pipeline orchestration to the IntelligenceFactory;
uses existing repositories for data access.
"""

import logging
from typing import List

from infrastructure.uow import AbstractUnitOfWork
from models.operational_event import EntityType
from models.vehicle_domain import VehicleStatus

from infrastructure.intelligence.factory import IntelligenceFactory
from infrastructure.intelligence.fleet_health.analyzer import FleetHealthAnalyzer
from infrastructure.intelligence.fleet_health.models import VehicleIntelligenceContext
from infrastructure.intelligence.event_processing.builder import EvidenceBuilder
from infrastructure.intelligence.event_processing.models import (
    FuelReceiptEvent, GPSEvent, FuelSensorEvent, VehicleSnapshotEvent
)
from schemas.fleet_intelligence import (
    FleetHealthResponse, FleetFindingSchema, FleetDomainStatisticsSchema,
    DomainRiskCountsSchema, FleetInsightSchema
)

logger = logging.getLogger("fleetguard.services.fleet_intelligence")


class FleetIntelligenceService:
    """
    Application-layer coordinator for Fleet Intelligence.

    Uses IntelligenceFactory to obtain a fully configured orchestrator
    (never manually reconstructs the pipeline) and uses existing
    repositories through the UnitOfWork for all data access.
    """

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow
        self._orchestrator = IntelligenceFactory.build_orchestrator()
        self._builder = EvidenceBuilder()

    async def get_fleet_health(self) -> FleetHealthResponse:
        """
        Dynamically executes the intelligence engine against existing
        operational events for all active vehicles to produce a real-time
        fleet health report.
        """
        # 1. Fetch active vehicles via the existing repository
        vehicles = await self.uow.repositories.vehicle.search_vehicles(
            is_active=True, limit=200, offset=0
        )

        vehicle_contexts: List[VehicleIntelligenceContext] = []

        for vehicle in vehicles:
            # 2. Fetch recent operational events for each vehicle via existing repository
            db_events = await self.uow.repositories.operational_event.list_events_by_entity(
                entity_type=EntityType.VEHICLE,
                entity_id=vehicle.registration_number,
                limit=100,
                offset=0,
            )

            # 3. Transform DB events → intelligence pydantic events for the builder
            pydantic_events = []

            # Inject a baseline vehicle snapshot so the engine knows about the vehicle
            pydantic_events.append(VehicleSnapshotEvent(
                correlation_id=str(vehicle.id),
                vehicle_id=vehicle.registration_number,
                tank_capacity=vehicle.tank_capacity or 400.0,
            ))

            for ev in db_events:
                payload = ev.payload or {}
                base_kwargs = {
                    "event_id": ev.id,
                    "correlation_id": str(vehicle.id),
                    "timestamp": ev.occurred_at,
                }

                try:
                    if ev.event_type.value == "FUEL_FILLED":
                        pydantic_events.append(FuelReceiptEvent(
                            **base_kwargs,
                            quantity=payload.get("quantity", 0.0),
                            amount=payload.get("amount", 0.0),
                            station_name=payload.get("station_name"),
                            station_lat=payload.get("latitude"),
                            station_lon=payload.get("longitude"),
                        ))
                    elif ev.event_type.value == "POSITION_RECORDED":
                        pydantic_events.append(GPSEvent(
                            **base_kwargs,
                            latitude=payload.get("latitude", 0.0),
                            longitude=payload.get("longitude", 0.0),
                            accuracy=payload.get("accuracy", 10.0),
                        ))
                    elif ev.event_type.value == "FUEL_DRAINED":
                        pydantic_events.append(FuelSensorEvent(
                            **base_kwargs,
                            fuel_before=payload.get("fuel_before", 0.0),
                            fuel_after=payload.get("fuel_after", 0.0),
                        ))
                except Exception:
                    # Skip events that can't be mapped due to missing/malformed payload fields
                    logger.debug(
                        "Skipping event %s for vehicle %s — mapping error",
                        ev.id, vehicle.registration_number,
                    )

            # 4. Build EvidencePackage and execute orchestrator
            package = self._builder.build_package(pydantic_events)
            result = self._orchestrator.execute(package)

            # 5. Extract DomainRiskProfiles from the execution trace
            profiles = result.trace.domain_risk_profiles if result.trace else []

            vehicle_contexts.append(VehicleIntelligenceContext(
                vehicle_id=vehicle.registration_number,
                profiles=profiles,
            ))

        # 6. Aggregate into fleet-level health report
        analyzer = FleetHealthAnalyzer(fleet_id="current_fleet")
        report = analyzer.execute(
            vehicle_contexts=vehicle_contexts,
            fleet_insights=[],
        )

        # 7. Map to API response schema
        return FleetHealthResponse(
            fleet_id=report.fleet_id,
            generated_at=report.generated_at,
            fleet_health_status=report.fleet_health_status.value,
            vehicle_count=report.vehicle_count,
            operational_vehicle_count=report.operational_vehicle_count,
            critical_vehicle_count=report.critical_vehicle_count,
            fleet_summary=report.fleet_summary,
            fleet_findings=[
                FleetFindingSchema(
                    finding_key=f.finding_key,
                    severity=f.severity.value,
                    summary=f.summary,
                    metadata=f.metadata,
                )
                for f in report.fleet_findings
            ],
            domain_statistics=FleetDomainStatisticsSchema(
                fuel=DomainRiskCountsSchema(**report.domain_statistics.fuel.model_dump()),
                driver=DomainRiskCountsSchema(**report.domain_statistics.driver.model_dump()),
                maintenance=DomainRiskCountsSchema(**report.domain_statistics.maintenance.model_dump()),
                tyre=DomainRiskCountsSchema(**report.domain_statistics.tyre.model_dump()),
                route=DomainRiskCountsSchema(**report.domain_statistics.route.model_dump()),
                compliance=DomainRiskCountsSchema(**report.domain_statistics.compliance.model_dump()),
            ),
            fleet_insights=[
                FleetInsightSchema(
                    insight_key=i.insight_key,
                    insight_type=i.insight_type.value,
                    insight_strength=i.insight_strength.value,
                    summary=i.summary,
                )
                for i in report.fleet_insights
            ],
        )
