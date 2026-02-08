# Policy Propagation

Policies in AgentMesh are declarative YAML/JSON documents evaluated at runtime.  
This document explains how policies are loaded, matched, and enforced.

## Policy Lifecycle

```
1. Author writes YAML/JSON policy
2. PolicyEngine.load_policy() parses and stores it
3. On every agent action → evaluate() runs matching rules in priority order
4. Decision is returned (<5 ms) and logged in the audit chain
5. Shadow mode allows dry-run without enforcement
```

## Policy Format

```yaml
version: "1.0"
name: api-rate-limit
description: Prevent API quota exhaustion
agent: "*"                         # or a specific did:mesh:<hash>
default_action: allow
rules:
  - name: rate-limit-external-api
    description: Max 100 API calls per hour
    condition: "action == 'api_call' and resource == 'external'"
    action: deny
    limit: "100/hour"
    priority: 10
    enabled: true

  - name: require-approval-for-delete
    description: Destructive actions need human approval
    condition: "action == 'delete'"
    action: require_approval
    approvers: ["admin@example.com"]
    priority: 5
```

## Condition Expressions

Conditions are evaluated against a context dictionary:

| Syntax | Example | Meaning |
|--------|---------|---------|
| `==` | `action == 'read'` | Equality |
| `!=` | `outcome != 'error'` | Inequality |
| `and` | `action == 'write' and resource == 'db'` | Logical AND |
| `or` | `role == 'admin' or role == 'lead'` | Logical OR |
| dot path | `agent.tier == 'trusted'` | Nested dict traversal |

## Loading Policies

```python
from agentmesh.governance import PolicyEngine, Policy

engine = PolicyEngine()

# From YAML string
policy = engine.load_yaml("""
version: "1.0"
name: no-pii
agent: "*"
rules:
  - name: block-pii-logging
    condition: "data.contains_pii == True"
    action: deny
    priority: 1
""")

# From JSON string
policy = engine.load_json('{"version":"1.0","name":"audit-all", ...}')

# Or load a pre-parsed Policy object
engine.load_policy(policy)
```

## Evaluating Actions

```python
decision = engine.evaluate(
    agent_did="did:mesh:abc123",
    context={
        "action": "api_call",
        "resource": "external",
        "data": {"payload_size": 1024},
    }
)

if decision.allowed:
    proceed()
else:
    print(f"Denied by {decision.matched_rule}: {decision.reason}")
    # decision.rate_limited is True if the rule has a limit
    # decision.rate_limit_reset is a UNIX timestamp
```

## PolicyDecision Fields

| Field | Type | Description |
|-------|------|-------------|
| `allowed` | `bool` | Whether the action is permitted |
| `action` | `str` | Rule action: allow, deny, warn, require_approval, log |
| `matched_rule` | `str` | Name of the rule that matched |
| `policy_name` | `str` | Name of the parent policy |
| `reason` | `str` | Human-readable explanation |
| `approvers` | `list[str]` | Who must approve (for require_approval) |
| `rate_limited` | `bool` | True if denied due to rate limit |
| `rate_limit_reset` | `float` | When the rate-limit window resets (UNIX timestamp) |
| `evaluation_ms` | `float` | Time taken to evaluate (typically <5 ms) |

## Rule Priority

Rules are evaluated in ascending `priority` order (lower = evaluated first).  
The **first matching rule** determines the outcome. If no rule matches, `default_action` applies.

## Rate Limiting

Use the `limit` field in format `<count>/<window>`:

| Value | Meaning |
|-------|---------|
| `100/hour` | 100 invocations per rolling hour |
| `10/minute` | 10 invocations per rolling minute |
| `1000/day` | 1000 invocations per rolling day |

When the limit is exceeded, `PolicyDecision.rate_limited = True`.

## Agent Matching

- `agent: "*"` — applies to all agents
- `agent: "did:mesh:abc123"` — applies to a single agent
- `agents: ["did:mesh:abc", "did:mesh:xyz"]` — applies to a list

## Shadow Mode

Test policies without enforcement:

```python
from agentmesh.governance import ShadowMode

shadow = ShadowMode(engine)

# Evaluate without blocking
result = shadow.evaluate("did:mesh:abc", context)
# result.would_deny is True if the policy would have blocked the action
# result.divergence tracks how often shadow differs from production
```

## Propagation to Integrations

When AgentMesh is used through framework integrations (LangGraph, Swarm, Flowise, etc.),
policies propagate automatically:

1. The integration adapter calls `PolicyEngine.evaluate()` before each tool/action.
2. If denied, the integration returns an error to the framework instead of executing.
3. All decisions are logged via the Merkle-chained audit log.
4. Trust scores are updated in the Reward Engine.

This means a single YAML policy file governs agent behavior across all integrated frameworks.

## Audit Integration

Every `evaluate()` call produces an audit entry:

```python
audit_log.log(
    event_type="policy_evaluation",
    agent_did=agent_did,
    action=context["action"],
    outcome="allowed" if decision.allowed else "denied",
    policy_decision=decision.action,
    data={"rule": decision.matched_rule, "policy": decision.policy_name},
)
```

Export as CloudEvents for external ingestion:

```python
events = audit_log.export_cloudevents()
# → list of CloudEvents v1.0 JSON envelopes
```
