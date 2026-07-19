# ADR 001: Validation Engine vs. Fleet Intelligence Engine

## Decision
The platform will strictly separate physical data constraints (Validation Engine) from probabilistic and behavioral risk scoring (Fleet Intelligence Engine). The Validation Engine executes first, and events failing validation are immediately rejected. The Intelligence Engine only evaluates events that pass structural and physical validation.

## Context
FleetGuard handles operational events from heterogeneous sources. Early designs proposed a unified "Rules Engine" to evaluate everything about an event. However, this approach dangerously blurred the lines between two fundamentally different categories of rules:
1. **Physical Impossibility**: A truck with a 200L tank claiming to fill 500L is physically impossible. This is a hard structural failure.
2. **Behavioral Anomaly**: A truck filling 100L at an unknown location at 3 AM is physically possible, but highly suspicious. This is a probabilistic risk.

Mixing these concepts into a single engine makes policies extremely difficult to manage. A physical impossibility isn't a "High Risk"—it's an invalid event. Treating it as a risk dilutes the meaning of risk scoring.

## Alternatives Considered
- **Single Unified Engine**: Treat physical impossibilities as "CRITICAL" risks. 
  - *Drawback*: Requires downstream systems to handle fundamentally broken data (e.g., negative fuel quantities) rather than blocking it at the perimeter.
- **Subsuming Validation into Intelligence**: Run everything through Intelligence and let the Global Policy Engine decide what to do with physical failures.
  - *Drawback*: Subsuming validation forces pure intelligence algorithms to defend against garbage data, complicating fraud detection models.

## Consequences
- **Positive**: The Intelligence Engine operates purely on sanitized, physically possible data, drastically simplifying behavioral algorithms and pure checks.
- **Positive**: Hard failures (rejections) are immediately captured at the edge, saving expensive intelligence compute cycles.
- **Negative**: Maintainers must consciously decide whether a new rule belongs in Validation (impossible) or Intelligence (improbable).
