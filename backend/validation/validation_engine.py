"""
FleetGuard — Validation Engine

Coordinates all registered validators for incoming Operational Events.

The ValidationEngine is the orchestrator of the Validation & Enrichment Engine
layer.  It receives events from the EventDispatcher (via its EventSubscriber
interface), runs all applicable validators, aggregates their results, and
writes the final verification decision back to the Operational Event Store.

Responsibilities
----------------
• Maintain a registry of ``BaseValidator`` instances.
• For each event: build a ``ValidationContext``, run applicable validators,
  aggregate ``ValidationResult`` objects into a single ``VerificationStatus``.
• Merge ``enrichment_data`` from all validators into the event's metadata.
• Write the final status and enriched metadata back via ``OperationalEventService``.
• Catch and log individual validator failures without blocking other validators.

Aggregation rules (single source of truth)
------------------------------------------
The engine applies these rules in priority order:

1. REJECTED    — if ANY validator returns REJECTED, the final status is REJECTED.
2. NEEDS_REVIEW — if ANY validator returns NEEDS_MANUAL_REVIEW (and none REJECTED),
                  the final status is DISPUTED.
3. PENDING_MORE_DATA — if ANY validator returns PENDING_MORE_DATA (and none of
                  the above), the event remains PENDING.
4. VERIFIED    — only if ALL applicable validators return VERIFIED.
5. No validators ran — event remains PENDING (conservative default).

What the engine does NOT do
---------------------------
• It does not know about fuel, GPS, OCR, drivers, or vehicles.
• It does not contain validation logic — that lives in concrete validators.
• It does not raise HTTP exceptions.
• It does not communicate with the database directly — only through the service.

Integration
-----------
The ``ValidationEngine`` implements ``EventSubscriber`` so it registers with
the ``EventDispatcher`` and receives events automatically after they are
persisted.  No router change is required.

The ``async_sessionmaker`` dependency is injected at construction time.
The engine is instantiated in ``main.py`` at startup.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from dispatchers.event_subscriber import EventSubscriber
from models.operational_event import VerificationStatus
from schemas.operational_event import OperationalEventResponse
from validation.base_validator import BaseValidator
from validation.validation_context import ValidationContext
from validation.validation_outcome import ValidationOutcome
from validation.validation_result import ValidationResult

logger = logging.getLogger("fleetguard.validation.engine")


class ValidationEngine(EventSubscriber):
    """
    Orchestrates all registered validators for incoming Operational Events.

    Implements ``EventSubscriber`` so it can be registered directly with
    ``EventDispatcher``.  Receives ALL event types (``event_filter = None``).

    Parameters
    ----------
    session_factory : Callable[[], AsyncSession]
        The async session maker factory used to obtain short-lived db
        sessions for writing validation outcomes back to the store.

    Usage (startup registration in main.py)
    ----------------------------------------
    ::

        from validation.validation_engine import ValidationEngine
        from database import async_session_factory

        engine = ValidationEngine(session_factory=async_session_factory)
        engine.register_validator(FuelQuantityValidator())
        event_dispatcher.register_subscriber(engine)
    """

    # Identifies this subscriber in the dispatcher registry.
    name: str = "validation_engine"

    # Receives ALL event types — individual validators declare their own scope
    # via their ``applies_to()`` method.
    event_filter = None

    def __init__(self, session_factory: Callable[[], AsyncSession]) -> None:
        self._session_factory = session_factory
        self._validators: list[BaseValidator] = []

    # -----------------------------------------------------------------------
    # Validator Registry
    # -----------------------------------------------------------------------

    def register_validator(self, validator: BaseValidator) -> None:
        """
        Register a concrete validator with the engine.

        Parameters
        ----------
        validator : BaseValidator
            The validator to register.

        Raises
        ------
        ValueError
            If a validator with the same ``name`` is already registered.
        """
        for existing in self._validators:
            if existing.name == validator.name:
                raise ValueError(
                    f"A validator named '{validator.name}' is already registered."
                )
        self._validators.append(validator)
        logger.info("Validator registered: %s", validator.name)

    def unregister_validator(self, name: str) -> None:
        """
        Unregister a validator by name.

        Parameters
        ----------
        name : str
            The ``name`` attribute of the validator to remove.

        Raises
        ------
        KeyError
            If no validator with the given name is registered.
        """
        before = len(self._validators)
        self._validators = [v for v in self._validators if v.name != name]
        if len(self._validators) == before:
            raise KeyError(f"No validator named '{name}' is registered.")
        logger.info("Validator unregistered: %s", name)

    @property
    def validator_names(self) -> list[str]:
        """Names of all currently registered validators."""
        return [v.name for v in self._validators]

    # -----------------------------------------------------------------------
    # EventSubscriber — called by EventDispatcher
    # -----------------------------------------------------------------------

    async def handle(self, event: OperationalEventResponse) -> None:
        """
        Entry point called by the ``EventDispatcher`` after event persist.

        Runs all registered validators against the event, aggregates their
        results, and writes the final status back to the event store.

        Parameters
        ----------
        event : OperationalEventResponse
            The newly persisted event.  Read-only.
        """
        logger.info(
            "ValidationEngine handling event id=%s type=%s",
            event.id,
            event.event_type.value,
        )

        context = ValidationContext(event=event)

        # Run all applicable validators
        results = await self._run_validators(context)

        if not results:
            logger.info(
                "No validators applied to event id=%s — remains PENDING.",
                event.id,
            )
            return

        # Aggregate results into a final VerificationStatus
        final_status = self._aggregate(results)

        # Collect enrichment data from all validators
        merged_enrichment = self._merge_enrichment(results, event)

        # Write outcomes back to the event store
        await self._apply_outcome(event, final_status, merged_enrichment, results)

    # -----------------------------------------------------------------------
    # Internal orchestration
    # -----------------------------------------------------------------------

    async def _run_validators(
        self, context: ValidationContext
    ) -> list[ValidationResult]:
        """
        Run every registered validator that applies to the context.

        Catches per-validator exceptions so one failing validator does not
        prevent others from running.
        """
        results: list[ValidationResult] = []

        for validator in self._validators:
            try:
                applicable = await validator.applies_to(context)
                if not applicable:
                    logger.debug(
                        "Validator '%s' skipped for event_type=%s.",
                        validator.name,
                        context.event.event_type.value,
                    )
                    continue

                logger.debug(
                    "Running validator '%s' for event id=%s.",
                    validator.name,
                    context.event.id,
                )
                result = await validator.validate(context)
                result.validator_name = validator.name  # set by engine, not validator
                results.append(result)

                logger.info(
                    "Validator '%s' outcome=%s for event id=%s. Reasons=%s",
                    validator.name,
                    result.outcome.value,
                    context.event.id,
                    result.reasons,
                )

            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "Validator '%s' raised an unexpected error for event id=%s: %s",
                    validator.name,
                    context.event.id,
                    exc,
                )
                # Do not append a result — the engine will treat missing
                # results conservatively (event stays PENDING).

        return results

    def _aggregate(self, results: list[ValidationResult]) -> VerificationStatus:
        """
        Aggregate multiple ``ValidationResult`` objects into one ``VerificationStatus``.

        Priority order (highest to lowest):
            1. Any REJECTED       → REJECTED
            2. Any NEEDS_REVIEW   → DISPUTED
            3. Any PENDING_MORE_DATA → PENDING
            4. All VERIFIED       → VERIFIED
        """
        outcomes = {r.outcome for r in results}

        if ValidationOutcome.REJECTED in outcomes:
            return VerificationStatus.REJECTED

        if ValidationOutcome.NEEDS_MANUAL_REVIEW in outcomes:
            return VerificationStatus.DISPUTED

        if ValidationOutcome.PENDING_MORE_DATA in outcomes:
            return VerificationStatus.PENDING

        # All outcomes must be VERIFIED
        return VerificationStatus.VERIFIED

    def _merge_enrichment(
        self,
        results: list[ValidationResult],
        event: OperationalEventResponse,
    ) -> dict[str, Any]:
        """
        Merge enrichment_data from all validators into a single dict.

        Each validator's enrichment is namespaced under its ``validator_name``
        to prevent key collisions between validators.

        The existing event metadata is preserved and extended, not replaced.
        """
        merged: dict[str, Any] = dict(event.event_metadata or {})

        enrichment_by_validator: dict[str, Any] = {
            r.validator_name: r.enrichment_data
            for r in results
            if r.enrichment_data
        }

        if enrichment_by_validator:
            # Namespace under "vee" (Validation & Enrichment Engine)
            vee_block = merged.get("vee", {})
            vee_block.update(enrichment_by_validator)
            merged["vee"] = vee_block

        return merged

    async def _apply_outcome(
        self,
        event: OperationalEventResponse,
        final_status: VerificationStatus,
        merged_metadata: dict[str, Any],
        results: list[ValidationResult],
    ) -> None:
        """
        Write the aggregated outcome back to the Operational Event Store.

        Steps:
        1. Build a summary of all validator results into the metadata.
        2. Update event_metadata with enrichment data + validation summary.
        3. Update verification_status via the service.
        """
        # Build a human-readable validation summary for auditors
        validation_summary = {
            "validators_run": [r.validator_name for r in results],
            "outcomes": {r.validator_name: r.outcome.value for r in results},
            "all_reasons": {r.validator_name: r.reasons for r in results if r.reasons},
            "all_warnings": {r.validator_name: r.warnings for r in results if r.warnings},
            "final_status": final_status.value,
        }
        vee_block = merged_metadata.get("vee", {})
        vee_block["validation_summary"] = validation_summary
        merged_metadata["vee"] = vee_block

        try:
            # We must import OperationalEventService here to avoid circular imports.
            from services.operational_event_service import OperationalEventService  # noqa: PLC0415
            
            # Create a short-lived DB session to run the service methods.
            async with self._session_factory() as session:
                service = OperationalEventService(session)
                
                # Write enriched metadata first
                await service.update_metadata(event.id, merged_metadata)
                
                # Then advance the status
                await service.apply_update(
                    event.id,
                    _StatusUpdateOnly(verification_status=final_status),
                )
                
                # Commit the transaction because we are bypassing get_db()
                await session.commit()

            logger.info(
                "Event id=%s advanced to %s after validation.",
                event.id,
                final_status.value,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Failed to write validation outcome for event id=%s: %s",
                event.id,
                exc,
            )


# ---------------------------------------------------------------------------
# Internal helper — thin OperationalEventUpdate substitute
# ---------------------------------------------------------------------------

from schemas.operational_event import OperationalEventUpdate  # noqa: E402


def _StatusUpdateOnly(
    *, verification_status: VerificationStatus
) -> OperationalEventUpdate:
    """
    Build an ``OperationalEventUpdate`` that touches only ``verification_status``.

    Used internally by the engine to avoid importing the schema at the top
    of this module (which would create a heavier dependency graph).
    """
    return OperationalEventUpdate(verification_status=verification_status)
