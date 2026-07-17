# Milestone 9 — Validation Framework

---

## Overview

This milestone implements the Validation & Enrichment Engine (VEE) **framework**.

No validation rules are implemented. This milestone builds only the
infrastructure that future validators will plug into:

- `ValidationOutcome` — possible verdicts for a single validator
- `ValidationResult` — structured output of one validator run
- `ValidationContext` — immutable event bundle passed to every validator
- `BaseValidator` — ABC every concrete validator must subclass
- `ValidationEngine` — orchestrator; implements `EventSubscriber`

The engine is registered with the `EventDispatcher` and receives every
newly created `OperationalEvent` automatically. With no validators registered
yet, events remain in `PENDING` state.

---

## Architecture

```
EventDispatcher.publish(event)
        │
        ▼
ValidationEngine.handle(event)           ← EventSubscriber
        │
        ├─ Build ValidationContext(event)
        │
        ├─ For each registered BaseValidator:
        │       │
        │       ├─ applies_to(context) → False → skip silently
        │       │
        │       └─ applies_to(context) → True
        │               │
        │               └─ validate(context) → ValidationResult
        │
        ├─ Aggregate outcomes  (priority: REJECTED > NEEDS_REVIEW > PENDING > VERIFIED)
        │
        ├─ Merge enrichment_data → event_metadata["vee"]
        │
        └─ Write back via OperationalEventService:
                ├─ update_metadata(event_id, merged_metadata)
                └─ apply_update(event_id, {verification_status: final_status})
```

---

## Core Components

### `ValidationOutcome`

Enum of the four possible verdicts a single validator can return.

| Value | Meaning |
|---|---|
| `VERIFIED` | Checks passed — event is trustworthy |
| `NEEDS_MANUAL_REVIEW` | Cannot decide automatically — needs human review |
| `REJECTED` | Event is invalid or fraudulent |
| `PENDING_MORE_DATA` | Supporting data not yet available — revisit later |

---

### `ValidationResult`

Dataclass produced by every `BaseValidator.validate()` call.

| Field | Type | Purpose |
|---|---|---|
| `outcome` | `ValidationOutcome` | The verdict |
| `validator_name` | `str` | Set by engine automatically |
| `reasons` | `list[str]` | Human-readable explanations |
| `evidence` | `dict[str, Any]` | Structured data used to reach the verdict |
| `warnings` | `list[str]` | Non-blocking observations |
| `enrichment_data` | `dict[str, Any]` | Data to merge into `event_metadata` |

Factory methods enforce required fields:

```python
ValidationResult.verified(warnings=["minor gap"])
ValidationResult.rejected(["claimed litres exceed tank capacity"], evidence={...})
ValidationResult.needs_review(["no receipt attached"])
ValidationResult.pending_more_data(["GPS fix pending"])
```

---

### `ValidationContext`

Frozen dataclass passed to every validator. Read-only.

| Field | Type | Purpose |
|---|---|---|
| `event` | `OperationalEventResponse` | The event being validated |
| `extra` | `dict[str, Any]` | Additional data pre-fetched by the engine |

Convenience properties: `context.raw_payload`, `context.capture_method`

---

### `BaseValidator`

Abstract base class. Every concrete validator must implement:

| Method | Signature | Purpose |
|---|---|---|
| `applies_to` | `async (context) → bool` | Return `True` to run; `False` to skip |
| `validate` | `async (context) → ValidationResult` | Perform the check |

Validators must be **stateless**. All input comes through `ValidationContext`.
All output is expressed through `ValidationResult`.

```python
class FuelQuantityValidator(BaseValidator):
    name = "fuel_quantity_validator"

    async def applies_to(self, context: ValidationContext) -> bool:
        return context.event.event_type == EventType.FUEL_FILLED

    async def validate(self, context: ValidationContext) -> ValidationResult:
        litres = (context.raw_payload or {}).get("liters", 0)
        if litres > 200:
            return ValidationResult.rejected(["Exceeds max tank capacity"])
        return ValidationResult.verified()
```

---

### `ValidationEngine`

Orchestrates all registered validators. Implements `EventSubscriber`.

**Aggregation rules (priority order):**

| Rule | Condition | Final Status |
|---|---|---|
| 1 | Any `REJECTED` | `REJECTED` |
| 2 | Any `NEEDS_MANUAL_REVIEW` (no REJECTED) | `DISPUTED` |
| 3 | Any `PENDING_MORE_DATA` (no above) | `PENDING` |
| 4 | All `VERIFIED` | `VERIFIED` |
| 5 | No validators ran | `PENDING` (conservative default) |

**Enrichment namespacing:**

All `enrichment_data` from validators is merged into `event.event_metadata["vee"]`,
namespaced by `validator_name` to prevent collisions:

```json
{
  "vee": {
    "fuel_quantity_validator": { "price_per_litre": 91.0 },
    "validation_summary": {
      "validators_run": ["fuel_quantity_validator"],
      "outcomes": { "fuel_quantity_validator": "VERIFIED" },
      "final_status": "VERIFIED"
    }
  }
}
```

---

## Validation Flow

```
1. Event persisted → EventDispatcher.publish(event)
2. ValidationEngine.handle(event) called
3. ValidationContext built
4. For each validator:
   a. applies_to(context) → skip if False
   b. validate(context) → ValidationResult
   c. validator_name stamped on result by engine
5. Aggregate all outcomes → final VerificationStatus
6. Merge all enrichment_data → event_metadata["vee"]
7. Write merged metadata via OperationalEventService.update_metadata()
8. Write final status via OperationalEventService.apply_update()
```

---

## Files Created

| File | Purpose |
|---|---|
| `backend/validation/__init__.py` | Package — exports all five public components |
| `backend/validation/validation_outcome.py` | `ValidationOutcome` enum |
| `backend/validation/validation_result.py` | `ValidationResult` dataclass + factory methods |
| `backend/validation/validation_context.py` | `ValidationContext` frozen dataclass |
| `backend/validation/base_validator.py` | `BaseValidator` ABC |
| `backend/validation/validation_engine.py` | `ValidationEngine` — orchestrator + `EventSubscriber` |

## Files Modified

None. The Event Platform is not modified.

> [!NOTE]
> The `ValidationEngine` is designed to be registered in `main.py` at startup
> alongside the `EventDispatcher`. This wiring is left for the next milestone
> when the first concrete validator (Fuel) is ready, so the engine has
> meaningful work to do before it is connected to live traffic.

---

## Current Limitations

- **No validators registered** — the engine is wired but has no rules.
  Events will remain `PENDING` until fuel (and other) validators are added.
- **No pre-fetch mechanism** — `ValidationContext.extra` is currently always
  empty. The engine does not yet fetch historical data (e.g. fuel averages)
  before running validators. This will be added when the first validator
  needs it.
- **No retry for `PENDING_MORE_DATA`** — events that land in this state are
  not automatically re-queued. A polling or event-triggered re-validation
  mechanism is needed in a future milestone.
- **Single-pass only** — the engine runs validators once per event. Multi-pass
  (e.g. re-validate after enrichment) is not yet supported.
- **Service requires an `AsyncSession`** — the `ValidationEngine` holds an
  `OperationalEventService` instance which needs a database session. When
  registered as a subscriber, the session must be correctly scoped (per
  dispatch, not per request).

---

## Next Milestone

**Milestone 10 — Fuel Validation Rules**

Implement:
- `FuelQuantityValidator` — validate claimed litres against vehicle tank capacity.
- `FuelPriceValidator` — compare reported price per litre against market range.
- `FuelDuplicateValidator` — detect duplicate fuelling events within a time window.
- Register `ValidationEngine` with `EventDispatcher` in `main.py`.
- Register fuel validators with the engine at startup.
