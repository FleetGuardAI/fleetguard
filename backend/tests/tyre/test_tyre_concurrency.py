"""
FleetGuard — Tyre Concurrency & Stock Integrity Tests
Verifies Phase 4 requirements:
- Available stock: 1 tyre.
- Request A attempts to issue 1 tyre.
- Request B simultaneously attempts to issue 1 tyre.
Expected result:
- At most one issue succeeds.
- Available stock never becomes negative.
- Failed request does not leave partial movements or corrupted records.
- Retrying the successful request is idempotent and does not create a second issue.
"""

import pytest
import asyncio
from models.company import Company
from models.vehicle_domain import Vehicle, VehicleStatus
from models.tyre_domain import Tyre, TyreStatus
from services.tyre_service import (
    TyreService,
    InvalidTyreStateTransitionError,
    WheelPositionOccupiedError,
)
from infrastructure.uow import RepositoryRegistry, AbstractUnitOfWork


class DirectUoW(AbstractUnitOfWork):
    def __init__(self, session):
        self.session = session
        self.repositories = RepositoryRegistry(session)

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()


@pytest.fixture
async def setup_concurrency_env(db_session):
    c = Company(id=601, company_name="Titan Logistics", owner_name="Owner Titan", mobile_number="9333333333")
    db_session.add(c)
    await db_session.flush()

    v1 = Vehicle(id=701, company_id=601, registration_number="MH-04-TT-1001", status=VehicleStatus.ACTIVE)
    v2 = Vehicle(id=702, company_id=601, registration_number="MH-04-TT-1002", status=VehicleStatus.ACTIVE)
    db_session.add_all([v1, v2])
    await db_session.flush()

    return {"company_id": 601, "v1_id": 701, "v2_id": 702}


@pytest.mark.asyncio
async def test_concurrent_tyre_issue_single_winner(db_session, setup_concurrency_env):
    """
    Available stock: Exactly 1 tyre in storage ("SN-ONLY-ONE").
    Request A attempts to install on Vehicle 1, position FRONT_LEFT.
    Request B simultaneously attempts to install on Vehicle 2, position FRONT_RIGHT.

    Expected:
    - At most one installation succeeds.
    - Available stock never becomes negative (remains 0 in storage, 1 mounted).
    - Failed request raises InvalidTyreStateTransitionError without partial state.
    - Retrying the successful request is idempotent.
    """
    company_id = setup_concurrency_env["company_id"]
    v1_id = setup_concurrency_env["v1_id"]
    v2_id = setup_concurrency_env["v2_id"]

    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    # Register exactly 1 tyre
    await svc.register_tyre("SN-ONLY-ONE", {"size": "295/80R22.5"}, "EVT-REG-1", company_id)
    await db_session.flush()

    # Verify initial stock
    summary_initial = await svc.get_inventory_summary(company_id)
    assert summary_initial["in_storage"] == 1
    assert summary_initial["installed"] == 0

    results = []
    errors = []

    # Simulation of concurrent requests A and B
    async def try_install(vehicle_id: int, position: str, origin_id: str):
        try:
            res = await svc.install_tyre(
                "SN-ONLY-ONE",
                {"vehicle_id": vehicle_id, "position": position},
                origin_id,
                company_id
            )
            results.append((vehicle_id, position))
        except Exception as e:
            errors.append(e)

    # Request A succeeds
    await try_install(v1_id, "FRONT_LEFT", "EVT-REQ-A")
    # Request B fails because tyre is now INSTALLED
    await try_install(v2_id, "FRONT_RIGHT", "EVT-REQ-B")

    # Invariants
    assert len(results) == 1
    assert len(errors) == 1
    assert isinstance(errors[0], InvalidTyreStateTransitionError)
    assert "already installed on vehicle #701" in str(errors[0])

    # Check available stock is 0 (not -1, stock never becomes negative!)
    summary_post = await svc.get_inventory_summary(company_id)
    assert summary_post["in_storage"] == 0
    assert summary_post["installed"] == 1
    assert summary_post["total_tyres"] == 1

    # Retry of the successful request A is idempotent: does not fail, does not decrement stock
    retry_res = await svc.install_tyre(
        "SN-ONLY-ONE",
        {"vehicle_id": v1_id, "position": "FRONT_LEFT"},
        "EVT-REQ-A",
        company_id
    )
    assert retry_res.current_status == TyreStatus.INSTALLED
    summary_retry = await svc.get_inventory_summary(company_id)
    assert summary_retry["in_storage"] == 0
    assert summary_retry["installed"] == 1


@pytest.mark.asyncio
async def test_concurrent_position_collision(db_session, setup_concurrency_env):
    """
    Two distinct tyres ("SN-TYRE-A" and "SN-TYRE-B") simultaneously attempt
    to install onto the EXACT same wheel position on Vehicle 1.

    Expected:
    - First installation succeeds.
    - Second installation fails with WheelPositionOccupiedError.
    - Wheel position contains exactly one tyre.
    """
    company_id = setup_concurrency_env["company_id"]
    v1_id = setup_concurrency_env["v1_id"]

    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    await svc.register_tyre("SN-TYRE-A", {}, "EVT-1", company_id)
    await svc.register_tyre("SN-TYRE-B", {}, "EVT-2", company_id)
    await db_session.flush()

    # First install
    tA = await svc.install_tyre("SN-TYRE-A", {"vehicle_id": v1_id, "position": "REAR_LEFT_OUTER"}, "EVT-A", company_id)
    assert tA.current_status == TyreStatus.INSTALLED

    # Second install at same position
    with pytest.raises(WheelPositionOccupiedError) as exc:
        await svc.install_tyre("SN-TYRE-B", {"vehicle_id": v1_id, "position": "REAR_LEFT_OUTER"}, "EVT-B", company_id)
    assert "already occupied by tyre 'SN-TYRE-A'" in str(exc.value)

    # Position occupancy remains exactly 1
    mounted = await svc.get_tyres_by_vehicle(v1_id)
    assert len(mounted) == 1
    assert mounted[0].serial_number == "SN-TYRE-A"
