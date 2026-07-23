# Evidence Framework

## Overview
The Evidence Framework provides the immutable, strongly-typed foundation for the Fleet Intelligence Engine. It safely organizes heterogeneous evidence captured from various fleet operations, enabling downstream Intelligence Checks to operate on concrete facts without dealing with serialization or orchestration logic.

## Responsibilities
**What it does:**
- Enforces strict immutability of gathered evidence.
- Provides type-safe domain models for different evidence categories (e.g., GPS, Fuel Sensors, Receipts).
- Gracefully handles missing evidence without crashing.
- Organizes multi-source evidence (e.g., multiple GPS devices) safely and efficiently.

**What it intentionally does NOT do:**
- It does NOT perform business logic, validation, or risk calculation.
- It does NOT perform duplicate resolution (orchestrators must resolve duplicates before building the package).
- It does NOT serialize or deserialize data natively in its registry.

## Evidence Lifecycle
Evidence flows through the platform strictly as Read-Only facts:
1. **Evidence Provider**: External systems (Telematics, OCR) emit raw data.
2. **Evidence Builder**: The system standardizes raw data and resolves identity duplicates.
3. **Evidence Package**: The builder constructs an immutable `EvidencePackage`.
4. **Checks**: Pure functions consume the `EvidencePackage` to answer objective questions.
5. **Assessments**: Business aggregators compile check results to formulate domain intelligence.

## BaseEvidence
`BaseEvidence` is the abstract foundation for all evidence. It is a frozen Pydantic model.
**Fields:**
- `evidence_id` (UUID): The unique identity of the evidence piece.
- `evidence_type` (str): The domain category (e.g., "GPSEvidence").
- `source` (str): The logical system that generated the data (e.g., "telematics_gateway").
- `origin` (str): The specific hardware or sub-system (e.g., "vehicle_tracker_v1").
- `collected_at` (datetime): When the fact occurred.
- `reliability` (Reliability Enum): The inherent trustworthiness of the source.
- `metadata` (dict): Extraneous non-business data for debugging.

*Why only shared metadata?* To strictly enforce type safety. Business attributes must be explicitly defined on the subclasses rather than hidden in a generic dictionary.

## Strongly Typed Evidence
Each subclass (e.g., `ReceiptEvidence`) defines explicit properties (e.g., `quantity`, `amount`, `station_name`). This completely removes the ambiguity and runtime errors associated with schema-less `payload` dictionaries, ensuring maximum type safety for downstream Checks.

## Reliability
The `Reliability` enum (`UNKNOWN`, `LOW`, `MEDIUM`, `HIGH`, `VERIFIED`) provides a typed, standardized measure of source trustworthiness, moving away from arbitrary floating-point scores. This allows Policy Engines to easily define rules like "Require HIGH reliability for payments."

## Evidence Provenance
Fields like `source`, `origin`, and `collected_at` preserve the exact lineage of the evidence. This provenance is critical for the Explainability Model, allowing fleet managers to audit exactly which physical sensor or software version contributed to a Risk Assessment.

## EvidencePackage
The `EvidencePackage` is a READ-ONLY container.
- **Immutability**: Contains no mutator methods. Once constructed, it cannot be altered.
- **Retrieval**: Provides `get_evidence(Type)` for fetching the primary source and `get_all_evidence(Type)` for fetching all multi-source objects of a category.
- **Available Types**: `available_types()` lists the classes currently materialized in the package.
- **Duplicate Policy**: The constructor forcefully rejects duplicate *Evidence Identities* (`evidence_id`). However, it gracefully accepts multiple objects of the same *Evidence Category* (e.g., two distinct `GPSEvidence` objects representing a truck's tracker and a driver's phone).
- **Missing Evidence**: Lookups for non-existent evidence return `None` natively. Exceptions are never thrown, fully supporting Adaptive Intelligence.

## EvidenceRegistry
The `EvidenceRegistry` enables dynamic discovery of evidence subclasses.
- **Registration**: Classes are registered via `register()`, which strictly validates the presence of an `evidence_type`.
- **Lookup**: Builders use `get_class(evidence_type_string)` to dynamically find the correct constructor.
- **Future Extensibility**: New evidence domains can register themselves on startup without modifying core engine code.

## Public API

### `EvidencePackage`
```python
# Construct safely (Fails fast on duplicate evidence_ids)
package = EvidencePackage([gps_evidence, receipt_evidence])

# Retrieve primary evidence (Returns None if missing)
gps = package.get_evidence(GPSEvidence)

# Retrieve all evidence of a category (Returns [] if missing)
all_sensors = package.get_all_evidence(FuelSensorEvidence)

# Check existence
if package.has_evidence(ReceiptEvidence):
    print("Receipt found!")

# Flatten all evidence across types
all_facts = package.iterate_all()
```

### `EvidenceRegistry`
```python
registry = EvidenceRegistry()
registry.register(TyreSensorEvidence)
cls = registry.get_class("TyreSensorEvidence")
```

## Extension Guide
To introduce a new evidence type:
1. Create a frozen Pydantic subclass of `BaseEvidence`.
2. Define its `evidence_type` string default.
3. Define its strongly-typed business properties.
4. Call `EvidenceRegistry().register(NewEvidenceClass)` during application bootstrap.
5. The `EvidencePackage` will immediately support storing and retrieving the new type safely.

## Best Practices
- **Embrace Missing Data**: Design Checks to gracefully handle `get_evidence() -> None`.
- **Prefer `get_all_evidence()`**: When writing Checks for multi-source environments (e.g., dual fuel tanks), explicitly iterate over all returned evidence.

## Anti-Patterns
- **Don't mutate evidence**: Pydantic `frozen=True` will block this.
- **Don't place business logic inside evidence**: Evidence is a struct, not a service.
- **Don't use generic payload dictionaries**: If you need a new field, add it to the subclass schema explicitly.
- **Don't access databases from evidence objects**: Stay completely isolated from infrastructure.
- **Don't silently override duplicate evidence**: Resolve duplicate IDs *before* constructing the `EvidencePackage`.

## Testing Strategy
The unit tests in `test_evidence_framework.py` comprehensively cover:
- Pydantic validation and strict immutability.
- Multi-source same-category ingestion in the package.
- Duplicate `evidence_id` rejection on construction.
- Retrieval speed and missing-evidence handling.
- Dynamic registry constraints.

## Developer Notes
When building the `EvidencePackage`, ensure your Orchestrator strictly deduplicates inputs (e.g., discarding older duplicate GPS points) to prevent the `EvidencePackage` from raising `ValueError` halts.
