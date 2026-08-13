"""
Fleet Intelligence Engine - Factory
Provides an application-level adapter to construct the full Intelligence Pipeline.
"""

from infrastructure.intelligence.checks.registry import CheckRegistry
from infrastructure.intelligence.checks.executor import CheckExecutor

from infrastructure.intelligence.assessments.registry import AssessmentRegistry
from infrastructure.intelligence.assessments.executor import AssessmentExecutor

from infrastructure.intelligence.domain_risk.registry import DomainRiskRegistry
from infrastructure.intelligence.domain_risk.executor import DomainRiskExecutor

from infrastructure.intelligence.global_decision.registry import DecisionRegistry
from infrastructure.intelligence.global_decision.executor import DecisionExecutor

from infrastructure.intelligence.orchestrator.base import IntelligenceOrchestrator

# Import domains (Tyre)
from infrastructure.intelligence.tyre_domain.checks.pressure import TyrePressureCheck
from infrastructure.intelligence.tyre_domain.checks.tread_depth import TyreTreadDepthCheck
from infrastructure.intelligence.tyre_domain.checks.age import TyreAgeCheck
from infrastructure.intelligence.tyre_domain.checks.wear_pattern import TyreWearPatternCheck
from infrastructure.intelligence.tyre_domain.checks.damage import TyreDamageCheck
from infrastructure.intelligence.tyre_domain.assessments.health import TyreHealthAssessment
from infrastructure.intelligence.tyre_domain.risk.health_risk import TyreHealthRiskEngine
from infrastructure.intelligence.tyre_domain.decision.health_decision import TyreHealthDecisionEngine

# Import domains (Route)
from infrastructure.intelligence.route_domain.checks.deviation import RouteDeviationCheck
from infrastructure.intelligence.route_domain.checks.trip_delay import TripDelayCheck
from infrastructure.intelligence.route_domain.checks.unauthorized_stop import UnauthorizedStopCheck
from infrastructure.intelligence.route_domain.checks.geofence_violation import GeofenceViolationCheck
from infrastructure.intelligence.route_domain.checks.excessive_detour import ExcessiveDetourCheck
from infrastructure.intelligence.route_domain.assessments.trip_compliance import TripComplianceAssessment
from infrastructure.intelligence.route_domain.risk.compliance_risk import TripComplianceRiskEngine
from infrastructure.intelligence.route_domain.decision.compliance_decision import TripComplianceDecisionEngine

# Import domains (Maintenance)
from infrastructure.intelligence.maintenance_domain.checks.service_overdue import MaintenanceServiceOverdueCheck
from infrastructure.intelligence.maintenance_domain.checks.distance_overdue import MaintenanceDistanceOverdueCheck
from infrastructure.intelligence.maintenance_domain.checks.time_overdue import MaintenanceTimeOverdueCheck
from infrastructure.intelligence.maintenance_domain.checks.repeated_failures import RepeatedFailureCheck
from infrastructure.intelligence.maintenance_domain.checks.critical_component_due import CriticalComponentDueCheck
from infrastructure.intelligence.maintenance_domain.assessments.vehicle_health import VehicleHealthAssessment
from infrastructure.intelligence.maintenance_domain.risk.vehicle_health_risk import VehicleHealthRiskEngine
from infrastructure.intelligence.maintenance_domain.decision.vehicle_health_decision import VehicleHealthDecisionEngine

# Import domains (Fuel)
from infrastructure.intelligence.fuel_domain.checks.quantity import FuelQuantityCheck
from infrastructure.intelligence.fuel_domain.checks.location import FuelLocationCheck
from infrastructure.intelligence.fuel_domain.checks.timing import FuelTimingCheck
from infrastructure.intelligence.fuel_domain.checks.tank_capacity import FuelTankCapacityCheck
from infrastructure.intelligence.fuel_domain.assessments.transaction_integrity import FuelTransactionIntegrityAssessment
from infrastructure.intelligence.fuel_domain.risk.transaction_risk import FuelTransactionRiskEngine
from infrastructure.intelligence.fuel_domain.decision.transaction_decision import FuelDecisionEngine

# Import domains (Driver)
from infrastructure.intelligence.driver_domain.checks.overspeed import DriverOverspeedCheck
from infrastructure.intelligence.driver_domain.checks.harsh_acceleration import HarshAccelerationCheck
from infrastructure.intelligence.driver_domain.checks.harsh_braking import HarshBrakingCheck
from infrastructure.intelligence.driver_domain.checks.excessive_idling import ExcessiveIdlingCheck
from infrastructure.intelligence.driver_domain.checks.route_compliance import RouteComplianceCheck
from infrastructure.intelligence.driver_domain.assessments.driver_behaviour import DriverBehaviourAssessment
from infrastructure.intelligence.driver_domain.risk.driver_risk import DriverBehaviourRiskEngine
from infrastructure.intelligence.driver_domain.decision.driver_decision import DriverBehaviourDecisionEngine

# Import domains (Compliance)
from infrastructure.intelligence.compliance_domain.checks.registration import RegistrationValidityCheck
from infrastructure.intelligence.compliance_domain.checks.insurance import InsuranceValidityCheck
from infrastructure.intelligence.compliance_domain.checks.fitness import FitnessCertificateCheck
from infrastructure.intelligence.compliance_domain.checks.pollution import PollutionCertificateCheck
from infrastructure.intelligence.compliance_domain.checks.permit import PermitValidityCheck
from infrastructure.intelligence.compliance_domain.checks.driver_license import DriverLicenseValidityCheck
from infrastructure.intelligence.compliance_domain.assessments.vehicle_compliance import VehicleComplianceAssessment
from infrastructure.intelligence.compliance_domain.risk.vehicle_compliance_risk import VehicleComplianceRiskEngine
from infrastructure.intelligence.compliance_domain.decision.vehicle_compliance_decision import VehicleComplianceDecisionEngine


class IntelligenceFactory:
    """
    Constructs and configures the IntelligenceOrchestrator by registering all 
    domain engines across the engine's registries.
    """

    @staticmethod
    def build_orchestrator() -> IntelligenceOrchestrator:
        # 1. Checks
        check_registry = CheckRegistry()
        # Tyre
        check_registry.register(TyrePressureCheck)
        check_registry.register(TyreTreadDepthCheck)
        check_registry.register(TyreAgeCheck)
        check_registry.register(TyreWearPatternCheck)
        check_registry.register(TyreDamageCheck)
        # Route
        check_registry.register(RouteDeviationCheck)
        check_registry.register(TripDelayCheck)
        check_registry.register(UnauthorizedStopCheck)
        check_registry.register(GeofenceViolationCheck)
        check_registry.register(ExcessiveDetourCheck)
        # Maintenance
        check_registry.register(MaintenanceServiceOverdueCheck)
        check_registry.register(MaintenanceDistanceOverdueCheck)
        check_registry.register(MaintenanceTimeOverdueCheck)
        check_registry.register(RepeatedFailureCheck)
        check_registry.register(CriticalComponentDueCheck)
        # Fuel
        check_registry.register(FuelQuantityCheck)
        check_registry.register(FuelLocationCheck)
        check_registry.register(FuelTimingCheck)
        check_registry.register(FuelTankCapacityCheck)
        # Driver
        check_registry.register(DriverOverspeedCheck)
        check_registry.register(HarshAccelerationCheck)
        check_registry.register(HarshBrakingCheck)
        check_registry.register(ExcessiveIdlingCheck)
        check_registry.register(RouteComplianceCheck)
        # Compliance
        check_registry.register(RegistrationValidityCheck)
        check_registry.register(InsuranceValidityCheck)
        check_registry.register(FitnessCertificateCheck)
        check_registry.register(PollutionCertificateCheck)
        check_registry.register(PermitValidityCheck)
        check_registry.register(DriverLicenseValidityCheck)
        
        check_executor = CheckExecutor(registry=check_registry)

        # 2. Assessments
        assessment_registry = AssessmentRegistry()
        assessment_registry.register(TyreHealthAssessment)
        assessment_registry.register(TripComplianceAssessment)
        assessment_registry.register(VehicleHealthAssessment)
        assessment_registry.register(FuelTransactionIntegrityAssessment)
        assessment_registry.register(DriverBehaviourAssessment)
        assessment_registry.register(VehicleComplianceAssessment)
        
        assessment_executor = AssessmentExecutor(registry=assessment_registry)

        # 3. Domain Risk
        risk_registry = DomainRiskRegistry()
        risk_registry.register(TyreHealthRiskEngine)
        risk_registry.register(TripComplianceRiskEngine)
        risk_registry.register(VehicleHealthRiskEngine)
        risk_registry.register(FuelTransactionRiskEngine)
        risk_registry.register(DriverBehaviourRiskEngine)
        risk_registry.register(VehicleComplianceRiskEngine)
        
        risk_executor = DomainRiskExecutor(registry=risk_registry)

        # 4. Global Decision
        decision_registry = DecisionRegistry()
        decision_registry.register(TyreHealthDecisionEngine)
        decision_registry.register(TripComplianceDecisionEngine)
        decision_registry.register(VehicleHealthDecisionEngine)
        decision_registry.register(FuelDecisionEngine)
        decision_registry.register(DriverBehaviourDecisionEngine)
        decision_registry.register(VehicleComplianceDecisionEngine)
        
        decision_executor = DecisionExecutor(registry=decision_registry)

        # Orchestrator
        return IntelligenceOrchestrator(
            check_executor=check_executor,
            assessment_executor=assessment_executor,
            risk_executor=risk_executor,
            decision_executor=decision_executor
        )
