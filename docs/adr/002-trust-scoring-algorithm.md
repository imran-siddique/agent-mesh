# ADR-002: 5-Dimension Weighted Trust Scoring (0–1000)

## Status

Accepted

## Context

AgentMesh needs a trust scoring system that captures multiple facets of agent
trustworthiness. A single scalar "reputation" value is insufficient because an agent
might be highly competent but have poor security hygiene, or be fully compliant but
unreliable in availability.

Design requirements:

1. **Granularity**: Scores must be fine-grained enough to distinguish between agents at
   similar trust levels and to detect gradual degradation.
2. **Dimension isolation**: A drop in one dimension (e.g., resource efficiency) should
   not automatically tank the entire score — each dimension must be independently
   observable.
3. **Configurable weights**: Different deployments (e.g., healthcare vs. e-commerce) need
   different emphasis — security-heavy vs. collaboration-heavy.
4. **Decay model**: Scores must degrade over time without positive signals to prevent
   stale high-trust agents from operating unchecked.
5. **Threshold-driven actions**: Specific score thresholds must trigger automatic
   governance actions (revocation, warnings, tier promotion).

Alternatives considered:

- **Binary trust (trusted/untrusted)**: Too coarse; no path for gradual trust building.
- **Single 0–100 score**: Insufficient granularity and no dimension visibility.
- **0.0–1.0 float**: Floating-point comparison issues in policy rules; less intuitive
  for operators.
- **Unbounded score**: No natural ceiling makes threshold definition arbitrary.

## Decision

Adopt a **5-dimension weighted scoring system on a 0–1000 integer scale**.

### Dimensions and Default Weights

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Policy Compliance | 0.25 | Adherence to governance rules |
| Security Posture | 0.25 | Credential hygiene, vulnerability posture |
| Output Quality | 0.20 | Task success rate, accuracy |
| Resource Efficiency | 0.15 | Compute/token usage vs. budget |
| Collaboration Health | 0.15 | Responsiveness, protocol compliance |

### Calculation

Each dimension is scored independently on 0–100, then combined:

```
TrustScore = round(
    (policy_compliance  × 0.25 +
     security_posture   × 0.25 +
     output_quality     × 0.20 +
     resource_efficiency × 0.15 +
     collaboration_health × 0.15) × 10
)
```

The `× 10` scaling maps the 0–100 weighted average to the 0–1000 output range.

### Decay Model

- **Rate**: −2.0 points per hour without positive signals
- **Floor**: Score cannot drop below 100 (prevents permanent lockout)
- **Recency weighting**: Signals from the last 24 hours carry full weight; older signals
  age out
- **Regime detection**: KL divergence > 0.5 triggers regime shift alert, propagated to
  neighbors (factor: 0.3, depth: 2 hops)

### Thresholds

| Threshold | Score | Action |
|-----------|-------|--------|
| Revocation | < 300 | Credentials revoked, agent blacklisted |
| Warning | < 500 | Alert raised, capabilities restricted |
| Standard | ≥ 500 | Normal operation |
| Trusted | ≥ 700 | Full collaboration, TrustBridge default |
| Verified Partner | ≥ 900 | Maximum privileges |

## Consequences

### Positive

- **Granularity**: 1000 discrete levels provide fine-grained differentiation; policy
  rules can use exact thresholds (e.g., `score >= 750`).
- **Dimension isolation**: Operators can inspect per-dimension scores in the API response
  to diagnose why an agent's trust dropped, without the dimensions bleeding into each
  other.
- **Configurable weights**: Deployers override weights via configuration — a healthcare
  deployment can set `security_posture: 0.40` while reducing `resource_efficiency: 0.05`.
  Weights are validated to sum to 1.0.
- **Integer comparison**: No floating-point edge cases in policy evaluation; threshold
  checks are simple integer comparisons.
- **Decay prevents stale trust**: An agent that stops interacting gradually loses trust,
  forcing re-engagement before operating at high privilege levels.

### Negative

- **Weight tuning complexity**: Five weights with a sum-to-1.0 constraint require
  careful tuning. Mitigated by providing sensible defaults and the `WeightOptimizer`
  A/B testing utility in `reward/learning.py`.
- **Dimension boundary ambiguity**: Some signals (e.g., "failed authentication") could
  map to Security Posture or Policy Compliance. Mitigated by documenting canonical
  signal-to-dimension mappings in `reward/engine.py`.
- **Decay rate sensitivity**: A fixed −2 pts/hr may be too aggressive for infrequently
  used agents or too lenient for high-frequency ones. Mitigated by making the decay rate
  configurable per deployment.
