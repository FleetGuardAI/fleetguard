"""
FleetGuard — Tyre Inventory Valuation & Stock Accounting Integrity Tests
Comprehensive test suite verifying:
1. Tyre with known acquisition cost
2. Tyre with missing acquisition cost
3. Tyre with invalid or negative acquisition cost
4. Inventory values partitioned by lifecycle state
5. Installation does not duplicate acquisition value
6. Rotation does not change acquisition value
7. Retread preserves original casing acquisition cost
8. Retread cost remains separately identifiable
9. Repair cost remains separately identifiable
10. Retirement preserves historical acquisition data
11. Duplicate purchase submission is idempotent
12. Purchase Expense is not duplicated on installation
13. Expense approval behavior follows existing policy (status=PENDING)
14. Unknown-cost tyres are counted without fabricated valuation
15. Cross-company inventory valuation is blocked
16. Date/currency handling follows the existing schema conventions
17. Inventory valuation does not change locked financial totals
18. Integration with Tyre API endpoints
"""

import pytest
import uuid
from datetime import datetime, timezone
from pydantic import ValidationError

from models.tyre_domain import Tyre, TyreStatus, TyreLifecycleRecord, LifecycleEventCategory
from models.vehicle_domain import Vehicle, VehicleStatus
from models.company import Company
from models.user import User, UserRole
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus
from schemas.tyre_domain import TyreCreateRequest
from services.auth_service import get_current_user
from main import app
from services.tyre_service import (
    TyreService,
    InvalidTyreStateTransitionError,
    WheelPositionOccupiedError,
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
async def setup_val_env(db_session):
    """Sets up companies and vehicles for valuation testing."""
    c1 = Company(id=301, company_name="Gamma Freight", owner_name="Owner Gamma", mobile_number="9876543233")
    c2 = Company(id=302, company_name="Delta Haulage", owner_name="Owner Delta", mobile_number="9876543244")
    db_session.add_all([c1, c2])
    await db_session.flush()

    v1 = Vehicle(
        id=401, company_id=301, registration_number="KA-05-AB-1111",
        status=VehicleStatus.ACTIVE, current_odometer=30000.0
    )
    v2 = Vehicle(
        id=402, company_id=301, registration_number="KA-05-CD-2222",
        status=VehicleStatus.ACTIVE, current_odometer=60000.0
    )
    v_c2 = Vehicle(
        id=403, company_id=302, registration_number="MH-14-XY-3333",
        status=VehicleStatus.ACTIVE, current_odometer=10000.0
    )
    db_session.add_all([v1, v2, v_c2])
    await db_session.flush()

    return {"c1": c1, "c2": c2, "v1": v1, "v2": v2, "v_c2": v_c2}


@pytest.mark.asyncio
async def test_01_tyre_with_known_acquisition_cost(db_session, setup_val_env):
    """Scenario 1: Tyre registered with known acquisition cost has typed fields and valuation reflected."""
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    payload = {
        "manufacturer": "Bridgestone",
        "brand": "R156",
        "size": "295/80R22.5",
        "purchase_cost": 15500.50,
        "purchase_currency": "INR",
        "invoice_number": "INV-2026-001",
        "vendor": "Apollo Tyres Depot",
        "purchase_date": "2026-04-10T09:00:00+00:00"
    }
    tyre = await svc.register_tyre("SN-VAL-01", payload, "EVT-REG-01", 301)

    assert tyre.purchase_cost == 15500.50
    assert tyre.purchase_currency == "INR"
    assert tyre.purchase_invoice == "INV-2026-001"
    assert tyre.purchase_vendor == "Apollo Tyres Depot"
    assert tyre.purchase_date is not None
    assert tyre.current_status == TyreStatus.IN_STORAGE

    val = await svc.get_inventory_valuation(301)
    assert val["total_owned_tyres"] == 1
    assert val["total_owned_acquisition_value"] == 15500.50
    assert val["total_known_cost_count"] == 1
    assert val["total_unknown_cost_count"] == 0
    assert val["total_coverage_pct"] == 100.0
    assert val["by_lifecycle_state"]["IN_STORAGE"]["total_acquisition_value"] == 15500.50
    assert val["by_lifecycle_state"]["IN_STORAGE"]["known_cost_count"] == 1


@pytest.mark.asyncio
async def test_02_tyre_with_missing_acquisition_cost(db_session, setup_val_env):
    """Scenario 2: Tyre with missing purchase cost is tracked as unknown-cost without zero-fabrication."""
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    payload = {
        "manufacturer": "Michelin",
        "brand": "X Multi",
        "size": "295/80R22.5"
    }
    tyre = await svc.register_tyre("SN-VAL-NOCOST", payload, "EVT-REG-02", 301)

    assert tyre.purchase_cost is None
    assert tyre.current_status == TyreStatus.IN_STORAGE

    val = await svc.get_inventory_valuation(301)
    assert val["total_owned_tyres"] == 1
    assert val["total_owned_acquisition_value"] == 0.0
    assert val["total_known_cost_count"] == 0
    assert val["total_unknown_cost_count"] == 1
    assert val["total_coverage_pct"] == 0.0
    assert val["by_lifecycle_state"]["IN_STORAGE"]["known_cost_count"] == 0
    assert val["by_lifecycle_state"]["IN_STORAGE"]["unknown_cost_count"] == 1


@pytest.mark.asyncio
async def test_03_tyre_with_invalid_or_negative_acquisition_cost(db_session, setup_val_env):
    """Scenario 3: Negative acquisition costs are rejected by service and schema validation."""
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    # 1. Service rejection
    with pytest.raises(InvalidTyreStateTransitionError) as exc_info:
        await svc.register_tyre("SN-VAL-NEG", {"purchase_cost": -1200.0}, "EVT-NEG", 301)
    assert "Purchase cost cannot be negative" in str(exc_info.value)

    # 2. Schema rejection
    with pytest.raises(ValidationError):
        TyreCreateRequest(serial_number="SN-SCHEMA-NEG", purchase_cost=-50.0)


@pytest.mark.asyncio
async def test_04_inventory_values_partitioned_by_lifecycle_state(db_session, setup_val_env):
    """Scenario 4: Inventory acquisition values correctly partition across all lifecycle states."""
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    # 1. IN_STORAGE (10,000)
    await svc.register_tyre("SN-PART-01", {"purchase_cost": 10000.0}, "EVT-P1", 301)

    # 2. INSTALLED (12,000)
    await svc.register_tyre("SN-PART-02", {"purchase_cost": 12000.0}, "EVT-P2", 301)
    await svc.install_tyre("SN-PART-02", {"vehicle_id": 401, "position": "FL"}, "EVT-P2-INS", 301)

    # 3. RETREADING (14,000)
    await svc.register_tyre("SN-PART-03", {"purchase_cost": 14000.0}, "EVT-P3", 301)
    await svc.install_tyre("SN-PART-03", {"vehicle_id": 401, "position": "FR"}, "EVT-P3-INS", 301)
    await svc.remove_tyre("SN-PART-03", {"target_status": "RETREADING"}, "EVT-P3-REM", 301)

    # 4. IN_REPAIR (16,000)
    await svc.register_tyre("SN-PART-04", {"purchase_cost": 16000.0}, "EVT-P4", 301)
    await svc.install_tyre("SN-PART-04", {"vehicle_id": 401, "position": "RLO"}, "EVT-P4-INS", 301)
    await svc.remove_tyre("SN-PART-04", {"target_status": "IN_REPAIR"}, "EVT-P4-REM", 301)

    # 5. RETIRED (8,000)
    await svc.register_tyre("SN-PART-05", {"purchase_cost": 8000.0}, "EVT-P5", 301)
    await svc.retire_tyre("SN-PART-05", {"reason": "End of life"}, "EVT-P5-RET", 301)

    val = await svc.get_inventory_valuation(301)

    # Active operational assets (excludes RETIRED)
    assert val["total_active_tyres"] == 4
    assert val["total_active_acquisition_value"] == 52000.0  # 10k + 12k + 14k + 16k
    assert val["active_known_cost_count"] == 4

    # Total owned (includes RETIRED)
    assert val["total_owned_tyres"] == 5
    assert val["total_owned_acquisition_value"] == 60000.0  # 52k + 8k
    assert val["total_known_cost_count"] == 5

    # State partitions
    by_state = val["by_lifecycle_state"]
    assert by_state["IN_STORAGE"]["total_acquisition_value"] == 10000.0
    assert by_state["INSTALLED"]["total_acquisition_value"] == 12000.0
    assert by_state["RETREADING"]["total_acquisition_value"] == 14000.0
    assert by_state["IN_REPAIR"]["total_acquisition_value"] == 16000.0
    assert by_state["RETIRED"]["total_acquisition_value"] == 8000.0


@pytest.mark.asyncio
async def test_05_installation_does_not_duplicate_acquisition_value(db_session, setup_val_env):
    """Scenario 5: Installing a tyre moves its valuation between states without duplicating cost."""
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    # 1. Registered in IN_STORAGE
    tyre = await svc.register_tyre("SN-INST-VAL", {"purchase_cost": 12500.0}, "EVT-INST-01", 301)
    val_before = await svc.get_inventory_valuation(301)
    assert val_before["by_lifecycle_state"]["IN_STORAGE"]["total_acquisition_value"] == 12500.0
    assert val_before["by_lifecycle_state"]["INSTALLED"]["total_acquisition_value"] == 0.0
    assert val_before["total_active_acquisition_value"] == 12500.0

    # 2. Installed on vehicle
    await svc.install_tyre("SN-INST-VAL", {"vehicle_id": 401, "position": "FL"}, "EVT-INST-02", 301)
    val_after = await svc.get_inventory_valuation(301)
    assert val_after["by_lifecycle_state"]["IN_STORAGE"]["total_acquisition_value"] == 0.0
    assert val_after["by_lifecycle_state"]["INSTALLED"]["total_acquisition_value"] == 12500.0
    assert val_after["total_active_acquisition_value"] == 12500.0  # Exactly preserved, not 25,000


@pytest.mark.asyncio
async def test_06_rotation_does_not_change_acquisition_value(db_session, setup_val_env):
    """Scenario 6: Rotating or swapping wheel positions preserves asset valuation intact."""
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    await svc.register_tyre("SN-ROT-01", {"purchase_cost": 13000.0}, "EVT-R1", 301)
    await svc.install_tyre("SN-ROT-01", {"vehicle_id": 401, "position": "FL"}, "EVT-R1-INS", 301)

    # Rotate to vacant position FR
    await svc.rotate_tyre("SN-ROT-01", {"new_position": "FR"}, "EVT-R1-ROT", 301)
    val = await svc.get_inventory_valuation(301)

    assert val["by_lifecycle_state"]["INSTALLED"]["total_acquisition_value"] == 13000.0
    assert val["total_active_acquisition_value"] == 13000.0


@pytest.mark.asyncio
async def test_07_retread_preserves_original_casing_acquisition_cost(db_session, setup_val_env):
    """Scenario 7: Retreading resets wear cycle but preserves historical casing purchase cost."""
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    await svc.register_tyre("SN-RET-VAL", {"purchase_cost": 14000.0}, "EVT-RET-REG", 301)
    tyre_retreaded = await svc.retread_tyre(
        "SN-RET-VAL",
        {"cost": 3500.0, "vendor": "Bandag", "tread_depth_mm": 12.0},
        "EVT-RET-01",
        301
    )

    assert tyre_retreaded.purchase_cost == 14000.0  # Casing cost unchanged
    assert tyre_retreaded.retread_count == 1
    assert tyre_retreaded.current_status == TyreStatus.IN_STORAGE

    val = await svc.get_inventory_valuation(301)
    # The casing acquisition value remains 14,000 in IN_STORAGE
    assert val["by_lifecycle_state"]["IN_STORAGE"]["total_acquisition_value"] == 14000.0


@pytest.mark.asyncio
async def test_08_retread_cost_remains_separately_identifiable(db_session, setup_val_env):
    """Scenario 8: Retread service cost is tracked in Expense ledger and reported separately."""
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    await svc.register_tyre("SN-RET-EXP", {"purchase_cost": 14000.0}, "EVT-R-REG", 301)
    await svc.retread_tyre("SN-RET-EXP", {"cost": 3800.0, "vendor": "TyreSol"}, "EVT-R-PROC", 301)

    val = await svc.get_inventory_valuation(301)
    assert val["total_active_acquisition_value"] == 14000.0  # Asset cost
    assert val["total_retread_expenditure"] == 3800.0        # Service expense

    # Verify Expense record in canonical ledger
    exp = await uow.repositories.expense.get_expense_by_business_id("EXP-TYRE-RETREAD-SN-RET-EXP-1")
    assert exp is not None
    assert exp.amount == 3800.0
    assert exp.category == ExpenseCategory.TYRE
    assert exp.status == ExpenseStatus.PENDING  # Requires approval


@pytest.mark.asyncio
async def test_09_repair_cost_remains_separately_identifiable(db_session, setup_val_env):
    """Scenario 9: Tyre puncture/patch repair expense is separately tracked in Expense ledger."""
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    await svc.register_tyre("SN-REP-VAL", {"purchase_cost": 11000.0}, "EVT-REP-REG", 301)
    await svc.repair_tyre("SN-REP-VAL", {"cost": 450.0, "repair_type": "PUNCTURE"}, "EVT-REP-01", 301)

    val = await svc.get_inventory_valuation(301)
    assert val["total_active_acquisition_value"] == 11000.0  # Asset cost unchanged
    assert val["total_repair_expenditure"] == 450.0          # Recognized repair expense

    exp = await uow.repositories.expense.get_expense_by_business_id("EXP-TYRE-REPAIR-SN-REP-VAL-EVT-REP-01")
    assert exp is not None
    assert exp.amount == 450.0
    assert exp.category == ExpenseCategory.TYRE
    assert exp.status == ExpenseStatus.PENDING  # Governed by approval policy


@pytest.mark.asyncio
async def test_10_retirement_preserves_historical_acquisition_data(db_session, setup_val_env):
    """Scenario 10: Retiring a tyre excludes it from active assets but preserves historical cost."""
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    tyre = await svc.register_tyre("SN-RET-HIST", {"purchase_cost": 15000.0}, "EVT-RH-REG", 301)
    await svc.retire_tyre("SN-RET-HIST", {"reason": "Tread worn out, casing non-retreadable"}, "EVT-RH-RET", 301)

    assert tyre.current_status == TyreStatus.RETIRED
    assert tyre.purchase_cost == 15000.0  # Historical cost preserved

    val = await svc.get_inventory_valuation(301)
    assert val["total_active_tyres"] == 0
    assert val["total_active_acquisition_value"] == 0.0
    assert val["total_owned_tyres"] == 1
    assert val["total_owned_acquisition_value"] == 15000.0
    assert val["by_lifecycle_state"]["RETIRED"]["total_acquisition_value"] == 15000.0


@pytest.mark.asyncio
async def test_11_duplicate_purchase_submission_is_idempotent(db_session, setup_val_env):
    """Scenario 11: Duplicate purchase submission updates specs idempotently without duplicate expenses."""
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    payload = {
        "manufacturer": "Bridgestone",
        "purchase_cost": 17000.0,
        "record_purchase_expense": True
    }
    # Submission 1
    t1 = await svc.register_tyre("SN-IDEMP-01", payload, "EVT-IDEMP-1", 301)
    # Submission 2 (retry)
    t2 = await svc.register_tyre("SN-IDEMP-01", payload, "EVT-IDEMP-2", 301)

    assert t1.id == t2.id
    val = await svc.get_inventory_valuation(301)
    assert val["total_owned_tyres"] == 1
    assert val["total_owned_acquisition_value"] == 17000.0

    # Verify only 1 purchase expense exists
    exp = await uow.repositories.expense.get_expense_by_business_id("EXP-TYRE-PURCHASE-SN-IDEMP-01")
    assert exp is not None
    assert exp.amount == 17000.0


@pytest.mark.asyncio
async def test_12_purchase_expense_not_duplicated_on_installation(db_session, setup_val_env):
    """Scenario 12: Installing a previously purchased tyre does NOT create a secondary Expense."""
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    # 1. Purchase receipt creates single pending purchase expense
    await svc.register_tyre(
        "SN-P-INST-01",
        {"purchase_cost": 16000.0, "record_purchase_expense": True},
        "EVT-PI-1",
        301
    )
    # 2. Tyre is subsequently mounted on vehicle
    await svc.install_tyre("SN-P-INST-01", {"vehicle_id": 401, "position": "FL"}, "EVT-PI-2", 301)

    # Verify no additional expense created
    all_expenses = await uow.repositories.expense.search_expenses(company_id=301)
    tyre_expenses = [e for e in all_expenses if "SN-P-INST-01" in e.business_id]
    assert len(tyre_expenses) == 1
    assert tyre_expenses[0].business_id == "EXP-TYRE-PURCHASE-SN-P-INST-01"


@pytest.mark.asyncio
async def test_13_expense_approval_behavior_follows_existing_policy(db_session, setup_val_env):
    """Scenario 13: All operational tyre expenses (purchase, retread, repair) enter as PENDING."""
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    # 1. Purchase
    await svc.register_tyre("SN-EXP-POL", {"purchase_cost": 15000.0, "record_purchase_expense": True}, "EVT-EP-1", 301)
    exp_p = await uow.repositories.expense.get_expense_by_business_id("EXP-TYRE-PURCHASE-SN-EXP-POL")
    assert exp_p.status == ExpenseStatus.PENDING

    # 2. Retread
    await svc.retread_tyre("SN-EXP-POL", {"cost": 3000.0, "vendor": "MRF"}, "EVT-EP-2", 301)
    exp_r = await uow.repositories.expense.get_expense_by_business_id("EXP-TYRE-RETREAD-SN-EXP-POL-1")
    assert exp_r.status == ExpenseStatus.PENDING

    # 3. Repair
    await svc.repair_tyre("SN-EXP-POL", {"cost": 350.0}, "EVT-EP-3", 301)
    exp_rep = await uow.repositories.expense.get_expense_by_business_id("EXP-TYRE-REPAIR-SN-EXP-POL-EVT-EP-3")
    assert exp_rep.status == ExpenseStatus.PENDING


@pytest.mark.asyncio
async def test_14_unknown_cost_tyres_counted_without_fabricated_valuation(db_session, setup_val_env):
    """Scenario 14: 1 tyre with known cost and 2 without are counted transparently without price guessing."""
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    # 1 known cost
    await svc.register_tyre("SN-KNOWN-1", {"purchase_cost": 21000.0}, "EVT-K1", 301)
    # 2 unknown costs
    await svc.register_tyre("SN-UNKN-1", {}, "EVT-U1", 301)
    await svc.register_tyre("SN-UNKN-2", {}, "EVT-U2", 301)

    val = await svc.get_inventory_valuation(301)
    assert val["total_owned_tyres"] == 3
    assert val["total_owned_acquisition_value"] == 21000.0  # Does NOT fabricate (e.g. 21k * 3 = 63k)
    assert val["total_known_cost_count"] == 1
    assert val["total_unknown_cost_count"] == 2
    assert val["total_coverage_pct"] == 33.33


@pytest.mark.asyncio
async def test_15_cross_company_inventory_valuation_is_blocked(db_session, setup_val_env):
    """Scenario 15: Tenant isolation ensures Company A and Company B valuations are completely segregated."""
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    # Company 301 tyres
    await svc.register_tyre("SN-CO-A1", {"purchase_cost": 10000.0}, "EVT-A1", 301)
    await svc.register_tyre("SN-CO-A2", {"purchase_cost": 15000.0}, "EVT-A2", 301)

    # Company 302 tyres
    await svc.register_tyre("SN-CO-B1", {"purchase_cost": 18000.0}, "EVT-B1", 302)

    val_a = await svc.get_inventory_valuation(301)
    assert val_a["total_owned_tyres"] == 2
    assert val_a["total_owned_acquisition_value"] == 25000.0
    assert val_a["total_known_cost_count"] == 2

    val_b = await svc.get_inventory_valuation(302)
    assert val_b["total_owned_tyres"] == 1
    assert val_b["total_owned_acquisition_value"] == 18000.0
    assert val_b["total_known_cost_count"] == 1


@pytest.mark.asyncio
async def test_16_date_and_currency_handling_schema_conventions(db_session, setup_val_env):
    """Scenario 16: Purchase date and currency adhere to standard schema parsing and timezone conventions."""
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    payload = {
        "purchase_cost": 19500.0,
        "purchase_currency": "INR",
        "purchase_date": "2026-06-20T14:30:00+00:00",
        "invoice_number": "TAX-INV-999"
    }
    tyre = await svc.register_tyre("SN-CURR-01", payload, "EVT-C1", 301)

    assert tyre.purchase_currency == "INR"
    assert tyre.purchase_invoice == "TAX-INV-999"
    assert tyre.purchase_date.year == 2026
    assert tyre.purchase_date.month == 6


@pytest.mark.asyncio
async def test_17_inventory_valuation_does_not_change_locked_financial_totals(db_session, setup_val_env):
    """Scenario 17: Inventory acquisition value does NOT alter canonical approved expenses."""
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    # Existing operational expenses
    exp1 = Expense(
        business_id="EXP-FUEL-EXISTING",
        category=ExpenseCategory.FUEL,
        amount=5000.0,
        status=ExpenseStatus.APPROVED,
        expense_date=datetime.now(timezone.utc),
        company_id=301,
        origin_type="verified_event",
        origin_id="EVT-F1"
    )
    exp2 = Expense(
        business_id="EXP-MAINT-EXISTING",
        category=ExpenseCategory.MAINTENANCE,
        amount=3000.0,
        status=ExpenseStatus.APPROVED,
        expense_date=datetime.now(timezone.utc),
        company_id=301,
        origin_type="verified_event",
        origin_id="EVT-M1"
    )
    db_session.add_all([exp1, exp2])
    await db_session.flush()

    # Register & install tyres worth 30,000
    await svc.register_tyre("SN-FIN-01", {"purchase_cost": 15000.0}, "EVT-F-REG-1", 301)
    await svc.register_tyre("SN-FIN-02", {"purchase_cost": 15000.0}, "EVT-F-REG-2", 301)
    await svc.install_tyre("SN-FIN-01", {"vehicle_id": 401, "position": "FL"}, "EVT-F-INS-1", 301)

    # Check valuation
    val = await svc.get_inventory_valuation(301)
    assert val["total_active_acquisition_value"] == 30000.0

    # Check canonical Expense ledger: approved expenses remain strictly 8,000 (5k + 3k)
    all_approved = await uow.repositories.expense.search_expenses(status=ExpenseStatus.APPROVED, company_id=301)
    total_approved = sum(e.amount for e in all_approved)
    assert total_approved == 8000.0


@pytest.mark.asyncio
async def test_18_tyre_valuation_api_endpoint(client, db_session, setup_val_env):
    """Scenario 18: GET /api/v1/tyres/inventory/valuation returns full schema payload via HTTP."""
    uow = DirectUoW(db_session)
    svc = TyreService(uow)

    user = User(
        id=701, email="admin@gamma.com", company_id=301,
        full_name="Admin Gamma", mobile_number="9111111133",
        password_hash="mock_hash", role=UserRole.COMPANY_ADMIN, is_active=True
    )
    db_session.add(user)
    await db_session.flush()

    await svc.register_tyre("SN-API-VAL-1", {"purchase_cost": 12000.0}, "EVT-API-1", 301)
    await svc.register_tyre("SN-API-VAL-2", {}, "EVT-API-2", 301)

    app.dependency_overrides[get_current_user] = lambda: user
    try:
        resp = client.get("/api/v1/tyres/inventory/valuation")
        assert resp.status_code == 200
        data = resp.json()

        assert data["valuation_method"] == "KNOWN_ACQUISITION_COST"
        assert data["currency"] == "INR"
        assert data["total_owned_tyres"] == 2
        assert data["total_owned_acquisition_value"] == 12000.0
        assert data["total_known_cost_count"] == 1
        assert data["total_unknown_cost_count"] == 1
        assert data["total_coverage_pct"] == 50.0
        assert "by_lifecycle_state" in data
        assert "IN_STORAGE" in data["by_lifecycle_state"]
        assert data["by_lifecycle_state"]["IN_STORAGE"]["total_acquisition_value"] == 12000.0
    finally:
        app.dependency_overrides.pop(get_current_user, None)

