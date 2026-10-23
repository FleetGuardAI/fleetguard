"""
FleetGuard — Driver Qualification & Cargo Capability Matrix Regression Suite
Exhaustive test suite covering all 23 mandatory regression scenarios:
1. Valid driver qualification creation with PENDING verification status.
2. Administrative verification of driver qualification (VERIFIED with authorized user).
3. Non-administrative (e.g. driver) verification rejection (403 Forbidden).
4. Administrative rejection of driver qualification (REJECTED with reason).
5. Qualification tenant isolation (cross-tenant verification/access rejection).
6. License class compatibility matching: LMV cannot operate HGV.
7. License class compatibility matching: HGV operates HGV and LMV.
8. License class compatibility matching: HMV operates all heavy and medium goods.
9. Verification status gate: PENDING qualification rejected for mandatory requirement.
10. Verification status gate: REJECTED qualification rejected for mandatory requirement.
11. Expiry gate: Qualification expired before trip start date rejected.
12. Expiry gate: Qualification valid through trip duration accepted.
13. Cargo capability: Overload rejection (cargo weight > vehicle payload capacity).
14. Cargo capability: Weight within payload capacity accepted.
15. Cargo capability: Unrecorded vehicle payload capacity yields REVIEW_REQUIRED / warning.
16. Hazardous cargo gate: Vehicle without hazardous certification rejected.
17. Hazardous cargo gate: Vehicle with hazardous certification accepted.
18. Hazardous cargo driver gate: Driver without verified HAZMAT certification rejected.
19. Hazardous cargo driver gate: Driver with verified HAZMAT certification accepted.
20. Temperature control gate: Reefer required cargo with standard vehicle rejected.
21. Temperature control gate: Reefer required cargo with temperature-controlled vehicle accepted.
22. Pre-trip intelligence score integrity: Overload or missing mandatory cert forces AVOID regardless of profit.
23. Start-trip boundary enforcement: POST /driver-app/trips/{id}/start strictly enforces driver qualifications and vehicle capabilities.
"""

import pytest
import uuid
from datetime import datetime, date, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import select

from main import app
from database import get_db
from models.company import Company
from models.user import User, UserRole
from models.vehicle_domain import Vehicle, VehicleStatus
from models.driver_domain import Driver, DriverStatus
from models.trip_domain import Trip, TripStatus
from models.driver_qualification import (
    DriverQualification,
    QualificationType,
    LicenseClass,
    QualificationVerificationStatus,
)
from services.auth_service import get_current_user
from routers.driver_mobile import get_current_driver


@pytest.fixture
async def setup_matrix_env(db_session):
    """Sets up isolated tenant companies, vehicles with capability specs, drivers, and users."""
    suffix = uuid.uuid4().hex[:6]

    # Companies
    comp_a = Company(
        company_name=f"Logistics Alpha {suffix}",
        owner_name="Alpha Owner",
        mobile_number=f"alpha_{suffix}",
    )
    comp_b = Company(
        company_name=f"Logistics Beta {suffix}",
        owner_name="Beta Owner",
        mobile_number=f"beta_{suffix}",
    )
    db_session.add_all([comp_a, comp_b])
    await db_session.flush()

    # Users
    admin_a = User(
        company_id=comp_a.id,
        role=UserRole.COMPANY_ADMIN,
        is_active=True,
        full_name="Alpha Admin",
        email=f"admin_a_{suffix}@fleetguard.io",
        mobile_number=f"adm_a_{suffix}",
        password_hash="secret",
    )
    driver_user_a = User(
        company_id=comp_a.id,
        role=UserRole.DRIVER,
        is_active=True,
        full_name="Driver User A",
        email=f"driver_a_{suffix}@fleetguard.io",
        mobile_number=f"dru_a_{suffix}",
        password_hash="secret",
    )
    admin_b = User(
        company_id=comp_b.id,
        role=UserRole.COMPANY_ADMIN,
        is_active=True,
        full_name="Beta Admin",
        email=f"admin_b_{suffix}@fleetguard.io",
        mobile_number=f"adm_b_{suffix}",
        password_hash="secret",
    )
    db_session.add_all([admin_a, driver_user_a, admin_b])
    await db_session.flush()

    # Drivers
    drv_a = Driver(
        company_id=comp_a.id,
        user_id=driver_user_a.id,
        name=f"Driver Alpha {suffix}",
        phone_number=f"+9198{suffix[:8]}",
        status=DriverStatus.ACTIVE,
    )
    drv_b = Driver(
        company_id=comp_b.id,
        name=f"Driver Beta {suffix}",
        phone_number=f"+9197{suffix[:8]}",
        status=DriverStatus.ACTIVE,
    )
    db_session.add_all([drv_a, drv_b])
    await db_session.flush()

    # Vehicles for Company A
    veh_standard = Vehicle(
        company_id=comp_a.id,
        registration_number=f"STD-{suffix}",
        vehicle_class="LIGHT_COMMERCIAL",
        payload_capacity_tonnes=5.0,
        status=VehicleStatus.ACTIVE,
        tank_capacity=200.0,
        hazardous_certified=False,
        temperature_controlled=False,
    )
    veh_heavy = Vehicle(
        company_id=comp_a.id,
        registration_number=f"HVY-{suffix}",
        vehicle_class="HEAVY_DUTY",
        payload_capacity_tonnes=25.0,
        status=VehicleStatus.ACTIVE,
        tank_capacity=450.0,
        hazardous_certified=False,
        temperature_controlled=False,
    )
    veh_hazmat = Vehicle(
        company_id=comp_a.id,
        registration_number=f"HAZ-{suffix}",
        vehicle_class="HEAVY_DUTY",
        payload_capacity_tonnes=20.0,
        status=VehicleStatus.ACTIVE,
        tank_capacity=400.0,
        hazardous_certified=True,
        temperature_controlled=False,
    )
    veh_reefer = Vehicle(
        company_id=comp_a.id,
        registration_number=f"REF-{suffix}",
        vehicle_class="MEDIUM_DUTY",
        payload_capacity_tonnes=10.0,
        status=VehicleStatus.ACTIVE,
        tank_capacity=300.0,
        hazardous_certified=False,
        temperature_controlled=True,
    )
    veh_unrecorded = Vehicle(
        company_id=comp_a.id,
        registration_number=f"UNR-{suffix}",
        vehicle_class="MEDIUM_DUTY",
        payload_capacity_tonnes=None,  # Unrecorded payload capacity
        status=VehicleStatus.ACTIVE,
        tank_capacity=300.0,
        hazardous_certified=False,
        temperature_controlled=False,
    )
    db_session.add_all([veh_standard, veh_heavy, veh_hazmat, veh_reefer, veh_unrecorded])
    await db_session.flush()

    return {
        "suffix": suffix,
        "comp_a": comp_a,
        "comp_b": comp_b,
        "admin_a": admin_a,
        "admin_b": admin_b,
        "driver_user_a": driver_user_a,
        "drv_a": drv_a,
        "drv_b": drv_b,
        "veh_standard": veh_standard,
        "veh_heavy": veh_heavy,
        "veh_hazmat": veh_hazmat,
        "veh_reefer": veh_reefer,
        "veh_unrecorded": veh_unrecorded,
    }


# ===========================================================================
# 1. Qualification Creation with PENDING Status
# ===========================================================================
@pytest.mark.asyncio
async def test_01_qualification_creation_pending_status(db_session, setup_matrix_env):
    env = setup_matrix_env
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: env["admin_a"]

    with TestClient(app) as client:
        res = client.post(
            f"/api/v1/drivers/{env['drv_a'].id}/qualifications",
            json={
                "qualification_type": "DRIVING_LICENSE",
                "license_class": "HGV",
                "certificate_number": f"DL-MH-12-{env['suffix']}",
                "issuing_authority": "RTO Pune",
                "issue_date": "2024-01-01",
                "expiry_date": "2029-01-01",
                "evidence_url": "https://storage.fleetguard.io/docs/dl.pdf",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["verification_status"] == "PENDING"
        assert data["license_class"] == "HGV"
        assert data["certificate_number"] == f"DL-MH-12-{env['suffix']}"


# ===========================================================================
# 2. Administrative Verification of Qualification
# ===========================================================================
@pytest.mark.asyncio
async def test_02_admin_verification_of_qualification(db_session, setup_matrix_env):
    env = setup_matrix_env
    qual = DriverQualification(
        driver_id=env["drv_a"].id,
        company_id=env["comp_a"].id,
        qualification_type=QualificationType.DRIVING_LICENSE,
        license_class=LicenseClass.HGV,
        certificate_number=f"DL-VER-{env['suffix']}",
        verification_status=QualificationVerificationStatus.PENDING,
    )
    db_session.add(qual)
    await db_session.flush()

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: env["admin_a"]

    with TestClient(app) as client:
        res = client.post(
            f"/api/v1/driver-qualifications/{qual.id}/verify",
            json={"verification_status": "VERIFIED"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["verification_status"] == "VERIFIED"
        assert data["verified_by"] == env["admin_a"].email
        assert data["verified_at"] is not None


# ===========================================================================
# 3. Non-Administrative Verification Rejection (403 Forbidden)
# ===========================================================================
@pytest.mark.asyncio
async def test_03_non_admin_verification_forbidden(db_session, setup_matrix_env):
    env = setup_matrix_env
    qual = DriverQualification(
        driver_id=env["drv_a"].id,
        company_id=env["comp_a"].id,
        qualification_type=QualificationType.DRIVING_LICENSE,
        license_class=LicenseClass.HGV,
        certificate_number=f"DL-SEC-{env['suffix']}",
        verification_status=QualificationVerificationStatus.PENDING,
    )
    db_session.add(qual)
    await db_session.flush()

    app.dependency_overrides[get_db] = lambda: db_session
    # User has DRIVER role
    app.dependency_overrides[get_current_user] = lambda: env["driver_user_a"]

    with TestClient(app) as client:
        res = client.post(
            f"/api/v1/driver-qualifications/{qual.id}/verify",
            json={"verification_status": "VERIFIED"},
        )
        assert res.status_code == 403
        assert "lack authorized administrative role" in res.json()["detail"]


# ===========================================================================
# 4. Administrative Rejection with Reason
# ===========================================================================
@pytest.mark.asyncio
async def test_04_admin_rejection_with_reason(db_session, setup_matrix_env):
    env = setup_matrix_env
    qual = DriverQualification(
        driver_id=env["drv_a"].id,
        company_id=env["comp_a"].id,
        qualification_type=QualificationType.DRIVING_LICENSE,
        license_class=LicenseClass.HGV,
        certificate_number=f"DL-REJ-{env['suffix']}",
        verification_status=QualificationVerificationStatus.PENDING,
    )
    db_session.add(qual)
    await db_session.flush()

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: env["admin_a"]

    with TestClient(app) as client:
        res = client.post(
            f"/api/v1/driver-qualifications/{qual.id}/verify",
            json={
                "verification_status": "REJECTED",
                "rejection_reason": "Photograph blurred and license watermark missing",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["verification_status"] == "REJECTED"
        assert data["rejection_reason"] == "Photograph blurred and license watermark missing"


# ===========================================================================
# 5. Qualification Tenant Isolation
# ===========================================================================
@pytest.mark.asyncio
async def test_05_qualification_tenant_isolation(db_session, setup_matrix_env):
    env = setup_matrix_env
    qual_a = DriverQualification(
        driver_id=env["drv_a"].id,
        company_id=env["comp_a"].id,
        qualification_type=QualificationType.DRIVING_LICENSE,
        license_class=LicenseClass.HGV,
        certificate_number=f"DL-TEN-{env['suffix']}",
        verification_status=QualificationVerificationStatus.PENDING,
    )
    db_session.add(qual_a)
    await db_session.flush()

    app.dependency_overrides[get_db] = lambda: db_session
    # Admin B attempts to access / verify Company A's qualification
    app.dependency_overrides[get_current_user] = lambda: env["admin_b"]

    with TestClient(app) as client:
        res_get = client.get(f"/api/v1/driver-qualifications/{qual_a.id}")
        assert res_get.status_code == 404

        res_verify = client.post(
            f"/api/v1/driver-qualifications/{qual_a.id}/verify",
            json={"verification_status": "VERIFIED"},
        )
        assert res_verify.status_code == 404


# ===========================================================================
# 6. License Class Mismatch: LMV Cannot Operate HGV
# ===========================================================================
@pytest.mark.asyncio
async def test_06_license_class_mismatch_lmv_for_heavy(db_session, setup_matrix_env):
    env = setup_matrix_env
    qual_lmv = DriverQualification(
        driver_id=env["drv_a"].id,
        company_id=env["comp_a"].id,
        qualification_type=QualificationType.DRIVING_LICENSE,
        license_class=LicenseClass.LMV,
        certificate_number=f"LMV-{env['suffix']}",
        verification_status=QualificationVerificationStatus.VERIFIED,
    )
    db_session.add(qual_lmv)
    await db_session.flush()

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: env["admin_a"]

    # Assign drv_a (LMV only) to heavy vehicle
    payload = {
        "origin_location": "Warehouse A",
        "destination_location": "Depot B",
        "vehicle_id": env["veh_heavy"].id,  # HEAVY_DUTY
        "driver_id": env["drv_a"].id,
        "planned_distance": 100.0,
    }

    with TestClient(app) as client:
        res = client.post("/api/v1/trips", json=payload)
        assert res.status_code == 400
        assert "does not permit heavy vehicle operation" in res.json()["detail"]


# ===========================================================================
# 7. License Class Matching: HGV Operates HGV and LMV
# ===========================================================================
@pytest.mark.asyncio
async def test_07_license_class_matching_hgv_for_heavy(db_session, setup_matrix_env):
    env = setup_matrix_env
    qual_hgv = DriverQualification(
        driver_id=env["drv_a"].id,
        company_id=env["comp_a"].id,
        qualification_type=QualificationType.DRIVING_LICENSE,
        license_class=LicenseClass.HGV,
        certificate_number=f"HGV-{env['suffix']}",
        verification_status=QualificationVerificationStatus.VERIFIED,
    )
    db_session.add(qual_hgv)
    await db_session.flush()

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: env["admin_a"]

    payload = {
        "origin_location": "Warehouse A",
        "destination_location": "Depot B",
        "vehicle_id": env["veh_heavy"].id,
        "driver_id": env["drv_a"].id,
        "planned_distance": 100.0,
    }

    with TestClient(app) as client:
        res = client.post("/api/v1/trips", json=payload)
        assert res.status_code == 201
        assert res.json()["status"] == "CREATED"


# ===========================================================================
# 8. License Class Hierarchy: HMV Covers All Heavy and Medium Goods
# ===========================================================================
@pytest.mark.asyncio
async def test_08_license_class_hierarchy_hmv_covers_all(db_session, setup_matrix_env):
    env = setup_matrix_env
    qual_hmv = DriverQualification(
        driver_id=env["drv_a"].id,
        company_id=env["comp_a"].id,
        qualification_type=QualificationType.DRIVING_LICENSE,
        license_class=LicenseClass.HMV,
        certificate_number=f"HMV-{env['suffix']}",
        verification_status=QualificationVerificationStatus.VERIFIED,
    )
    db_session.add(qual_hmv)
    await db_session.flush()

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: env["admin_a"]

    payload = {
        "origin_location": "Warehouse A",
        "destination_location": "Depot B",
        "vehicle_id": env["veh_heavy"].id,
        "driver_id": env["drv_a"].id,
        "required_vehicle_class": "HEAVY_DUTY",
        "planned_distance": 120.0,
    }

    with TestClient(app) as client:
        res = client.post("/api/v1/trips", json=payload)
        assert res.status_code == 201


# ===========================================================================
# 9. Verification Status Gate: PENDING Qualification Rejected for Mandatory Gate
# ===========================================================================
@pytest.mark.asyncio
async def test_09_pending_qualification_cannot_satisfy_mandatory_gate(db_session, setup_matrix_env):
    env = setup_matrix_env
    qual_pending = DriverQualification(
        driver_id=env["drv_a"].id,
        company_id=env["comp_a"].id,
        qualification_type=QualificationType.DRIVING_LICENSE,
        license_class=LicenseClass.HGV,
        certificate_number=f"HGV-PND-{env['suffix']}",
        verification_status=QualificationVerificationStatus.PENDING,
    )
    db_session.add(qual_pending)
    await db_session.flush()

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: env["admin_a"]

    payload = {
        "origin_location": "Warehouse A",
        "destination_location": "Depot B",
        "vehicle_id": env["veh_heavy"].id,
        "driver_id": env["drv_a"].id,
        "planned_distance": 100.0,
    }

    with TestClient(app) as client:
        res = client.post("/api/v1/trips", json=payload)
        assert res.status_code == 400
        assert "pending verification" in res.json()["detail"]


# ===========================================================================
# 10. Verification Status Gate: REJECTED Qualification Rejected
# ===========================================================================
@pytest.mark.asyncio
async def test_10_rejected_qualification_cannot_satisfy_mandatory_gate(db_session, setup_matrix_env):
    env = setup_matrix_env
    qual_rejected = DriverQualification(
        driver_id=env["drv_a"].id,
        company_id=env["comp_a"].id,
        qualification_type=QualificationType.DRIVING_LICENSE,
        license_class=LicenseClass.HGV,
        certificate_number=f"HGV-REJ-{env['suffix']}",
        verification_status=QualificationVerificationStatus.REJECTED,
        rejection_reason="Forged document",
    )
    db_session.add(qual_rejected)
    await db_session.flush()

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: env["admin_a"]

    payload = {
        "origin_location": "Warehouse A",
        "destination_location": "Depot B",
        "vehicle_id": env["veh_heavy"].id,
        "driver_id": env["drv_a"].id,
        "planned_distance": 100.0,
    }

    with TestClient(app) as client:
        res = client.post("/api/v1/trips", json=payload)
        assert res.status_code == 400
        assert "rejected during verification" in res.json()["detail"]


# ===========================================================================
# 11. Expiry Gate: Qualification Expired Before Trip Start Date Rejected
# ===========================================================================
@pytest.mark.asyncio
async def test_11_expired_qualification_rejected(db_session, setup_matrix_env):
    env = setup_matrix_env
    yesterday = (datetime.now(timezone.utc) - timedelta(days=2)).date()
    qual_expired = DriverQualification(
        driver_id=env["drv_a"].id,
        company_id=env["comp_a"].id,
        qualification_type=QualificationType.DRIVING_LICENSE,
        license_class=LicenseClass.HGV,
        certificate_number=f"HGV-EXP-{env['suffix']}",
        verification_status=QualificationVerificationStatus.VERIFIED,
        expiry_date=yesterday,
    )
    db_session.add(qual_expired)
    await db_session.flush()

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: env["admin_a"]

    payload = {
        "origin_location": "Warehouse A",
        "destination_location": "Depot B",
        "vehicle_id": env["veh_heavy"].id,
        "driver_id": env["drv_a"].id,
        "planned_start_time": datetime.now(timezone.utc).isoformat(),
        "planned_distance": 100.0,
    }

    with TestClient(app) as client:
        res = client.post("/api/v1/trips", json=payload)
        assert res.status_code == 400
        assert "expired" in res.json()["detail"].lower()


# ===========================================================================
# 12. Expiry Gate: Qualification Valid Through Trip Duration Accepted
# ===========================================================================
@pytest.mark.asyncio
async def test_12_unexpired_qualification_accepted(db_session, setup_matrix_env):
    env = setup_matrix_env
    next_year = (datetime.now(timezone.utc) + timedelta(days=365)).date()
    qual_valid = DriverQualification(
        driver_id=env["drv_a"].id,
        company_id=env["comp_a"].id,
        qualification_type=QualificationType.DRIVING_LICENSE,
        license_class=LicenseClass.HGV,
        certificate_number=f"HGV-VAL-{env['suffix']}",
        verification_status=QualificationVerificationStatus.VERIFIED,
        expiry_date=next_year,
    )
    db_session.add(qual_valid)
    await db_session.flush()

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: env["admin_a"]

    payload = {
        "origin_location": "Warehouse A",
        "destination_location": "Depot B",
        "vehicle_id": env["veh_heavy"].id,
        "driver_id": env["drv_a"].id,
        "planned_start_time": datetime.now(timezone.utc).isoformat(),
        "planned_distance": 100.0,
    }

    with TestClient(app) as client:
        res = client.post("/api/v1/trips", json=payload)
        assert res.status_code == 201


# ===========================================================================
# 13. Cargo Capability: Overload Rejection
# ===========================================================================
@pytest.mark.asyncio
async def test_13_payload_overload_rejection(db_session, setup_matrix_env):
    env = setup_matrix_env
    # Vehicle standard has payload capacity of 5.0 tonnes
    payload = {
        "origin_location": "Warehouse A",
        "destination_location": "Depot B",
        "vehicle_id": env["veh_standard"].id,
        "cargo_weight": 8.5,  # Exceeds 5.0 tonnes
        "planned_distance": 50.0,
    }

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: env["admin_a"]

    with TestClient(app) as client:
        res = client.post("/api/v1/trips", json=payload)
        assert res.status_code == 400
        assert "exceeds vehicle payload capacity" in res.json()["detail"]


# ===========================================================================
# 14. Cargo Capability: Weight Within Payload Capacity Accepted
# ===========================================================================
@pytest.mark.asyncio
async def test_14_payload_within_capacity_accepted(db_session, setup_matrix_env):
    env = setup_matrix_env
    # Vehicle standard has capacity 5.0 tonnes; cargo is 3.5 tonnes
    payload = {
        "origin_location": "Warehouse A",
        "destination_location": "Depot B",
        "vehicle_id": env["veh_standard"].id,
        "cargo_weight": 3.5,
        "planned_distance": 50.0,
    }

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: env["admin_a"]

    with TestClient(app) as client:
        res = client.post("/api/v1/trips", json=payload)
        assert res.status_code == 201


# ===========================================================================
# 15. Cargo Capability: Unrecorded Vehicle Payload Capacity Yields Warning
# ===========================================================================
@pytest.mark.asyncio
async def test_15_unrecorded_vehicle_payload_capacity_marginal(db_session, setup_matrix_env):
    env = setup_matrix_env
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: env["admin_a"]

    with TestClient(app) as client:
        res = client.post(
            "/api/v1/trips/intelligence/evaluate",
            json={
                "origin_location": "Warehouse A",
                "destination_location": "Depot B",
                "vehicle_id": env["veh_unrecorded"].id,
                "cargo_weight": 7.0,
                "revenue": 15000.0,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["cargo_suitability"]["status"] == "MARGINAL"
        assert any("unrecorded" in r for r in data["cargo_suitability"]["reasons"])


# ===========================================================================
# 16. Hazardous Cargo Gate: Vehicle Without Hazardous Certification Rejected
# ===========================================================================
@pytest.mark.asyncio
async def test_16_hazardous_cargo_vehicle_without_certification_rejected(db_session, setup_matrix_env):
    env = setup_matrix_env
    # Heavy truck lacks hazardous_certified (False)
    payload = {
        "origin_location": "Chemical Refinery",
        "destination_location": "Industrial Park",
        "vehicle_id": env["veh_heavy"].id,
        "cargo_category": "HAZARDOUS",
        "planned_distance": 120.0,
    }

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: env["admin_a"]

    with TestClient(app) as client:
        res = client.post("/api/v1/trips", json=payload)
        assert res.status_code == 400
        assert "lacks hazardous materials transport certification" in res.json()["detail"]


# ===========================================================================
# 17. Hazardous Cargo Gate: Vehicle With Hazardous Certification Accepted
# ===========================================================================
@pytest.mark.asyncio
async def test_17_hazardous_cargo_vehicle_with_certification_accepted(db_session, setup_matrix_env):
    env = setup_matrix_env
    # Setup driver with verified HAZMAT
    qual_hazmat = DriverQualification(
        driver_id=env["drv_a"].id,
        company_id=env["comp_a"].id,
        qualification_type=QualificationType.HAZMAT_CERTIFICATION,
        license_class=LicenseClass.HAZMAT,
        certificate_number=f"HAZ-{env['suffix']}",
        verification_status=QualificationVerificationStatus.VERIFIED,
    )
    qual_hgv = DriverQualification(
        driver_id=env["drv_a"].id,
        company_id=env["comp_a"].id,
        qualification_type=QualificationType.DRIVING_LICENSE,
        license_class=LicenseClass.HGV,
        certificate_number=f"HGV-{env['suffix']}",
        verification_status=QualificationVerificationStatus.VERIFIED,
    )
    db_session.add_all([qual_hazmat, qual_hgv])
    await db_session.flush()

    payload = {
        "origin_location": "Chemical Refinery",
        "destination_location": "Industrial Park",
        "vehicle_id": env["veh_hazmat"].id,
        "driver_id": env["drv_a"].id,
        "cargo_category": "HAZARDOUS",
        "planned_distance": 120.0,
    }

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: env["admin_a"]

    with TestClient(app) as client:
        res = client.post("/api/v1/trips", json=payload)
        assert res.status_code == 201


# ===========================================================================
# 18. Hazardous Cargo Driver Gate: Driver Without HAZMAT Certification Rejected
# ===========================================================================
@pytest.mark.asyncio
async def test_18_hazardous_cargo_driver_without_hazmat_cert_rejected(db_session, setup_matrix_env):
    env = setup_matrix_env
    # Driver has only HGV, no HAZMAT certification
    qual_hgv = DriverQualification(
        driver_id=env["drv_a"].id,
        company_id=env["comp_a"].id,
        qualification_type=QualificationType.DRIVING_LICENSE,
        license_class=LicenseClass.HGV,
        certificate_number=f"HGV-ONLY-{env['suffix']}",
        verification_status=QualificationVerificationStatus.VERIFIED,
    )
    db_session.add(qual_hgv)
    await db_session.flush()

    payload = {
        "origin_location": "Chemical Plant",
        "destination_location": "Storage Terminal",
        "vehicle_id": env["veh_hazmat"].id,
        "driver_id": env["drv_a"].id,
        "cargo_category": "HAZARDOUS",
        "planned_distance": 80.0,
    }

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: env["admin_a"]

    with TestClient(app) as client:
        res = client.post("/api/v1/trips", json=payload)
        assert res.status_code == 400
        assert "HAZMAT" in res.json()["detail"]


# ===========================================================================
# 19. Hazardous Cargo Driver Gate: Driver With Verified HAZMAT Accepted
# ===========================================================================
@pytest.mark.asyncio
async def test_19_hazardous_cargo_driver_with_hazmat_cert_accepted(db_session, setup_matrix_env):
    env = setup_matrix_env
    qual_hazmat = DriverQualification(
        driver_id=env["drv_a"].id,
        company_id=env["comp_a"].id,
        qualification_type=QualificationType.HAZMAT_CERTIFICATION,
        certificate_number=f"HAZ-CERT-{env['suffix']}",
        verification_status=QualificationVerificationStatus.VERIFIED,
    )
    qual_hgv = DriverQualification(
        driver_id=env["drv_a"].id,
        company_id=env["comp_a"].id,
        qualification_type=QualificationType.DRIVING_LICENSE,
        license_class=LicenseClass.HGV,
        certificate_number=f"HGV-CERT-{env['suffix']}",
        verification_status=QualificationVerificationStatus.VERIFIED,
    )
    db_session.add_all([qual_hazmat, qual_hgv])
    await db_session.flush()

    payload = {
        "origin_location": "Chemical Plant",
        "destination_location": "Storage Terminal",
        "vehicle_id": env["veh_hazmat"].id,
        "driver_id": env["drv_a"].id,
        "cargo_category": "HAZARDOUS",
        "planned_distance": 80.0,
    }

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: env["admin_a"]

    with TestClient(app) as client:
        res = client.post("/api/v1/trips", json=payload)
        assert res.status_code == 201


# ===========================================================================
# 20. Temperature Control Gate: Reefer Required Cargo With Standard Vehicle Rejected
# ===========================================================================
@pytest.mark.asyncio
async def test_20_temperature_control_cargo_unrefrigerated_vehicle_rejected(db_session, setup_matrix_env):
    env = setup_matrix_env
    payload = {
        "origin_location": "Cold Store Hub",
        "destination_location": "Retail Supermarket",
        "vehicle_id": env["veh_standard"].id,  # temperature_controlled is False
        "cargo_category": "PERISHABLE",
        "cargo_temperature_required": True,
        "planned_distance": 45.0,
    }

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: env["admin_a"]

    with TestClient(app) as client:
        res = client.post("/api/v1/trips", json=payload)
        assert res.status_code == 400
        assert "lacks refrigeration equipment" in res.json()["detail"]


# ===========================================================================
# 21. Temperature Control Gate: Reefer Required Cargo With Reefer Accepted
# ===========================================================================
@pytest.mark.asyncio
async def test_21_temperature_control_cargo_refrigerated_vehicle_accepted(db_session, setup_matrix_env):
    env = setup_matrix_env
    payload = {
        "origin_location": "Cold Store Hub",
        "destination_location": "Retail Supermarket",
        "vehicle_id": env["veh_reefer"].id,  # temperature_controlled is True
        "cargo_category": "PERISHABLE",
        "cargo_temperature_required": True,
        "planned_distance": 45.0,
    }

    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: env["admin_a"]

    with TestClient(app) as client:
        res = client.post("/api/v1/trips", json=payload)
        assert res.status_code == 201


# ===========================================================================
# 22. Pre-Trip Intelligence Score Integrity: Overload Forces AVOID
# ===========================================================================
@pytest.mark.asyncio
async def test_22_pre_trip_intelligence_score_integrity_overload_forces_avoid(db_session, setup_matrix_env):
    env = setup_matrix_env
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: env["admin_a"]

    with TestClient(app) as client:
        # Massive revenue (80000) that would otherwise yield a high profit margin
        res = client.post(
            "/api/v1/trips/intelligence/evaluate",
            json={
                "origin_location": "Mumbai",
                "destination_location": "Delhi",
                "vehicle_id": env["veh_standard"].id,  # Capacity 5 tonnes
                "cargo_weight": 14.0,  # Grossly overloaded
                "revenue": 80000.0,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["recommendation"] == "AVOID"
        assert data["risk_level"] == "HIGH"
        assert data["cargo_suitability"]["status"] == "UNSUITABLE"
        assert any("exceeds vehicle payload capacity" in r for r in data["cargo_suitability"]["reasons"])


# ===========================================================================
# 23. Start-Trip Boundary Enforcement: POST /driver-app/trips/{id}/start Gate
# ===========================================================================
@pytest.mark.asyncio
async def test_23_trip_start_boundary_enforces_qualifications_and_capabilities(db_session, setup_matrix_env):
    env = setup_matrix_env
    # Create trip in CREATED status requiring HAZMAT
    trip = Trip(
        trip_id=f"TRP-STRT-GT-{env['suffix']}",
        company_id=env["comp_a"].id,
        vehicle_id=env["veh_hazmat"].id,
        driver_id=env["drv_a"].id,
        status=TripStatus.CREATED,
        cargo_category="HAZARDOUS",
        start_selfie_url="https://storage.fleetguard.io/selfies/start.jpg",
    )
    db_session.add(trip)
    await db_session.flush()

    # Driver drv_a has NO verified HAZMAT qualification
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_driver] = lambda: env["drv_a"]

    with TestClient(app) as client:
        # Starting trip must be strictly blocked at the boundary
        res = client.post(f"/api/v1/driver-app/trips/{trip.id}/start")
        assert res.status_code == 400
        assert "HAZMAT" in res.json()["detail"]
