# ADR-003: Chained Delegation vs Flat Authorization

## Status

Accepted

## Context

AgentMesh supports multi-agent workflows where a human sponsor delegates authority to
Agent A, which in turn delegates a subset of that authority to Agent B, and so on. We
needed to choose between two authorization models:

1. **Flat authorization**: Every agent receives capabilities directly from a central
   authority (or the human sponsor). There is no transitive delegation — each agent's
   permissions are independently granted.
2. **Chained delegation**: Capabilities flow through a chain of delegation links.
   Each link narrows the capability set and is cryptographically signed by the
   delegator. Verification walks the chain back to the root sponsor.

Key requirements:

- **Composability**: Agents must be able to sub-delegate tasks to specialist agents
  without requiring the human to individually authorize every agent in the workflow.
- **Least privilege**: Each delegation step must narrow (never widen) the capability
  set — a delegatee cannot gain capabilities the delegator does not possess.
- **Auditability**: It must be possible to trace any agent's authority back to a human
  sponsor for compliance and incident investigation.
- **Revocation**: Revoking a link in the chain must invalidate all downstream links.
- **Bounded depth**: Unbounded chains create verification overhead and make revocation
  propagation slow.

## Decision

Use **chained delegation** with cryptographic link signing, capability narrowing, and
configurable depth limits.

### Chain Structure

```
[Root: Human Sponsor]
    │
    ├─ Ed25519 signature
    │
    ▼
[Link 1: Agent A]
    capabilities: ["read:*", "write:data", "delegate:*"]
    │
    ├─ Ed25519 signature (Agent A's key)
    │
    ▼
[Link 2: Agent B]
    capabilities: ["read:data"]   ← narrowed from "read:*"
    │
    ├─ Ed25519 signature (Agent B's key)
    │
    ▼
[Link 3: Agent C]
    capabilities: ["read:data"]   ← cannot widen beyond parent
```

### Implementation Details

- **DelegationLink**: Each link contains `delegator_did`, `delegatee_did`, `capabilities`,
  `previous_link_hash`, and `signature`. Links form an immutable hash chain.
- **Capability narrowing validation**: Delegatee capabilities must be a subset of
  delegator capabilities. Wildcard narrowing is supported (e.g., `read:*` → `read:data`).
- **Hash chaining**: Each link includes the SHA-256 hash of the previous link, creating
  a tamper-evident chain.
- **Signature verification**: Each link's signature is verified against the delegator's
  Ed25519 public key.
- **On-Behalf-Of (OBO)**: `UserContext` propagates through the chain so downstream agents
  can act on behalf of the original human sponsor.
- **Default max depth**: 3 (configurable via `identity/sponsor.py`).
- **Default max sponsored agents**: 10 per sponsor.

### Verification Algorithm

```
verify_chain(chain):
    for each link in chain:
        1. Verify link.signature against delegator's public key
        2. Verify link.previous_hash matches hash(previous_link)
        3. Verify link.capabilities ⊆ previous_link.capabilities
        4. Verify chain depth ≤ max_delegation_depth
    if all pass: chain is valid
    else: reject with specific failure reason
```

## Consequences

### Positive

- **Composability**: Agents can autonomously sub-delegate to specialist agents without
  human intervention at each step, enabling complex multi-agent workflows.
- **Least privilege by construction**: Capability narrowing is enforced cryptographically
  — it is impossible to create a valid link that widens capabilities.
- **Full auditability**: Every chain can be traced to a human sponsor. The hash chain
  provides tamper evidence for compliance audits.
- **Cascading revocation**: Revoking a link automatically invalidates all downstream
  links because their hash chain becomes broken. Revocation propagation completes
  within ≤ 5 seconds.

### Negative

- **Verification cost**: Walking the chain requires O(depth) signature verifications.
  Mitigated by the depth limit (default 3) and caching of verified chains (15 min TTL).
- **Chain management complexity**: Agents must store and present their full chain for
  every interaction. Mitigated by the `DelegationChain` class which handles chain
  serialization and validation automatically.
- **Depth limit trade-off**: The default depth of 3 may be insufficient for deeply
  nested orchestration patterns. Deployments can increase this, but deeper chains
  increase verification latency and revocation propagation time.
- **Single point of failure**: If the root sponsor's key is compromised, the entire
  chain is compromised. Mitigated by credential TTL (15 min) and SPIFFE SVID rotation.
- **No cycle detection**: The chain model assumes a tree structure rooted at a human
  sponsor. If Agent A delegates to Agent B and Agent B delegates back to Agent A
  (via separate chains), each chain validates independently but the combined delegation
  graph contains a cycle. This can create confused-deputy scenarios and ambiguous
  revocation semantics. **Planned mitigation:** add graph-level cycle detection at
  link creation time by tracking the global delegation graph and rejecting links that
  would introduce cycles.
