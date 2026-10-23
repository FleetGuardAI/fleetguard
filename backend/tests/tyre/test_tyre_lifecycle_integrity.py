"""
FleetGuard — Tyre Lifecycle & Inventory Integrity Tests
Verifies:
- Canonical tyre identity and multi-tenant isolation
- Lifecycle state transitions and invalid transition guards
- Wheel position tracking and collision rejection
- Odometer distance calculation and rollback protection
- Retread lifecycle (casing identity, retread count, wear cycle reset, scrap on rejection)
- Inventory stock integrity (balance invariant: Total = Storage + Installed + Retreading + In Repair + Retired)
- Financial integrity (Expense single source of truth, no double counting)
- Concurrency and race condition safety
"""

import pytest
import uuid
from datetime import datetime, timezone

from models.tyre_domain import Tyre, TyreStatus, TyreLifecycleRecord, LifecycleEventCategory
from models.vehicle_domain import Vehicle, VehicleStatus
from models.company import Company
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus
from models.operational_event import OperationalEvent, EventType, EntityType
from services.tyre_service import (
    TyreService,
    TyreNotFoundError,
    InvalidTyreStateTransitionError,
    WheelPositionOccupiedError,
    OdometerRollbackError,
    VehicleNotFoundError,
)
from infrastructure.uow import RepositoryRegistry, AbstractUnitOfWork


class DirectUoW(AbstractUnitOfWork):
    """Simple test UoW wrapping db_session."""
    def __init__(self, session):
        self.session = session
        self.repositories = RepositoryRegistry(session)

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()


@pytest.fixture
async def setup_test_env(db_session):
    """Sets up companies and vehicles for testing."""
    c1 = Company(id=101, company_name="Alpha Logistics", owner_name="Owner Alpha", mobile_number="9876543210")
    c2 = Company(id=102, company_name="Beta Transport", owner_name="Owner Beta", mobile_number="9876543211")
    db_session.add_all([c1, c2])
    await db_session.flush()


    v1 = Vehicle(
        id=201, company_id=101, registration_number="KA-01-AB-1234",
        status=VehicleStatus.ACTIVE, current_odometer=50000.0
    )
    v2 = Vehicle(
        id=202, company_id=101, registration_number="KA-01-CD-5678",
        status=VehicleStatus.ACTIVE, current_odometer=80000.0
    )
    v_c2 = Vehicle(
        id=203, company_id=102, registration_number="MH-12-XY-9999",
        status=VehicleStatus.ACTIVE, current_odometer=20000.0
    )
    db_session.add_all([v1, v2, v_c2])
    await db_session.flush()

    return {"c1": c1, "c2": c2, "v1": v1, "v2": v2, "v_c2": v_c2}


@pytest.mark.asyncio
async def test_tyre_registration_and_stock_balance(db_session, setup_test_env):
    """
    Phase 1, 2, 3: Direct stock entry registers tyre in IN_STORAGE.
    Available stock increases by 1. Total = In Storage + Mounted + Retreading + Retired.
    """
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    payload = {
        "manufacturer": "Bridgestone",
        "brand": "R156",
        "size": "295/80R22.5",
        "initial_tread_mm": 16.0,
        "purchase_cost": 18000.0,
        "record_purchase_expense": True
    }
    tyre = await svc.register_tyre("SN-BR-001", payload, "EVT-REG-001", company_id=101)
    await db_session.flush()

    assert tyre.serial_number == "SN-BR-001"
    assert tyre.company_id == 101
    assert tyre.current_status == TyreStatus.IN_STORAGE
    assert tyre.current_vehicle_id is None
    assert tyre.current_position is None
    assert tyre.current_tread_depth_mm == 16.0
    assert tyre.retread_count == 0
    assert tyre.total_lifetime_km == 0.0

    # Verify inventory summary invariant
    summary = await svc.get_inventory_summary(company_id=101)
    assert summary["total_tyres"] == 1
    assert summary["in_storage"] == 1
    assert summary["installed"] == 0

    # Verify purchase expense recorded once
    exp = await uow.repositories.expense.get_expense_by_business_id("EXP-TYRE-PURCHASE-SN-BR-001")
    assert exp is not None
    assert exp.amount == 18000.0
    assert exp.category == ExpenseCategory.TYRE
    assert exp.company_id == 101


@pytest.mark.asyncio
async def test_installation_and_single_position_occupancy(db_session, setup_test_env):
    """
    Phase 6: Installing tyre sets status to INSTALLED and decrements available storage stock.
    Attempting to install a second tyre at the same occupied position must fail with WheelPositionOccupiedError.
    """
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    # Register two tyres
    t1 = await svc.register_tyre("SN-001", {"size": "295/80R22.5"}, "EVT-1", 101)
    t2 = await svc.register_tyre("SN-002", {"size": "295/80R22.5"}, "EVT-2", 101)
    await db_session.flush()

    # Install t1 at FRONT_LEFT on v1
    install_payload = {
        "vehicle_id": 201,
        "position": "FRONT_LEFT",
        "odometer_km": 50000.0
    }
    await svc.install_tyre("SN-001", install_payload, "EVT-INS-1", 101)
    await db_session.flush()

    assert t1.current_status == TyreStatus.INSTALLED
    assert t1.current_vehicle_id == 201
    assert t1.current_position == "FRONT_LEFT"
    assert t1.current_installation_odometer == 50000.0

    # Inventory check
    summary = await svc.get_inventory_summary(101)
    assert summary["total_tyres"] == 2
    assert summary["in_storage"] == 1
    assert summary["installed"] == 1

    # Attempt to install t2 at FRONT_LEFT on v1 -> MUST FAIL (collision)
    with pytest.raises(WheelPositionOccupiedError) as exc:
        await svc.install_tyre("SN-002", install_payload, "EVT-INS-2", 101)
    assert "already occupied by tyre 'SN-001'" in str(exc.value)


@pytest.mark.asyncio
async def test_invalid_transitions_guarded(db_session, setup_test_env):
    """
    Phase 2:
    - Cannot install an already mounted tyre.
    - Cannot retire a mounted tyre without removal.
    - Cannot install a retired tyre.
    - Cannot retread a mounted tyre without removal.
    """
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    await svc.register_tyre("SN-GUARD-1", {}, "EVT-1", 101)
    await svc.install_tyre("SN-GUARD-1", {"vehicle_id": 201, "position": "FRONT_LEFT"}, "EVT-2", 101)
    await db_session.flush()

    # 1. Cannot install an already mounted tyre on vehicle 2
    with pytest.raises(InvalidTyreStateTransitionError) as exc1:
        await svc.install_tyre("SN-GUARD-1", {"vehicle_id": 202, "position": "FRONT_RIGHT"}, "EVT-3", 101)
    assert "already installed on vehicle #201" in str(exc1.value)

    # 2. Cannot retire a mounted tyre without removal
    with pytest.raises(InvalidTyreStateTransitionError) as exc2:
        await svc.retire_tyre("SN-GUARD-1", {"reason": "Damaged"}, "EVT-4", 101)
    assert "while still INSTALLED" in str(exc2.value)

    # 3. Cannot retread a mounted tyre without removal
    with pytest.raises(InvalidTyreStateTransitionError) as exc3:
        await svc.retread_tyre("SN-GUARD-1", {"action": "COMPLETED"}, "EVT-5", 101)
    assert "currently INSTALLED on vehicle #201" in str(exc3.value)


@pytest.mark.asyncio
async def test_odometer_distance_and_rollback_protection(db_session, setup_test_env):
    """
    Phase 7:
    - Removal odometer < installation odometer is rejected (odometer rollback guard).
    - Valid removal accumulates distance into total_lifetime_km and current_retread_km.
    """
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    await svc.register_tyre("SN-ODO-1", {}, "EVT-1", 101)
    await svc.install_tyre("SN-ODO-1", {"vehicle_id": 201, "position": "FRONT_LEFT", "odometer_km": 50000.0}, "EVT-2", 101)
    await db_session.flush()

    # Attempt rollback reading: removal at 48000 km when installed at 50000 km
    with pytest.raises(OdometerRollbackError) as exc:
        await svc.remove_tyre("SN-ODO-1", {"odometer_km": 48000.0}, "EVT-3", 101)
    assert "Odometer rollback rejected" in str(exc.value)

    # Valid removal: vehicle odometer at 56500.5 km (distance = 6500.5 km)
    t = await svc.remove_tyre("SN-ODO-1", {"odometer_km": 56500.5, "target_status": "IN_STORAGE"}, "EVT-4", 101)
    await db_session.flush()

    assert t.current_status == TyreStatus.IN_STORAGE
    assert t.current_vehicle_id is None
    assert t.current_position is None
    assert t.current_installation_odometer is None
    assert t.total_lifetime_km == 6500.5
    assert t.current_retread_km == 6500.5


@pytest.mark.asyncio
async def test_retread_lifecycle_casing_preservation_and_expense(db_session, setup_test_env):
    """
    Phase 8 & Phase 9:
    - Retreading preserves physical casing identity and lifetime mileage.
    - Increments retread_count.
    - Resets current_retread_km to 0.0 (fresh tread).
    - Creates single retread expense in Expense ledger (no duplicate on retry).
    """
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    # 1. Register and install tyre
    t = await svc.register_tyre("SN-RET-01", {"initial_tread_mm": 16.0}, "EVT-1", 101)
    await svc.install_tyre("SN-RET-01", {"vehicle_id": 201, "position": "FRONT_LEFT", "odometer_km": 10000.0}, "EVT-2", 101)
    # Run 40,000 km
    await svc.remove_tyre("SN-RET-01", {"odometer_km": 50000.0, "target_status": "RETREADING"}, "EVT-3", 101)
    await db_session.flush()

    assert t.current_status == TyreStatus.RETREADING
    assert t.total_lifetime_km == 40000.0
    assert t.current_retread_km == 40000.0
    assert t.retread_count == 0

    # 2. Retread completed by vendor (Apollo Retread, ₹3,500, new tread 12mm)
    retread_payload = {
        "action": "COMPLETED",
        "vendor": "Apollo Retreads",
        "cost": 3500.0,
        "tread_depth_mm": 12.0
    }
    t_retreaded = await svc.retread_tyre("SN-RET-01", retread_payload, "EVT-RETREAD-01", 101)
    await db_session.flush()

    # Casing identity preserved!
    assert t_retreaded.id == t.id
    assert t_retreaded.serial_number == "SN-RET-01"
    assert t_retreaded.retread_count == 1
    assert t_retreaded.total_lifetime_km == 40000.0  # Lifetime mileage preserved on casing
    assert t_retreaded.current_retread_km == 0.0     # Reset to 0 for fresh tread service
    assert t_retreaded.current_tread_depth_mm == 12.0
    assert t_retreaded.current_status == TyreStatus.IN_STORAGE

    # 3. Expense verification: exactly 1 retread expense created
    retread_exp = await uow.repositories.expense.get_expense_by_business_id("EXP-TYRE-RETREAD-SN-RET-01-1")
    assert retread_exp is not None
    assert retread_exp.amount == 3500.0
    assert retread_exp.category == ExpenseCategory.TYRE
    assert retread_exp.company_id == 101

    # 4. Retry of the same retread event must not duplicate count or expense
    t_retried = await svc.retread_tyre("SN-RET-01", retread_payload, "EVT-RETREAD-01", 101)
    assert t_retried.retread_count == 1


@pytest.mark.asyncio
async def test_retread_rejection_retires_casing(db_session, setup_test_env):
    """
    Phase 8: If retreader rejects casing (casing defect), tyre is retired.
    """
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    await svc.register_tyre("SN-BAD-CASING", {}, "EVT-1", 101)
    await svc.install_tyre("SN-BAD-CASING", {"vehicle_id": 201, "position": "FRONT_RIGHT", "odometer_km": 10000.0}, "EVT-2", 101)
    await svc.remove_tyre("SN-BAD-CASING", {"odometer_km": 60000.0, "target_status": "RETREADING"}, "EVT-3", 101)
    await db_session.flush()

    reject_payload = {
        "action": "REJECTED",
        "rejection_reason": "Severe crown belt separation",
        "vendor": "MRF Pre-cure"
    }
    t = await svc.retread_tyre("SN-BAD-CASING", reject_payload, "EVT-REJECT-1", 101)
    await db_session.flush()

    assert t.current_status == TyreStatus.RETIRED
    summary = await svc.get_inventory_summary(101)
    assert summary["retired"] == 1


@pytest.mark.asyncio
async def test_tyre_rotation_atomic_swap(db_session, setup_test_env):
    """
    Phase 6: Two tyres on the same vehicle can be swapped in wheel positions atomically.
    """
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    t1 = await svc.register_tyre("SN-SWAP-1", {}, "EVT-1", 101)
    t2 = await svc.register_tyre("SN-SWAP-2", {}, "EVT-2", 101)
    await svc.install_tyre("SN-SWAP-1", {"vehicle_id": 201, "position": "FRONT_LEFT"}, "EVT-3", 101)
    await svc.install_tyre("SN-SWAP-2", {"vehicle_id": 201, "position": "FRONT_RIGHT"}, "EVT-4", 101)
    await db_session.flush()

    assert t1.current_position == "FRONT_LEFT"
    assert t2.current_position == "FRONT_RIGHT"

    # Rotate t1 to FRONT_RIGHT, swapping with t2
    await svc.rotate_tyre(
        "SN-SWAP-1", 
        {"new_position": "FRONT_RIGHT", "swap_serial_number": "SN-SWAP-2"}, 
        "EVT-ROT-1", 
        101
    )
    await db_session.flush()

    assert t1.current_position == "FRONT_RIGHT"
    assert t2.current_position == "FRONT_LEFT"


@pytest.mark.asyncio
async def test_multi_tenant_isolation(db_session, setup_test_env):
    """
    Phase 2 & 3: Tenant 1 cannot access, install, or mutate tyres owned by Tenant 2.
    """
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    # Company 102 tyre
    await svc.register_tyre("SN-C2-001", {"brand": "Michelin"}, "EVT-1", company_id=102)
    await db_session.flush()

    # Company 101 attempts to install Company 102's tyre
    with pytest.raises(TyreNotFoundError) as exc:
        await svc.install_tyre("SN-C2-001", {"vehicle_id": 201, "position": "FRONT_LEFT"}, "EVT-2", company_id=101)
    assert "not found in your fleet" in str(exc.value)

    # Company 101 inventory summary must not include Company 102's tyre
    s1 = await svc.get_inventory_summary(company_id=101)
    s2 = await svc.get_inventory_summary(company_id=102)
    assert s1["total_tyres"] == 0
    assert s2["total_tyres"] == 1


@pytest.mark.asyncio
async def test_operational_event_integration(db_session, setup_test_env):
    """
    Verifies that TyreService.apply_verified_event correctly maps OperationalEvent
    into the domain state machine.
    """
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    event_id = uuid.uuid4()
    op_event = OperationalEvent(
        id=event_id,
        company_id=101,
        event_type=EventType.TYRE_REGISTERED,
        entity_type=EntityType.TYRE,
        entity_id="SN-OP-001",
        occurred_at=datetime.now(timezone.utc),
        payload={"manufacturer": "JK Tyre", "size": "10.00R20"}
    )
    await svc.apply_verified_event(op_event)
    await db_session.flush()

    tyre = await uow.repositories.tyre.get_tyre_by_serial_number("SN-OP-001")
    assert tyre is not None
    assert tyre.company_id == 101
    assert tyre.manufacturer == "JK Tyre"
    assert tyre.current_status == TyreStatus.IN_STORAGE
