# Trust Scoring Algorithm

AgentMesh uses a dynamic trust scoring system to evaluate agent reliability. This document explains how trust scores are calculated and used.

## Overview

Every agent in AgentMesh has a **trust score** between 0.0 (no trust) and 1.0 (full trust). Trust scores:

- Start at a neutral baseline (0.5)
- Increase with successful, compliant behavior
- Decrease with violations or anomalies
- Affect what actions an agent can perform

## Trust Score Formula

```
TrustScore = BaseScore 
           + SuccessFactor 
           + ComplianceFactor 
           + ReputationFactor
           - ViolationPenalty 
           - AnomalyPenalty
           - RecencyDecay
```

### Components

#### Base Score (0.5)
All agents start with a neutral score. This prevents both blind trust and unfair discrimination against new agents.

```python
base_score = 0.5
```

#### Success Factor (0.0 - 0.2)
Rewards successful interactions. Capped to prevent gaming through high volume.

```python
success_factor = min(0.2, successful_interactions * 0.001)
```

| Interactions | Factor |
|-------------|--------|
| 0 | 0.00 |
| 50 | 0.05 |
| 100 | 0.10 |
| 200+ | 0.20 (max) |

#### Compliance Factor (0.0 - 0.2)
Rewards policy compliance. Most impactful factor.

```python
compliance_rate = compliant_actions / total_actions
compliance_factor = 0.2 * compliance_rate
```

| Compliance Rate | Factor |
|----------------|--------|
| 100% | 0.20 |
| 90% | 0.18 |
| 80% | 0.16 |
| 50% | 0.10 |

#### Reputation Factor (0.0 - 0.1)
Endorsements from other trusted agents.

```python
endorsement_score = sum(endorser.trust_score for endorser in endorsers) / len(endorsers)
reputation_factor = 0.1 * endorsement_score if endorsers else 0
```

#### Violation Penalty (0.0 - 0.5)
Policy violations significantly reduce trust.

```python
violation_penalty = min(0.5, policy_violations * 0.1)
```

| Violations | Penalty |
|-----------|---------|
| 0 | 0.00 |
| 1 | 0.10 |
| 3 | 0.30 |
| 5+ | 0.50 (max) |

#### Anomaly Penalty (0.0 - 0.3)
Unusual behavior patterns reduce trust.

```python
anomaly_penalty = min(0.3, anomalous_behaviors * 0.05)
```

Anomalies include:
- Sudden spike in API calls
- Unusual access patterns
- Time-of-day anomalies
- Geographic anomalies

#### Recency Decay
Recent behavior matters more than historical behavior.

```python
decay_factor = 0.95  # Per day
effective_violation_count = sum(
    violation.weight * (decay_factor ** days_since_violation)
    for violation in violations
)
```

## Trust Thresholds

| Score Range | Trust Level | Permissions |
|------------|-------------|-------------|
| 0.0 - 0.2 | **Untrusted** | Read-only, heavily monitored |
| 0.2 - 0.4 | **Low** | Limited actions, approval required |
| 0.4 - 0.6 | **Moderate** | Standard permissions |
| 0.6 - 0.8 | **High** | Extended permissions |
| 0.8 - 1.0 | **Trusted** | Full permissions, can endorse others |

## Trust Score Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    TRUST SCORE LIFECYCLE                     │
│                                                              │
│   ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│   │  NEW    │────►│MODERATE │────►│  HIGH   │              │
│   │  0.5    │     │ 0.4-0.6 │     │ 0.6-0.8 │              │
│   └─────────┘     └────┬────┘     └────┬────┘              │
│                        │               │                    │
│                        ▼               ▼                    │
│   ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│   │UNTRUSTED│◄────│   LOW   │     │ TRUSTED │              │
│   │ 0.0-0.2 │     │ 0.2-0.4 │     │ 0.8-1.0 │              │
│   └─────────┘     └─────────┘     └─────────┘              │
│        │                                                    │
│        ▼                                                    │
│   ┌─────────┐                                              │
│   │ BANNED  │  (5+ violations or trust < 0.1)              │
│   └─────────┘                                              │
└─────────────────────────────────────────────────────────────┘
```

## Implementation

```python
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class TrustScore:
    """Dynamic trust score for an agent."""
    
    agent_did: str
    
    # Positive factors
    successful_interactions: int = 0
    compliant_actions: int = 0
    total_actions: int = 0
    endorsements: list[str] = None  # DIDs of endorsers
    
    # Negative factors
    policy_violations: int = 0
    anomalous_behaviors: int = 0
    failed_authentications: int = 0
    
    # Metadata
    created_at: datetime = None
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.endorsements is None:
            self.endorsements = []
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
    
    def calculate(self, endorser_scores: dict[str, float] = None) -> float:
        """Calculate the current trust score."""
        # Base score
        score = 0.5
        
        # Success factor (0.0 - 0.2)
        score += min(0.2, self.successful_interactions * 0.001)
        
        # Compliance factor (0.0 - 0.2)
        if self.total_actions > 0:
            compliance_rate = self.compliant_actions / self.total_actions
            score += 0.2 * compliance_rate
        
        # Reputation factor (0.0 - 0.1)
        if self.endorsements and endorser_scores:
            endorser_trust = [
                endorser_scores.get(did, 0.5) 
                for did in self.endorsements
            ]
            if endorser_trust:
                avg_endorser_trust = sum(endorser_trust) / len(endorser_trust)
                score += 0.1 * avg_endorser_trust
        
        # Violation penalty (0.0 - 0.5)
        score -= min(0.5, self.policy_violations * 0.1)
        
        # Anomaly penalty (0.0 - 0.3)
        score -= min(0.3, self.anomalous_behaviors * 0.05)
        
        # Auth failure penalty (0.0 - 0.2)
        score -= min(0.2, self.failed_authentications * 0.02)
        
        # Clamp to [0.0, 1.0]
        return max(0.0, min(1.0, score))
    
    @property
    def trust_level(self) -> str:
        """Get the trust level category."""
        score = self.calculate()
        if score >= 0.8:
            return "trusted"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "moderate"
        elif score >= 0.2:
            return "low"
        else:
            return "untrusted"
    
    def record_success(self) -> None:
        """Record a successful interaction."""
        self.successful_interactions += 1
        self.total_actions += 1
        self.compliant_actions += 1
        self.last_updated = datetime.utcnow()
    
    def record_violation(self) -> None:
        """Record a policy violation."""
        self.policy_violations += 1
        self.total_actions += 1
        self.last_updated = datetime.utcnow()
    
    def record_anomaly(self) -> None:
        """Record anomalous behavior."""
        self.anomalous_behaviors += 1
        self.last_updated = datetime.utcnow()
```

## Trust Score API

Query an agent's trust score:

```bash
GET /api/v1/trust/{agent_did}

Response:
{
  "agent_did": "did:agentmesh:alice",
  "score": 0.72,
  "level": "high",
  "factors": {
    "success": 0.15,
    "compliance": 0.18,
    "reputation": 0.09,
    "violations": -0.10,
    "anomalies": -0.10
  },
  "permissions": ["read", "write", "delegate"],
  "updated_at": "2024-01-15T10:30:00Z"
}
```

## Trust Decisions in Policies

Use trust scores in policy conditions:

```yaml
# Policy: Only trusted agents can access sensitive data
rules:
  - name: require-high-trust
    condition: "agent.trust_score >= 0.6"
    action: allow
    
  - name: block-low-trust
    condition: "agent.trust_score < 0.4"
    action: deny
    
  - name: require-approval-moderate
    condition: "agent.trust_score >= 0.4 and agent.trust_score < 0.6"
    action: require_approval
    approvers: ["security-team"]
```

## Best Practices

1. **Don't start at 0**: New agents need to function. Start neutral (0.5).

2. **Cap positive factors**: Prevent trust inflation through volume.

3. **Weight violations heavily**: One violation matters more than 10 successes.

4. **Apply time decay**: Recent behavior is more relevant.

5. **Enable recovery**: Agents should be able to rebuild trust over time.

6. **Monitor for gaming**: Watch for agents artificially inflating scores.

## See Also

- [Zero-Trust Architecture](zero-trust.md)
- [Policy Engine](../src/agentmesh/governance/policy.py)
- [Identity Management](identity.md)
