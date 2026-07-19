# ADR 002: Immutable, Strongly Typed Evidence Framework

## Decision
The Fleet Intelligence Engine will consume evidence wrapped in an immutable, strongly-typed domain model (`BaseEvidence` and its subclasses). Evidence objects will contain exactly zero business logic, validation rules, or database access layers. Furthermore, the `EvidencePackage` container will reject true identity duplicates at construction but gracefully allow multi-source evidence of the same domain category.

## Context
FleetGuard operational events trigger a variety of evidence gathering mechanisms (e.g., OCR parsers, GPS trackers). In the past, "evidence" was often passed around as weakly typed JSON bags or generic dictionary payloads. This led to:
- Frequent `KeyError`s in downstream logic.
- Difficulty tracing where a specific piece of evidence came from (loss of provenance).
- Silent mutations of evidence properties across the pipeline.

To implement an Explainable Intelligence Engine, the system must guarantee that the facts evaluated by the engine remain identical to the facts logged in the final decision tree.

## Alternatives Considered
- **Generic Payload Dictionaries**: Allow an `Evidence` class with a `payload: dict` property.
  - *Drawback*: Eliminates type safety. Downstream checks must guess the payload structure or perform extensive manual type conversions.
- **Mutable Evidence Objects**: Allow checks to "enrich" evidence objects in-place.
  - *Drawback*: Destroys explainability. If a Check mutates evidence, subsequent Checks are evaluating modified facts rather than raw facts.
- **Strict Single-Type Constraints**: Reject all duplicates of a category (e.g., allow only one `GPSEvidence`).
  - *Drawback*: Real-world fleets frequently employ multiple devices (e.g., Truck GPS and Driver Phone GPS). Forcing a 1:1 mapping drops valuable corroborating evidence.

## Consequences
- **Positive**: Strict immutability (`frozen=True`) mathematically proves that the evidence used by the Risk Engine is untouched from creation.
- **Positive**: Strong typing forces developers to model business domains correctly (e.g., explicitly defining `latitude` instead of dumping a map dict).
- **Positive**: Multi-source support naturally accommodates complex customer environments.
- **Negative**: Adds mild friction when creating new evidence types, as a strict Python subclass must be defined and registered rather than simply pushing a JSON object into a generic bucket.
