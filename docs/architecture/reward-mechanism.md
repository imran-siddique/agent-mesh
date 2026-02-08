# Reward Mechanism

The reward engine (Layer 4) maintains a **continuous trust score** for every agent.  
Scores drive access decisions, delegation limits, and automatic revocation.

## Five Dimensions

| Dimension | Weight | What it measures |
|-----------|--------|------------------|
| `policy_compliance` | 0.30 | Did the agent obey governance rules? |
| `resource_efficiency` | 0.15 | Token / compute usage vs budget |
| `output_quality` | 0.25 | Were outputs accepted or rejected by consumers? |
| `security_posture` | 0.20 | Did the agent stay within security boundaries? |
| `collaboration_health` | 0.10 | Were multi-agent handoffs successful? |

Weights are configurable and can be tuned via A/B experiments (see below).

## Trust Score (0–1000)

Each dimension score (0–100) is updated using an **exponential moving average (EMA)**:

```
new_score = α × signal_value + (1 − α) × previous_score
```

The overall trust score is a weighted sum:

```python
total = Σ (dimension_score × weight × 10)   # 0–1000
```

## Tiers

| Tier | Score Range | Meaning |
|------|-------------|---------|
| `verified_partner` | ≥ 900 | Highest trust — full delegation allowed |
| `trusted` | 700–899 | Standard operations permitted |
| `standard` | 500–699 | Limited scope |
| `probationary` | 300–499 | Under review — warn on every action |
| `untrusted` | < 300 | Revocation triggered automatically |

## Recording Signals

```python
from agentmesh.reward import RewardEngine

engine = RewardEngine()

# Policy compliance
engine.record_policy_compliance("did:mesh:abc", compliant=True, policy_name="rate-limit")

# Resource efficiency
engine.record_resource_usage("did:mesh:abc", tokens_used=500, tokens_budget=1000,
                             compute_ms=120, compute_budget_ms=500)

# Output quality
engine.record_output_quality("did:mesh:abc", accepted=True, consumer="did:mesh:xyz")

# Security posture
engine.record_security_event("did:mesh:abc", within_boundary=True, event_type="api_call")

# Collaboration health
engine.record_collaboration("did:mesh:abc", handoff_successful=True, peer_did="did:mesh:xyz")
```

## Score Explanation

```python
explanation = engine.get_score_explanation("did:mesh:abc")
# {
#   "total_score": 820,
#   "tier": "trusted",
#   "dimensions": {
#     "policy_compliance": {"score": 95, "weight": 0.3, "signals": 42},
#     "resource_efficiency": {"score": 78, "weight": 0.15, "signals": 18},
#     ...
#   },
#   "at_risk": False
# }
```

## Automatic Revocation

When `total_score` drops below the configured `revocation_threshold` (default 300),
the engine fires all registered callbacks:

```python
@engine.on_revocation
def handle_revocation(agent_did: str, reason: str):
    logger.warning(f"Revoking {agent_did}: {reason}")
    # Remove from routing, alert operators, etc.
```

## Adaptive Weight Optimisation

The `WeightOptimizer` runs A/B experiments to find better weight configurations:

```python
from agentmesh.reward.learning import WeightOptimizer

optimizer = WeightOptimizer()

experiment = optimizer.start_experiment(
    name="boost-security-weight",
    control_weights={"security_posture": 0.20, ...},
    treatment_weights={"security_posture": 0.30, ...},
    treatment_pct=0.2,  # 20% of agents get treatment
)

# After collecting data...
if optimizer.should_adopt_treatment(experiment.experiment_id, min_lift_pct=5.0):
    engine.update_weights(**experiment.treatment_weights)
```

## Anomaly Detection

The `AdaptiveLearner` tracks per-agent action patterns and flags statistical outliers:

```python
from agentmesh.reward.learning import AdaptiveLearner

learner = AdaptiveLearner()
anomalies = learner.get_anomalies(since=datetime.utcnow() - timedelta(hours=1))
# Returns actions that deviate >2σ from the agent's historical baseline.
```

## Health Report

```python
report = engine.get_health_report(days=7)
# {
#   "agents_total": 24,
#   "agents_at_risk": ["did:mesh:xyz"],
#   "average_score": 745,
#   "revocations_last_7d": 1
# }
```
