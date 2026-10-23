"""
FleetGuard — Dispatch Suitability Service
Canonical domain service for evaluating driver qualifications, vehicle capabilities,
cargo requirements, and operational readiness across all dispatch and planning touchpoints.
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime, date, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from models.driver_domain import Driver, DriverStatus
from models.vehicle_domain import Vehicle, VehicleStatus
from models.trip_domain import Trip, TripStatus
from models.maintenance_domain import MaintenanceRecord, MaintenanceStatus
from models.driver_qualification import (
    DriverQualification,
    QualificationType,
    LicenseClass,
    QualificationVerificationStatus,
)
from schemas.pre_trip_intelligence import SuitabilityAssessment, SuitabilityStatus

logger = logging.getLogger("fleetguard.dispatch_suitability")

LICENSE_HIERARCHY: Dict[str, int] = {
    "LMV": 1,
    "MGV": 2,
    "HGV": 3,
    "HMV": 4,
}

VEHICLE_CLASS_HIERARCHY: Dict[str, int] = {
    "LIGHT_COMMERCIAL": 1,
    "MEDIUM_DUTY": 2,
    "HEAVY_DUTY": 3,
    "TRAILER": 4,
}


@dataclass
class DispatchSuitabilityResult:
    is_dispatchable: bool
    vehicle_suitability: SuitabilityAssessment
    driver_suitability: SuitabilityAssessment
    cargo_suitability: SuitabilityAssessment
    qualification_suitability: SuitabilityAssessment
    hard_failures: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class DispatchSuitabilityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def evaluate_dispatch_suitability(
        self,
        *,
        company_id: int,
        vehicle_id: Optional[int] = None,
        driver_id: Optional[int] = None,
        planned_start: Optional[datetime] = None,
        planned_end: Optional[datetime] = None,
        route_distance_km: Optional[float] = None,
        cargo_weight: Optional[float] = None,
        cargo_category: Optional[str] = None,
        required_vehicle_class: Optional[str] = None,
        required_driver_qualification: Optional[str] = None,
        cargo_temperature_required: Optional[bool] = None,
        exclude_trip_id: Optional[int] = None,
    ) -> DispatchSuitabilityResult:
        hard_failures: List[str] = []
        warnings: List[str] = []

        ref_date: date = planned_start.date() if planned_start else datetime.now(timezone.utc).date()
        norm_cargo_category: str = cargo_category.upper() if cargo_category else "GENERAL"

        # 1. Fetch Vehicle and Driver
        vehicle: Optional[Vehicle] = None
        if vehicle_id:
            vehicle = await self.db.get(Vehicle, vehicle_id)
            if not vehicle or vehicle.company_id != company_id:
                hard_failures.append("Invalid vehicle_id: Assigned vehicle does not belong to this company.")
                vehicle = None

        driver: Optional[Driver] = None
        if driver_id:
            driver = await self.db.get(Driver, driver_id)
            if not driver or driver.company_id != company_id:
                hard_failures.append("Invalid driver_id: Assigned driver does not belong to this company.")
                driver = None

        # 2. Vehicle Operational Suitability
        v_status = SuitabilityStatus.SUITABLE
        v_reasons: List[str] = []

        if not vehicle_id:
            v_status = SuitabilityStatus.INSUFFICIENT_DATA
            v_reasons.append("No vehicle assigned.")
        elif vehicle is None:
            v_status = SuitabilityStatus.UNSUITABLE
            v_reasons.append("Vehicle not found or unauthorized.")
        else:
            if vehicle.status != VehicleStatus.ACTIVE:
                v_status = SuitabilityStatus.UNSUITABLE
                msg = f"Vehicle is not eligible for dispatch (status is {vehicle.status.value})."
                v_reasons.append(msg)
                hard_failures.append(msg)

            # Check active trips for vehicle
            v_trip_stmt = select(Trip).where(
                Trip.vehicle_id == vehicle.id,
                Trip.status.in_([TripStatus.IN_PROGRESS, TripStatus.PAUSED]),
            )
            if exclude_trip_id is not None:
                v_trip_stmt = v_trip_stmt.where(Trip.id != exclude_trip_id)
            v_active_trips = (await self.db.execute(v_trip_stmt)).scalars().all()
            if v_active_trips:
                v_status = SuitabilityStatus.UNSUITABLE
                msg = "Assigned vehicle already has an active trip in progress."
                v_reasons.append(msg)
                hard_failures.append(msg)

            # Check Maintenance records
            maint_stmt = select(MaintenanceRecord).where(
                MaintenanceRecord.vehicle_id == vehicle.id,
                MaintenanceRecord.status.in_([MaintenanceStatus.SCHEDULED, MaintenanceStatus.STARTED]),
            )
            maint_records = (await self.db.execute(maint_stmt)).scalars().all()
            for m in maint_records:
                if m.status == MaintenanceStatus.STARTED:
                    v_status = SuitabilityStatus.UNSUITABLE
                    msg = "Vehicle is currently under active maintenance."
                    v_reasons.append(msg)
                    hard_failures.append(msg)
                    break
                elif m.status == MaintenanceStatus.SCHEDULED:
                    if v_status != SuitabilityStatus.UNSUITABLE:
                        v_status = SuitabilityStatus.MARGINAL
                    msg = "Vehicle has scheduled maintenance."
                    if msg not in v_reasons:
                        v_reasons.append(msg)
                        warnings.append(msg)

            # Check vehicle maintenance status flags
            if vehicle.maintenance_status == "OVERDUE":
                v_status = SuitabilityStatus.UNSUITABLE
                msg = "Vehicle is overdue for maintenance."
                v_reasons.append(msg)
                hard_failures.append(msg)
            elif vehicle.maintenance_status in ["DUE", "DUE_SOON"]:
                if v_status != SuitabilityStatus.UNSUITABLE:
                    v_status = SuitabilityStatus.MARGINAL
                msg = f"Vehicle maintenance is {vehicle.maintenance_status.lower().replace('_', ' ')}."
                v_reasons.append(msg)
                warnings.append(msg)

            if not v_reasons:
                v_reasons.append("Vehicle is available and suitable for the trip.")

        vehicle_assessment = SuitabilityAssessment(status=v_status, reasons=v_reasons)

        # 3. Driver Operational Suitability
        d_status = SuitabilityStatus.SUITABLE
        d_reasons: List[str] = []

        if not driver_id:
            d_status = SuitabilityStatus.INSUFFICIENT_DATA
            d_reasons.append("No driver assigned.")
        elif driver is None:
            d_status = SuitabilityStatus.UNSUITABLE
            d_reasons.append("Driver not found or unauthorized.")
        else:
            if driver.status != DriverStatus.ACTIVE:
                d_status = SuitabilityStatus.UNSUITABLE
                msg = f"Driver is not active (status is {driver.status.value})."
                d_reasons.append(msg)
                hard_failures.append(msg)

            # Check active trips for driver
            d_trip_stmt = select(Trip).where(
                Trip.driver_id == driver.id,
                Trip.status.in_([TripStatus.IN_PROGRESS, TripStatus.PAUSED]),
            )
            if exclude_trip_id is not None:
                d_trip_stmt = d_trip_stmt.where(Trip.id != exclude_trip_id)
            d_active_trips = (await self.db.execute(d_trip_stmt)).scalars().all()
            if d_active_trips:
                d_status = SuitabilityStatus.UNSUITABLE
                msg = "Assigned driver already has an active trip in progress."
                d_reasons.append(msg)
                hard_failures.append(msg)

            if driver.duty_status and driver.duty_status.lower() in ["off_duty", "on_leave"]:
                if d_status != SuitabilityStatus.UNSUITABLE:
                    d_status = SuitabilityStatus.MARGINAL
                msg = f"Driver duty status is {driver.duty_status}."
                d_reasons.append(msg)
                warnings.append(msg)

            if not d_reasons:
                d_reasons.append("Driver is available and suitable for the trip.")

        driver_assessment = SuitabilityAssessment(status=d_status, reasons=d_reasons)

        # 4. Cargo & Vehicle Compatibility
        c_status = SuitabilityStatus.SUITABLE
        c_reasons: List[str] = []

        if not vehicle:
            c_status = SuitabilityStatus.INSUFFICIENT_DATA
            c_reasons.append("No vehicle assigned to evaluate cargo capability.")
        else:
            # 4a. Payload capacity
            if cargo_weight is not None and cargo_weight > 0:
                if vehicle.payload_capacity_tonnes is not None:
                    if cargo_weight > vehicle.payload_capacity_tonnes:
                        c_status = SuitabilityStatus.UNSUITABLE
                        msg = (
                            f"Cargo weight ({cargo_weight:.2f} t) exceeds vehicle payload capacity "
                            f"({vehicle.payload_capacity_tonnes:.2f} t)."
                        )
                        c_reasons.append(msg)
                        hard_failures.append(msg)
                    else:
                        c_reasons.append(
                            f"Cargo weight ({cargo_weight:.2f} t) within vehicle payload capacity "
                            f"({vehicle.payload_capacity_tonnes:.2f} t)."
                        )
                else:
                    if c_status != SuitabilityStatus.UNSUITABLE:
                        c_status = SuitabilityStatus.MARGINAL
                    msg = (
                        f"Vehicle payload capacity is unrecorded; cannot verify if cargo weight "
                        f"({cargo_weight:.2f} t) is within legal limits."
                    )
                    c_reasons.append(msg)
                    warnings.append(msg)

            # 4b. Vehicle class vs Required Vehicle class
            if required_vehicle_class:
                req_vc = required_vehicle_class.upper()
                if not vehicle.vehicle_class:
                    c_status = SuitabilityStatus.UNSUITABLE
                    msg = f"Trip requires vehicle class '{required_vehicle_class}', but vehicle class is not recorded."
                    c_reasons.append(msg)
                    hard_failures.append(msg)
                else:
                    veh_vc = vehicle.vehicle_class.upper()
                    if req_vc in VEHICLE_CLASS_HIERARCHY and veh_vc in VEHICLE_CLASS_HIERARCHY:
                        if VEHICLE_CLASS_HIERARCHY[veh_vc] < VEHICLE_CLASS_HIERARCHY[req_vc]:
                            c_status = SuitabilityStatus.UNSUITABLE
                            msg = (
                                f"Vehicle class '{vehicle.vehicle_class}' does not satisfy "
                                f"required class '{required_vehicle_class}'."
                            )
                            c_reasons.append(msg)
                            hard_failures.append(msg)
                        else:
                            c_reasons.append(f"Vehicle class '{vehicle.vehicle_class}' satisfies required '{required_vehicle_class}'.")
                    elif veh_vc != req_vc:
                        c_status = SuitabilityStatus.UNSUITABLE
                        msg = (
                            f"Vehicle class '{vehicle.vehicle_class}' does not match "
                            f"required class '{required_vehicle_class}'."
                        )
                        c_reasons.append(msg)
                        hard_failures.append(msg)
                    else:
                        c_reasons.append(f"Vehicle class matches '{required_vehicle_class}'.")

            # 4c. Hazardous Certification Check
            norm_cargo_category = cargo_category.upper() if cargo_category else "GENERAL"
            if norm_cargo_category == "HAZARDOUS":
                if not vehicle.hazardous_certified:
                    c_status = SuitabilityStatus.UNSUITABLE
                    msg = "Vehicle lacks hazardous materials transport certification (HAZMAT)."
                    c_reasons.append(msg)
                    hard_failures.append(msg)
                else:
                    c_reasons.append("Vehicle is certified for hazardous materials.")

            # 4d. Temperature Control / Reefer Check
            requires_temp = bool(cargo_temperature_required) or (norm_cargo_category == "PERISHABLE" and cargo_temperature_required is not False)
            if requires_temp:
                if not vehicle.temperature_controlled:
                    c_status = SuitabilityStatus.UNSUITABLE
                    msg = "Cargo requires temperature control, but vehicle lacks refrigeration equipment."
                    c_reasons.append(msg)
                    hard_failures.append(msg)
                else:
                    c_reasons.append("Vehicle is equipped with temperature control.")

            # 4e. Supported Cargo Categories
            if vehicle.supported_cargo_categories and norm_cargo_category:
                supported_norm = [c.upper() for c in vehicle.supported_cargo_categories]
                if norm_cargo_category not in supported_norm:
                    c_status = SuitabilityStatus.UNSUITABLE
                    msg = (
                        f"Cargo category '{norm_cargo_category}' is not supported by vehicle "
                        f"(supported: {', '.join(vehicle.supported_cargo_categories)})."
                    )
                    c_reasons.append(msg)
                    hard_failures.append(msg)

            if not c_reasons:
                c_reasons.append("Vehicle capabilities meet cargo requirements.")

        cargo_assessment = SuitabilityAssessment(status=c_status, reasons=c_reasons)

        # 5. Driver Qualifications & Certifications
        q_status = SuitabilityStatus.SUITABLE
        q_reasons: List[str] = []

        if not driver:
            q_status = SuitabilityStatus.INSUFFICIENT_DATA
            q_reasons.append("No driver assigned to evaluate qualifications.")
        else:
            # Query all qualifications for driver
            qual_stmt = select(DriverQualification).where(
                DriverQualification.driver_id == driver.id,
                DriverQualification.company_id == company_id,
            )
            driver_quals = (await self.db.execute(qual_stmt)).scalars().all()

            verified_valid: List[DriverQualification] = []
            pending_quals: List[DriverQualification] = []
            expired_quals: List[DriverQualification] = []
            rejected_quals: List[DriverQualification] = []

            for q in driver_quals:
                if q.verification_status == QualificationVerificationStatus.VERIFIED:
                    if q.expiry_date and q.expiry_date < ref_date:
                        expired_quals.append(q)
                    else:
                        verified_valid.append(q)
                elif q.verification_status == QualificationVerificationStatus.PENDING:
                    pending_quals.append(q)
                elif q.verification_status == QualificationVerificationStatus.REJECTED:
                    rejected_quals.append(q)
                elif q.verification_status == QualificationVerificationStatus.EXPIRED:
                    expired_quals.append(q)

            def _to_str(val) -> str:
                if val is None:
                    return ""
                return val.value if hasattr(val, "value") else str(val)

            # Check 5a: HAZMAT requirement
            is_hazmat_required = (
                norm_cargo_category == "HAZARDOUS" or 
                (required_driver_qualification and required_driver_qualification.upper() == "HAZMAT")
            )
            if is_hazmat_required:
                has_valid_hazmat = any(
                    _to_str(q.qualification_type) == "HAZMAT_CERTIFICATION" or
                    _to_str(q.license_class) == "HAZMAT"
                    for q in verified_valid
                )
                if has_valid_hazmat:
                    q_reasons.append("Driver holds verified HAZMAT qualification.")
                else:
                    q_status = SuitabilityStatus.UNSUITABLE
                    has_rejected = any(
                        _to_str(q.qualification_type) == "HAZMAT_CERTIFICATION" or
                        _to_str(q.license_class) == "HAZMAT"
                        for q in rejected_quals
                    )
                    has_expired = any(
                        _to_str(q.qualification_type) == "HAZMAT_CERTIFICATION" or
                        _to_str(q.license_class) == "HAZMAT"
                        for q in expired_quals
                    )
                    has_pending = any(
                        _to_str(q.qualification_type) == "HAZMAT_CERTIFICATION" or
                        _to_str(q.license_class) == "HAZMAT"
                        for q in pending_quals
                    )
                    if has_rejected:
                        msg = "Driver HAZMAT qualification was rejected during verification."
                    elif has_expired:
                        msg = "Driver HAZMAT qualification is expired."
                    elif has_pending:
                        msg = "Driver HAZMAT qualification is pending verification."
                    else:
                        msg = "Driver lacks mandatory verified HAZMAT certification for hazardous cargo."
                    q_reasons.append(msg)
                    hard_failures.append(msg)

            # Check 5b: Heavy Vehicle / Trailer requirement
            req_heavy = (
                (vehicle and vehicle.vehicle_class in ["HEAVY_DUTY", "TRAILER", "HGV", "HMV"]) or
                (required_vehicle_class and required_vehicle_class.upper() in ["HEAVY_DUTY", "TRAILER", "HGV", "HMV"]) or
                (required_driver_qualification and required_driver_qualification.upper() in ["HGV", "HMV"])
            )
            if req_heavy:
                has_valid_heavy = any(
                    _to_str(q.license_class) in ["HGV", "HMV"] or
                    _to_str(q.qualification_type) == "HEAVY_VEHICLE_ENDORSEMENT"
                    for q in verified_valid
                )
                if has_valid_heavy:
                    q_reasons.append("Driver holds verified heavy vehicle / HGV license.")
                else:
                    q_status = SuitabilityStatus.UNSUITABLE
                    has_rejected = any(
                        _to_str(q.license_class) in ["HGV", "HMV"] or
                        _to_str(q.qualification_type) == "HEAVY_VEHICLE_ENDORSEMENT"
                        for q in rejected_quals
                    )
                    has_expired = any(
                        _to_str(q.license_class) in ["HGV", "HMV"] or
                        _to_str(q.qualification_type) == "HEAVY_VEHICLE_ENDORSEMENT"
                        for q in expired_quals
                    )
                    has_pending = any(
                        _to_str(q.license_class) in ["HGV", "HMV"] or
                        _to_str(q.qualification_type) == "HEAVY_VEHICLE_ENDORSEMENT"
                        for q in pending_quals
                    )
                    if has_rejected:
                        msg = "Driver heavy vehicle license was rejected during verification (requires HGV or HMV)."
                    elif has_expired:
                        msg = "Driver heavy vehicle license is expired."
                    elif has_pending:
                        msg = "Driver heavy vehicle license is pending verification."
                    else:
                        held = [_to_str(q.license_class) for q in verified_valid if q.license_class]
                        if held:
                            msg = f"Driver holds license class ({', '.join(held)}), which does not permit heavy vehicle operation (requires HGV or HMV)."
                        else:
                            msg = "Driver lacks verified heavy vehicle license (requires HGV or HMV)."
                    q_reasons.append(msg)
                    hard_failures.append(msg)

            # Check 5c: Arbitrary explicit qualification requirement
            if required_driver_qualification:
                req_qual = required_driver_qualification.upper()
                if req_qual not in ["HAZMAT", "HGV", "HMV"]:
                    matched = False
                    for q in verified_valid:
                        q_str = _to_str(q.qualification_type).upper()
                        l_str = _to_str(q.license_class).upper()
                        if q_str == req_qual or l_str == req_qual:
                            matched = True
                            break
                        if req_qual in LICENSE_HIERARCHY and l_str in LICENSE_HIERARCHY:
                            if LICENSE_HIERARCHY[l_str] >= LICENSE_HIERARCHY[req_qual]:
                                matched = True
                                break
                    if matched:
                        q_reasons.append(f"Driver holds verified qualification for '{required_driver_qualification}'.")
                    else:
                        q_status = SuitabilityStatus.UNSUITABLE
                        has_rejected = any(
                            _to_str(q.qualification_type).upper() == req_qual or _to_str(q.license_class).upper() == req_qual
                            for q in rejected_quals
                        )
                        has_pending = any(
                            _to_str(q.qualification_type).upper() == req_qual or _to_str(q.license_class).upper() == req_qual
                            for q in pending_quals
                        )
                        has_expired = any(
                            _to_str(q.qualification_type).upper() == req_qual or _to_str(q.license_class).upper() == req_qual
                            for q in expired_quals
                        )
                        if has_rejected:
                            msg = f"Driver qualification '{required_driver_qualification}' was rejected during verification."
                        elif has_expired:
                            msg = f"Driver qualification '{required_driver_qualification}' has expired."
                        elif has_pending:
                            msg = f"Driver qualification '{required_driver_qualification}' is pending verification."
                        else:
                            msg = f"Driver lacks verified qualification '{required_driver_qualification}'."
                        q_reasons.append(msg)
                        hard_failures.append(msg)

            # Check 5d: General driving license check if driving a vehicle
            if vehicle and not is_hazmat_required and not req_heavy and not required_driver_qualification:
                has_any_license = any(
                    q.qualification_type == QualificationType.DRIVING_LICENSE or q.license_class is not None
                    for q in verified_valid
                )
                if not has_any_license:
                    # Check legacy driver fields
                    if driver.license_number:
                        if driver.license_valid_until and driver.license_valid_until < ref_date:
                            q_status = SuitabilityStatus.UNSUITABLE
                            msg = "Driver driving license has expired."
                            q_reasons.append(msg)
                            hard_failures.append(msg)
                        else:
                            if q_status != SuitabilityStatus.UNSUITABLE:
                                q_status = SuitabilityStatus.MARGINAL
                            msg = "Driver has legacy license on file but lacks structured verified qualification."
                            q_reasons.append(msg)
                            warnings.append(msg)
                    else:
                        if q_status != SuitabilityStatus.UNSUITABLE:
                            q_status = SuitabilityStatus.MARGINAL
                        msg = "Driver lacks verified driving license or qualifications on file (review required)."
                        q_reasons.append(msg)
                        warnings.append(msg)

            if not q_reasons:
                q_reasons.append("Driver qualifications verified and suitable.")

        qualification_assessment = SuitabilityAssessment(status=q_status, reasons=q_reasons)

        is_dispatchable = (
            len(hard_failures) == 0 and
            vehicle_assessment.status != SuitabilityStatus.UNSUITABLE and
            driver_assessment.status != SuitabilityStatus.UNSUITABLE and
            cargo_assessment.status != SuitabilityStatus.UNSUITABLE and
            qualification_assessment.status != SuitabilityStatus.UNSUITABLE
        )

        return DispatchSuitabilityResult(
            is_dispatchable=is_dispatchable,
            vehicle_suitability=vehicle_assessment,
            driver_suitability=driver_assessment,
            cargo_suitability=cargo_assessment,
            qualification_suitability=qualification_assessment,
            hard_failures=hard_failures,
            warnings=warnings,
        )
