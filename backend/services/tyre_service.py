"""
FleetGuard — Tyre Service
Domain service orchestrating business rules for Tyre Management,
Inventory Integrity, Retread Lifecycle, and Financial Ledger integration.
"""

from typing import Optional, Sequence, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from infrastructure.uow import AbstractUnitOfWork
from datetime import datetime, timezone

from models.operational_event import OperationalEvent, EventType, EntityType
from models.tyre_domain import (
    Tyre, 
    TyreLifecycleRecord, 
    TyreStatus,
    LifecycleEventCategory
)
from models.expense_domain import Expense, ExpenseCategory, ExpenseStatus
from repositories.tyre_repository import TyreRepository


# ===========================================================================
# Domain Exceptions
# ===========================================================================

class TyreDomainError(Exception):
    """Base error for Tyre Domain."""
    pass


class TyreNotFoundError(TyreDomainError):
    """Raised when a requested tyre does not exist or belongs to another tenant."""
    pass


class InvalidTyreStateTransitionError(TyreDomainError):
    """Raised when an operation violates the tyre lifecycle state machine."""
    pass


class WheelPositionOccupiedError(TyreDomainError):
    """Raised when an installation or rotation targets an already occupied wheel position."""
    pass


class OdometerRollbackError(TyreDomainError):
    """Raised when a removal odometer is lower than installation odometer."""
    pass


class VehicleNotFoundError(TyreDomainError):
    """Raised when a target vehicle does not exist or belongs to another tenant."""
    pass


# ===========================================================================
# Domain Service
# ===========================================================================

class TyreService:
    """
    Coordinates Tyre Domain business rules and lifecycle invariants.
    Receives Canonical Events or handles direct domain operations from the API.
    """

    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    async def apply_verified_event(self, event: OperationalEvent) -> None:
        """
        Single entry point for asynchronous event-driven state mutation in the Tyre Domain.
        Reads a verified OperationalEvent and applies hardened business rules.
        """
        if event.entity_type != EntityType.TYRE:
            return

        payload = event.payload or {}
        serial_number = event.entity_id
        company_id = event.company_id
        origin_id = str(event.id)

        if event.event_type == EventType.TYRE_REGISTERED:
            await self.register_tyre(serial_number, payload, origin_id, company_id)
        elif event.event_type == EventType.TYRE_INSTALLED:
            await self.install_tyre(serial_number, payload, origin_id, company_id)
        elif event.event_type == EventType.TYRE_REMOVED:
            await self.remove_tyre(serial_number, payload, origin_id, company_id)
        elif event.event_type == EventType.TYRE_ROTATED:
            await self.rotate_tyre(serial_number, payload, origin_id, company_id)
        elif event.event_type == EventType.TYRE_REPAIRED:
            await self.repair_tyre(serial_number, payload, origin_id, company_id)
        elif event.event_type == EventType.TYRE_RETREADED:
            await self.retread_tyre(serial_number, payload, origin_id, company_id)
        elif event.event_type == EventType.TYRE_RETIRED:
            await self.retire_tyre(serial_number, payload, origin_id, company_id)
        elif event.event_type == EventType.TYRE_REPLACED:
            await self.replace_tyre(serial_number, payload, origin_id, company_id)

    # =========================================================================
    # Lifecycle Transitions (Idempotent, Atomic, Concurrency-Guarded)
    # =========================================================================

    async def register_tyre(
        self, 
        serial_number: str, 
        payload: dict, 
        origin_id: str, 
        company_id: int
    ) -> Tyre:
        """
        Registers a new physical tyre or updates specifications idempotently.
        Initial status is IN_STORAGE (available inventory).
        """
        clean_serial = serial_number.strip().upper()
        tyre = await self.uow.repositories.tyre.get_tyre_by_serial_number_for_update(clean_serial)

        purchase_info = dict(payload.get("purchase_information") or {})
        raw_cost = payload.get("purchase_cost")
        if raw_cost is None and "purchase_cost" in purchase_info:
            raw_cost = purchase_info.get("purchase_cost")

        p_cost: Optional[float] = None
        if raw_cost is not None:
            try:
                p_cost = float(raw_cost)
                if p_cost < 0.0:
                    raise InvalidTyreStateTransitionError(f"Purchase cost cannot be negative: {p_cost}")
            except (ValueError, TypeError):
                raise InvalidTyreStateTransitionError(f"Invalid purchase cost: {raw_cost}")

        raw_date = payload.get("purchase_date") or purchase_info.get("purchase_date")
        p_date: Optional[datetime] = None
        if raw_date:
            if isinstance(raw_date, datetime):
                p_date = raw_date
            else:
                try:
                    p_date = datetime.fromisoformat(str(raw_date))
                except (ValueError, TypeError):
                    p_date = None

        p_currency = str(payload.get("purchase_currency") or payload.get("currency") or purchase_info.get("currency") or "INR").upper()
        p_invoice = payload.get("invoice_number") or purchase_info.get("invoice_number")
        p_vendor = payload.get("vendor") or purchase_info.get("vendor")

        if tyre:
            if tyre.company_id != company_id:
                raise InvalidTyreStateTransitionError(
                    f"Tyre serial '{clean_serial}' is already registered under another company."
                )
            # Idempotent update: update specs without resetting active lifecycle state
            tyre.manufacturer = payload.get("manufacturer", tyre.manufacturer)
            tyre.brand = payload.get("brand", tyre.brand)
            tyre.model = payload.get("model", tyre.model)
            tyre.size = payload.get("size", tyre.size)
            if p_cost is not None:
                tyre.purchase_cost = p_cost
            if p_date is not None:
                tyre.purchase_date = p_date
            if p_currency:
                tyre.purchase_currency = p_currency
            if p_invoice:
                tyre.purchase_invoice = p_invoice
            if p_vendor:
                tyre.purchase_vendor = p_vendor

            updated_purchase_info = dict(tyre.purchase_information or {})
            if "purchase_information" in payload:
                updated_purchase_info.update(payload["purchase_information"])
            if p_cost is not None:
                updated_purchase_info["purchase_cost"] = p_cost
            if p_currency:
                updated_purchase_info["currency"] = p_currency
            if p_invoice:
                updated_purchase_info["invoice_number"] = p_invoice
            if p_vendor:
                updated_purchase_info["vendor"] = p_vendor
            tyre.purchase_information = updated_purchase_info

            await self.uow.repositories.tyre.upsert_tyre(tyre)
            return tyre

        initial_tread = payload.get("initial_tread_mm") or purchase_info.get("initial_tread_mm")
        if p_cost is not None:
            purchase_info["purchase_cost"] = p_cost
        if p_currency:
            purchase_info["currency"] = p_currency
        if p_invoice:
            purchase_info["invoice_number"] = p_invoice
        if p_vendor:
            purchase_info["vendor"] = p_vendor

        tyre = Tyre(
            company_id=company_id,
            serial_number=clean_serial,
            manufacturer=payload.get("manufacturer"),
            brand=payload.get("brand"),
            model=payload.get("model"),
            size=payload.get("size"),
            purchase_cost=p_cost,
            purchase_date=p_date,
            purchase_currency=p_currency,
            purchase_invoice=p_invoice,
            purchase_vendor=p_vendor,
            purchase_information=purchase_info,
            current_status=TyreStatus.IN_STORAGE,
            retread_count=0,
            total_lifetime_km=0.0,
            current_retread_km=0.0,
            current_tread_depth_mm=float(initial_tread) if initial_tread is not None else None,
            origin_type="verified_event",
            origin_id=origin_id
        )
        await self.uow.repositories.tyre.upsert_tyre(tyre)

        await self._append_lifecycle_record(
            tyre.id, company_id, LifecycleEventCategory.INSTALLED if payload.get("installed") else LifecycleEventCategory.REMOVED,
            payload, origin_id,
            extra_details={"action": "REGISTERED", "initial_status": TyreStatus.IN_STORAGE.value}
        )

        # Financial recognition: if record_purchase_expense requested and purchase_cost present
        if (payload.get("record_purchase_expense") or purchase_info.get("record_expense")) and p_cost is not None and p_cost > 0.0:
            exp_business_id = f"EXP-TYRE-PURCHASE-{clean_serial}"
            existing_exp = await self.uow.repositories.expense.get_expense_by_business_id(exp_business_id)
            if not existing_exp:
                exp = Expense(
                    business_id=exp_business_id,
                    category=ExpenseCategory.TYRE,
                    amount=p_cost,
                    currency=p_currency,
                    status=ExpenseStatus.PENDING,
                    expense_date=p_date or datetime.now(timezone.utc),
                    description=f"Direct tyre purchase receipt: {clean_serial} ({tyre.brand or tyre.manufacturer or 'Tyre'})",
                    receipt_reference=p_invoice,
                    company_id=company_id,
                    origin_type="verified_event",
                    origin_id=origin_id
                )
                await self.uow.repositories.expense.upsert_expense(exp)

        return tyre

    async def install_tyre(
        self, 
        serial_number: str, 
        payload: dict, 
        origin_id: str, 
        company_id: int
    ) -> Tyre:
        """
        Installs a tyre onto a vehicle at a designated wheel position.
        Guards:
        - Tyre must belong to company.
        - Tyre must be IN_STORAGE or REGISTERED.
        - Vehicle must exist and belong to company.
        - Designated wheel position must not already be occupied by another tyre.
        - Records installation odometer for future delta calculation.
        """
        clean_serial = serial_number.strip().upper()
        tyre = await self.uow.repositories.tyre.get_tyre_by_serial_number_for_update(clean_serial)
        if not tyre or tyre.company_id != company_id:
            raise TyreNotFoundError(f"Tyre '{clean_serial}' not found in your fleet.")

        vehicle_id = payload.get("vehicle_id")
        position = (payload.get("position") or "").strip().upper()
        if not vehicle_id or not position:
            raise InvalidTyreStateTransitionError("Both 'vehicle_id' and 'position' are required for tyre installation.")

        # Idempotent retry: if tyre is already mounted at this exact vehicle & position, return
        if tyre.current_status == TyreStatus.INSTALLED and tyre.current_vehicle_id == vehicle_id and tyre.current_position == position:
            return tyre

        # Transition Guards
        if tyre.current_status == TyreStatus.INSTALLED:
            raise InvalidTyreStateTransitionError(
                f"Tyre '{clean_serial}' is already installed on vehicle #{tyre.current_vehicle_id} at position '{tyre.current_position}'. "
                f"It must be removed before mounting on another vehicle."
            )
        if tyre.current_status == TyreStatus.RETIRED:
            raise InvalidTyreStateTransitionError(f"Cannot install tyre '{clean_serial}': tyre is RETIRED / scrapped.")
        if tyre.current_status == TyreStatus.RETREADING:
            raise InvalidTyreStateTransitionError(f"Cannot install tyre '{clean_serial}': tyre is currently sent out for RETREADING.")
        if tyre.current_status == TyreStatus.IN_REPAIR:
            raise InvalidTyreStateTransitionError(f"Cannot install tyre '{clean_serial}': tyre is currently IN_REPAIR.")

        # Verify vehicle ownership
        vehicle = await self.uow.repositories.vehicle.get_vehicle_by_id(vehicle_id)
        if not vehicle or vehicle.company_id != company_id:
            raise VehicleNotFoundError(f"Vehicle #{vehicle_id} not found in your fleet.")

        # Verify position occupancy
        occupant = await self.uow.repositories.tyre.get_tyre_at_position(vehicle_id, position)
        if occupant and occupant.id != tyre.id:
            raise WheelPositionOccupiedError(
                f"Position '{position}' on vehicle #{vehicle_id} is already occupied by tyre '{occupant.serial_number}'."
            )

        # Odometer determination
        odo = payload.get("odometer_km")
        if odo is None and vehicle.current_odometer is not None:
            odo = vehicle.current_odometer

        tyre.current_status = TyreStatus.INSTALLED
        tyre.current_vehicle_id = vehicle_id
        tyre.current_position = position
        tyre.current_installation_odometer = float(odo) if odo is not None else None
        tyre.origin_type = "verified_event"
        tyre.origin_id = origin_id
        await self.uow.repositories.tyre.upsert_tyre(tyre)

        await self._append_lifecycle_record(
            tyre.id, company_id, LifecycleEventCategory.INSTALLED, payload, origin_id,
            extra_details={"vehicle_id": vehicle_id, "position": position, "installation_odometer": tyre.current_installation_odometer}
        )

        return tyre

    async def remove_tyre(
        self, 
        serial_number: str, 
        payload: dict, 
        origin_id: str, 
        company_id: int
    ) -> Tyre:
        """
        Removes an installed tyre from a vehicle.
        Guards:
        - Tyre must be currently INSTALLED.
        - Removal odometer must be >= installation odometer (rejects odometer rollbacks).
        - Accumulates distance run into total_lifetime_km and current_retread_km.
        - Clears vehicle and position references atomically.
        """
        clean_serial = serial_number.strip().upper()
        tyre = await self.uow.repositories.tyre.get_tyre_by_serial_number_for_update(clean_serial)
        if not tyre or tyre.company_id != company_id:
            raise TyreNotFoundError(f"Tyre '{clean_serial}' not found in your fleet.")

        # Idempotent retry: if already unmounted, return
        if tyre.current_status != TyreStatus.INSTALLED and tyre.current_vehicle_id is None:
            return tyre

        if tyre.current_status != TyreStatus.INSTALLED:
            raise InvalidTyreStateTransitionError(
                f"Cannot remove tyre '{clean_serial}': tyre is in '{tyre.current_status.value}', not INSTALLED."
            )

        # Removal odometer validation
        vehicle_id = tyre.current_vehicle_id
        removal_odo = payload.get("odometer_km")
        if removal_odo is None and vehicle_id:
            vehicle = await self.uow.repositories.vehicle.get_vehicle_by_id(vehicle_id)
            if vehicle and vehicle.current_odometer is not None:
                removal_odo = vehicle.current_odometer

        dist_run = 0.0
        if tyre.current_installation_odometer is not None and removal_odo is not None:
            removal_odo_flt = float(removal_odo)
            if removal_odo_flt < tyre.current_installation_odometer:
                raise OdometerRollbackError(
                    f"Removal odometer ({removal_odo_flt} km) cannot be less than installation odometer "
                    f"({tyre.current_installation_odometer} km). Odometer rollback rejected."
                )
            dist_run = round(removal_odo_flt - tyre.current_installation_odometer, 2)
            tyre.total_lifetime_km = round(tyre.total_lifetime_km + dist_run, 2)
            tyre.current_retread_km = round(tyre.current_retread_km + dist_run, 2)

        target_status_raw = (payload.get("target_status") or "IN_STORAGE").upper()
        if target_status_raw == "RETREADING":
            tyre.current_status = TyreStatus.RETREADING
        elif target_status_raw == "IN_REPAIR":
            tyre.current_status = TyreStatus.IN_REPAIR
        elif target_status_raw == "RETIRED":
            tyre.current_status = TyreStatus.RETIRED
        else:
            tyre.current_status = TyreStatus.IN_STORAGE

        prev_pos = tyre.current_position
        tyre.current_vehicle_id = None
        tyre.current_position = None
        tyre.current_installation_odometer = None
        tyre.origin_type = "verified_event"
        tyre.origin_id = origin_id
        await self.uow.repositories.tyre.upsert_tyre(tyre)

        await self._append_lifecycle_record(
            tyre.id, company_id, LifecycleEventCategory.REMOVED, payload, origin_id,
            extra_details={
                "previous_vehicle_id": vehicle_id,
                "previous_position": prev_pos,
                "removal_odometer": removal_odo,
                "distance_run_km": dist_run,
                "target_status": tyre.current_status.value,
                "reason": payload.get("reason")
            }
        )

        return tyre

    async def rotate_tyre(
        self, 
        serial_number: str, 
        payload: dict, 
        origin_id: str, 
        company_id: int
    ) -> Tyre:
        """
        Rotates a tyre to a new wheel position on the same vehicle.
        Supports single move to vacant position or atomic 2-tyre swap.
        """
        clean_serial = serial_number.strip().upper()
        tyre = await self.uow.repositories.tyre.get_tyre_by_serial_number_for_update(clean_serial)
        if not tyre or tyre.company_id != company_id:
            raise TyreNotFoundError(f"Tyre '{clean_serial}' not found in your fleet.")

        if tyre.current_status != TyreStatus.INSTALLED or not tyre.current_vehicle_id:
            raise InvalidTyreStateTransitionError(
                f"Cannot rotate tyre '{clean_serial}': tyre is not currently INSTALLED on a vehicle."
            )

        new_position = (payload.get("new_position") or "").strip().upper()
        if not new_position:
            raise InvalidTyreStateTransitionError("Field 'new_position' is required for tyre rotation.")

        if new_position == tyre.current_position:
            return tyre  # Idempotent no-op

        occupant = await self.uow.repositories.tyre.get_tyre_at_position(tyre.current_vehicle_id, new_position)
        swap_serial = payload.get("swap_serial_number")
        if occupant and occupant.id != tyre.id:
            if swap_serial and occupant.serial_number.upper() == swap_serial.strip().upper():
                # Atomic swap
                old_pos = tyre.current_position
                occupant.current_position = old_pos
                occupant.origin_type = "verified_event"
                occupant.origin_id = origin_id
                await self.uow.repositories.tyre.upsert_tyre(occupant)
                await self._append_lifecycle_record(
                    occupant.id, company_id, LifecycleEventCategory.ROTATED, payload, origin_id,
                    extra_details={"previous_position": new_position, "new_position": old_pos, "swapped_with": tyre.serial_number}
                )
            else:
                raise WheelPositionOccupiedError(
                    f"Position '{new_position}' on vehicle #{tyre.current_vehicle_id} is occupied by tyre '{occupant.serial_number}'. "
                    f"Specify 'swap_serial_number' to perform a position swap."
                )

        prev_pos = tyre.current_position
        tyre.current_position = new_position
        tyre.origin_type = "verified_event"
        tyre.origin_id = origin_id
        await self.uow.repositories.tyre.upsert_tyre(tyre)

        await self._append_lifecycle_record(
            tyre.id, company_id, LifecycleEventCategory.ROTATED, payload, origin_id,
            extra_details={"previous_position": prev_pos, "new_position": new_position}
        )

        return tyre

    async def retread_tyre(
        self, 
        serial_number: str, 
        payload: dict, 
        origin_id: str, 
        company_id: int
    ) -> Tyre:
        """
        Processes a retread operation.
        - If action is REJECTED/SCRAPPED: tyre is retired (failed casing inspection).
        - If COMPLETED: increments retread_count, resets current_retread_km, returns tyre to IN_STORAGE.
        - Financial cost is expensed once via Expense domain without double counting.
        """
        clean_serial = serial_number.strip().upper()
        tyre = await self.uow.repositories.tyre.get_tyre_by_serial_number_for_update(clean_serial)
        if not tyre or tyre.company_id != company_id:
            raise TyreNotFoundError(f"Tyre '{clean_serial}' not found in your fleet.")

        if tyre.current_status == TyreStatus.INSTALLED:
            raise InvalidTyreStateTransitionError(
                f"Cannot retread tyre '{clean_serial}': tyre is currently INSTALLED on vehicle #{tyre.current_vehicle_id}. "
                f"It must be removed before retreading."
            )
        if tyre.current_status == TyreStatus.RETIRED:
            raise InvalidTyreStateTransitionError(f"Cannot retread tyre '{clean_serial}': tyre is already RETIRED.")

        action = (payload.get("action") or "COMPLETED").upper()
        if action in ("REJECTED", "SCRAPPED", "FAILED"):
            tyre.current_status = TyreStatus.RETIRED
            reason = payload.get("rejection_reason") or "Casing rejected during retreading"
            await self.uow.repositories.tyre.upsert_tyre(tyre)
            await self._append_lifecycle_record(
                tyre.id, company_id, LifecycleEventCategory.RETIRED, payload, origin_id,
                extra_details={"action": "RETREAD_REJECTED", "reason": reason, "vendor": payload.get("vendor")}
            )
            return tyre

        # Check idempotency: avoid double increment on retried event
        existing_record = await self.uow.repositories.tyre.get_lifecycle_record_by_origin(
            tyre.id, origin_id, LifecycleEventCategory.RETREADED
        )
        if existing_record:
            return tyre


        tyre.retread_count += 1
        tyre.current_retread_km = 0.0  # fresh tread wear cycle
        if payload.get("tread_depth_mm") is not None:
            tyre.current_tread_depth_mm = float(payload["tread_depth_mm"])
        tyre.current_status = TyreStatus.IN_STORAGE
        tyre.origin_type = "verified_event"
        tyre.origin_id = origin_id
        await self.uow.repositories.tyre.upsert_tyre(tyre)

        await self._append_lifecycle_record(
            tyre.id, company_id, LifecycleEventCategory.RETREADED, payload, origin_id,
            extra_details={
                "retread_count": tyre.retread_count,
                "vendor": payload.get("vendor"),
                "cost": payload.get("cost"),
                "tread_depth_mm": tyre.current_tread_depth_mm
            }
        )

        # Financial recognition: create retread service expense if cost present
        retread_cost = float(payload.get("cost") or 0.0)
        if retread_cost > 0.0:
            exp_business_id = f"EXP-TYRE-RETREAD-{clean_serial}-{tyre.retread_count}"
            existing_exp = await self.uow.repositories.expense.get_expense_by_business_id(exp_business_id)
            if not existing_exp:
                exp = Expense(
                    business_id=exp_business_id,
                    category=ExpenseCategory.TYRE,
                    amount=retread_cost,
                    currency=payload.get("currency", "INR"),
                    status=ExpenseStatus.PENDING,
                    expense_date=datetime.now(timezone.utc),
                    description=f"Tyre retread #{tyre.retread_count} for {clean_serial} (Vendor: {payload.get('vendor', 'Unknown')})",
                    receipt_reference=payload.get("receipt_reference") or payload.get("invoice_number"),
                    company_id=company_id,
                    origin_type="verified_event",
                    origin_id=origin_id
                )
                await self.uow.repositories.expense.upsert_expense(exp)

        return tyre

    async def repair_tyre(
        self, 
        serial_number: str, 
        payload: dict, 
        origin_id: str, 
        company_id: int
    ) -> Tyre:
        """
        Records a tyre repair (puncture, vulcanizing, patch).
        If tyre was in IN_REPAIR, returns it to IN_STORAGE if return_to_storage is True.
        Expanses repair cost once in the Expense ledger.
        """
        clean_serial = serial_number.strip().upper()
        tyre = await self.uow.repositories.tyre.get_tyre_by_serial_number_for_update(clean_serial)
        if not tyre or tyre.company_id != company_id:
            raise TyreNotFoundError(f"Tyre '{clean_serial}' not found in your fleet.")

        if tyre.current_status == TyreStatus.RETIRED:
            raise InvalidTyreStateTransitionError(f"Cannot repair tyre '{clean_serial}': tyre is RETIRED.")

        if tyre.current_status == TyreStatus.IN_REPAIR and payload.get("return_to_storage", True):
            tyre.current_status = TyreStatus.IN_STORAGE

        tyre.origin_type = "verified_event"
        tyre.origin_id = origin_id
        await self.uow.repositories.tyre.upsert_tyre(tyre)

        await self._append_lifecycle_record(
            tyre.id, company_id, LifecycleEventCategory.REPAIRED, payload, origin_id,
            extra_details={
                "repair_type": payload.get("repair_type", "PUNCTURE"),
                "workshop": payload.get("workshop"),
                "cost": payload.get("cost")
            }
        )

        repair_cost = float(payload.get("cost") or 0.0)
        if repair_cost > 0.0:
            exp_business_id = f"EXP-TYRE-REPAIR-{clean_serial}-{origin_id}"
            existing_exp = await self.uow.repositories.expense.get_expense_by_business_id(exp_business_id)
            if not existing_exp:
                exp = Expense(
                    business_id=exp_business_id,
                    category=ExpenseCategory.TYRE,
                    amount=repair_cost,
                    currency=payload.get("currency", "INR"),
                    status=ExpenseStatus.PENDING,
                    expense_date=datetime.now(timezone.utc),
                    description=f"Tyre repair ({payload.get('repair_type', 'PUNCTURE')}) for {clean_serial}",
                    receipt_reference=payload.get("receipt_reference"),
                    company_id=company_id,
                    vehicle_id=tyre.current_vehicle_id,
                    origin_type="verified_event",
                    origin_id=origin_id
                )
                await self.uow.repositories.expense.upsert_expense(exp)

        return tyre

    async def retire_tyre(
        self, 
        serial_number: str, 
        payload: dict, 
        origin_id: str, 
        company_id: int
    ) -> Tyre:
        """
        Permanently retires/scraps a tyre.
        Guards:
        - Cannot retire an already retired tyre (idempotent return).
        - Cannot retire a tyre that is currently INSTALLED on a vehicle without removal.
        """
        clean_serial = serial_number.strip().upper()
        tyre = await self.uow.repositories.tyre.get_tyre_by_serial_number_for_update(clean_serial)
        if not tyre or tyre.company_id != company_id:
            raise TyreNotFoundError(f"Tyre '{clean_serial}' not found in your fleet.")

        if tyre.current_status == TyreStatus.RETIRED:
            return tyre  # Idempotent

        if tyre.current_status == TyreStatus.INSTALLED:
            raise InvalidTyreStateTransitionError(
                f"Cannot retire tyre '{clean_serial}' while still INSTALLED on vehicle #{tyre.current_vehicle_id}. "
                f"It must be officially removed first."
            )

        tyre.current_status = TyreStatus.RETIRED
        tyre.current_vehicle_id = None
        tyre.current_position = None
        tyre.origin_type = "verified_event"
        tyre.origin_id = origin_id
        await self.uow.repositories.tyre.upsert_tyre(tyre)

        await self._append_lifecycle_record(
            tyre.id, company_id, LifecycleEventCategory.RETIRED, payload, origin_id,
            extra_details={"reason": payload.get("reason"), "salvage_value": payload.get("salvage_value")}
        )

        return tyre

    async def replace_tyre(
        self, 
        serial_number: str, 
        payload: dict, 
        origin_id: str, 
        company_id: int
    ) -> Tuple[Tyre, Tyre]:
        """
        Compound atomic replacement:
        Removes the old tyre from vehicle/position, then installs the new tyre at that position.
        """
        old_serial = serial_number
        new_serial = payload.get("new_serial_number")
        if not new_serial:
            raise InvalidTyreStateTransitionError("Field 'new_serial_number' is required for tyre replacement.")

        old_tyre = await self.uow.repositories.tyre.get_tyre_by_serial_number(old_serial)
        if not old_tyre or old_tyre.company_id != company_id:
            raise TyreNotFoundError(f"Old tyre '{old_serial}' not found.")
        if old_tyre.current_status != TyreStatus.INSTALLED:
            raise InvalidTyreStateTransitionError(f"Old tyre '{old_serial}' is not currently INSTALLED.")

        vehicle_id = old_tyre.current_vehicle_id
        position = old_tyre.current_position

        # 1. Remove old tyre
        remove_payload = {
            "odometer_km": payload.get("odometer_km"),
            "target_status": payload.get("old_tyre_target_status", "IN_STORAGE"),
            "reason": payload.get("reason", "Replaced by " + new_serial)
        }
        old_tyre = await self.remove_tyre(old_serial, remove_payload, origin_id, company_id)

        # 2. Install new tyre
        install_payload = {
            "vehicle_id": vehicle_id,
            "position": position,
            "odometer_km": payload.get("odometer_km")
        }
        new_tyre = await self.install_tyre(new_serial, install_payload, origin_id, company_id)

        return old_tyre, new_tyre

    # =========================================================================
    # Helpers & Read APIs
    # =========================================================================

    async def _append_lifecycle_record(
        self, 
        tyre_id: int, 
        company_id: int, 
        category: LifecycleEventCategory, 
        payload: dict, 
        origin_id: str,
        extra_details: Optional[dict] = None
    ) -> None:
        performed_at = datetime.now(timezone.utc)
        if "performed_at" in payload and payload["performed_at"]:
            try:
                if isinstance(payload["performed_at"], datetime):
                    performed_at = payload["performed_at"]
                else:
                    performed_at = datetime.fromisoformat(str(payload["performed_at"]))
            except (ValueError, TypeError):
                pass

        details = dict(payload.get("details") or {})
        if extra_details:
            details.update(extra_details)

        record = TyreLifecycleRecord(
            tyre_id=tyre_id,
            company_id=company_id,
            event_category=category,
            performed_at=performed_at,
            details=details,
            origin_type="verified_event",
            origin_id=origin_id
        )
        await self.uow.repositories.tyre.add_lifecycle_record(record)

    async def get_tyre(self, tyre_id: int) -> Optional[Tyre]:
        return await self.uow.repositories.tyre.get_tyre_by_id(tyre_id)

    async def get_tyre_by_company(self, tyre_id: int, company_id: int) -> Optional[Tyre]:
        return await self.uow.repositories.tyre.get_tyre_by_id_and_company(tyre_id, company_id)
        
    async def get_tyres_by_vehicle(self, vehicle_id: int, limit: int = 50, offset: int = 0) -> Sequence[Tyre]:
        return await self.uow.repositories.tyre.get_tyres_by_vehicle(vehicle_id, limit, offset)

    async def search_tyres(
        self, 
        company_id: int,
        status: Optional[TyreStatus] = None, 
        limit: int = 50, 
        offset: int = 0
    ) -> Sequence[Tyre]:
        return await self.uow.repositories.tyre.search_tyres_by_company(
            company_id=company_id, status=status, limit=limit, offset=offset
        )

    async def get_inventory_summary(self, company_id: int) -> Dict[str, int]:
        counts = await self.uow.repositories.tyre.count_by_status_for_company(company_id)
        total = sum(counts.values())
        return {
            "total_tyres": total,
            "in_storage": counts.get(TyreStatus.IN_STORAGE.value, 0) + counts.get(TyreStatus.REGISTERED.value, 0),
            "installed": counts.get(TyreStatus.INSTALLED.value, 0),
            "retreading": counts.get(TyreStatus.RETREADING.value, 0),
            "in_repair": counts.get(TyreStatus.IN_REPAIR.value, 0),
            "retired": counts.get(TyreStatus.RETIRED.value, 0)
        }

    async def get_inventory_valuation(self, company_id: int) -> Dict[str, Any]:
        """
        Computes company-scoped inventory acquisition valuation.
        Aggregates per-physical-tyre known purchase cost partitioned by lifecycle state.
        Transparently reports counts of unknown-cost tyres without zero-fabrication.
        Reports retread and repair expenditures separately from the Expense ledger.
        """
        return await self.uow.repositories.tyre.get_inventory_valuation_by_company(company_id)

