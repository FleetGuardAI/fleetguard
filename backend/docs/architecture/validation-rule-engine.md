# Validation Rule Engine Architecture

The FleetGuard Validation Rule Engine acts as the definitive trust arbiter for all incoming operational events. It is a completely generic, rule-driven orchestration layer that separates business logic from infrastructure.

## Design Philosophy

- **Rule Isolation**: Rules are atomic. A single rule failing or crashing cannot break the engine.
- **Stateless Execution**: Rules do *not* query the database directly. All required context (the `EvidencePackage`, historical `business_state`, and `configuration`) is pre-loaded by the Orchestrator and passed as a `ValidationContext`.
- **Severity-based Outcomes**: Rules do not dictate the final event verdict directly. They emit a `RuleResult` with a specific `RuleSeverity` (CRITICAL, WARNING, INFO), which the Orchestrator interprets into the final trust state (`VERIFIED`, `REJECTED`, `DISPUTED`).

## Core Components

### 1. The Request (`ValidationContext`)
When the `EvidencePackage` is ready, the `ValidationConsumer` triggers the `ValidationService`, which builds the `ValidationContext`. 
This context includes:
- The base `OperationalEvent`
- The `EvidencePackage` (collection statuses and evidence IDs)
- The raw `evidence_records`
- The current `business_state` (if required by rules)

### 2. The Plugin Lifecycle (`BaseValidationRule`)
Developers implement new validation rules by extending `BaseValidationRule`:
- `category`: Identifies the type of validation (e.g., `STRUCTURAL`, `FRAUD`, `COMPLIANCE`).
- `priority`: Determines the execution order (lowest number executes first).
- `applies_to(context)`: Synchronously determines if the rule is relevant.
- `evaluate(context)`: Asynchronously runs the logic and returns a `RuleResult`.

### 3. The Executor (`RuleExecutor`)
To ensure operational resilience, the `ValidationEngine` does not execute rules directly. It delegates to the `RuleExecutor`. 
The executor is responsible for:
- Catching unhandled exceptions from rules.
- Emitting execution metrics and traces (future capability).
- Enforcing rule timeouts (future capability).
- Managing parallel execution (future capability).

If a rule crashes, the `RuleExecutor` swallows the exception and translates it into a `WARNING` severity result. This prevents one poorly written rule from discarding a valid operational event, but still flags the event as `DISPUTED` for human review.

### 4. Verdict Mapping
The engine computes the final verdict based on aggregated rule severities:
- If *any* rule returns `CRITICAL` failure → `REJECTED`
- If *any* rule returns `WARNING` failure → `DISPUTED`
- If all rules pass (or only emit `INFO` failures) → `VERIFIED`
