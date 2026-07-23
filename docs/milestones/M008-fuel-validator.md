# Milestone 8 — Fuel Validator (Structural Validation)

---

## Overview

This milestone introduces the first concrete validator for the Validation &
Enrichment Engine (VEE): the `FuelStructuralValidator`.

This validator applies ONLY to `FUEL_FILLED` Operational Events. It performs
purely structural checks on the event payload to ensure it conforms to the
expected schema before any business rules or evidence-based checks are applied.

---

## What It Checks

The validator verifies that the payload contains required numeric fields and
that they fall within reasonable bounds.

| Field | Check |
|---|---|
| `liters` | Required. Must be a number > 0. |
| `amount` | Required. Must be a number > 0. |
| `odometer` | Optional. If provided, must be an integer >= 0. |

If any check fails, it returns a `ValidationOutcome.REJECTED` with specific
human-readable reasons detailing which fields were missing or invalid.

If all checks pass, it returns `ValidationOutcome.VERIFIED`.

---

## What It Does NOT Check

This validator is strictly structural. It does **not** attempt to prove
whether the fuel transaction genuinely occurred.

The following checks belong to future Evidence Providers and are out of scope
for this validator:
- Did the vehicle actually stop at a gas station? (GPS Validator)
- Does the claimed amount match a physical receipt? (OCR Validator)
- Did the vehicle's fuel level actually increase? (Telemetry Validator)
- Does the odometer reading make physical sense compared to the previous trip?

---

## Files Created

| File | Purpose |
|---|---|
| `backend/validation/validators/__init__.py` | Package exporting concrete validators. |
| `backend/validation/validators/fuel_structural_validator.py` | The validator implementation. |

## Files Modified

| File | Change |
|---|---|
| `backend/main.py` | Instantiates `ValidationEngine`, registers `FuelStructuralValidator`, and attaches the engine to the global `EventDispatcher`. |

---

## Architecture Integration

The Validation Engine is now fully wired into the application lifecycle:

1. `main.py` creates the `EventDispatcher`.
2. `main.py` creates the `ValidationEngine`, injecting the `async_session_factory`.
3. `main.py` registers the `FuelStructuralValidator` into the engine.
4. `main.py` registers the engine as a subscriber to the `EventDispatcher`.

When a `FUEL_FILLED` event is recorded (e.g., via `POST /api/v1/events`), the
router saves it to the database, the service publishes it to the dispatcher,
the dispatcher calls the Validation Engine, and the Engine runs the Structural
Validator. The final status is then written back to the event store.

---

## Next Milestone

**Milestone 9 — Evidence Collection Framework**

With the first validator in place, the system is ready to support external
evidence integration (e.g., fetching GPS coordinates, telemetry, or parsing
receipt images) to enable complex fraud-detection validators.
