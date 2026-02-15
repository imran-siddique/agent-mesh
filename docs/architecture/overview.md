# Architecture Deep-Dive

AgentMesh is a four-layer governance mesh for autonomous AI agents.  
Each layer is independently deployable and communicates via DIDs (Decentralized Identifiers).

## Layer Diagram

```
┌─────────────────────────────────────────────────────┐
│                 Client / Agent SDK                   │
└───────────────┬─────────────────────┬───────────────┘
                │                     │
┌───────────────▼─────────────────────▼───────────────┐
│  L4  Reward Engine                                   │
│  ├── 5-dimension trust scoring                       │
│  ├── Adaptive weight optimisation (A/B experiments)  │
│  └── Automatic revocation below threshold            │
├──────────────────────────────────────────────────────┤
│  L3  Governance Layer                                │
│  ├── Declarative YAML/JSON policy engine (<5 ms)     │
│  ├── Merkle-chained audit log (tamper-evident)       │
│  ├── CloudEvents v1.0 export                         │
│  └── Shadow mode for policy dry-runs                 │
├──────────────────────────────────────────────────────┤
│  L2  Trust Layer                                     │
│  ├── Continuous trust scoring (0–1000)               │
│  ├── DID-based mutual verification                   │
│  ├── Capability-narrowing delegation chains           │
│  └── Tier classification (verified → revoked)        │
├──────────────────────────────────────────────────────┤
│  L1  Identity Layer                                  │
│  ├── did:mesh:<hash> identifiers                     │
│  ├── SPIFFE-compatible SVID generation               │
│  ├── Key rotation & revocation                       │
│  └── Integration DIDs (did:langflow:, did:swarm:…)   │
└──────────────────────────────────────────────────────┘
```

## Directory Map

```
src/agentmesh/
├── identity/          # L1 — DID issuance, key management
├── trust/             # L2 — TrustEngine, delegation, scores
├── governance/        # L3 — PolicyEngine, AuditLog, ShadowMode
│   ├── policy.py      #      Declarative YAML/JSON rules
│   ├── audit.py       #      Merkle-chained log + CloudEvents
│   └── shadow.py      #      Dry-run mode
├── reward/            # L4 — RewardEngine, scoring, learning
│   ├── engine.py      #      Signal processing, revocation
│   ├── scoring.py     #      5 dimensions, tier thresholds
│   └── learning.py    #      A/B experiments, anomaly detection
├── cli/               # CLI (serve, verify, policy, audit)
├── core/              # Shared primitives (Agent, MeshClient)
├── integrations/      # Framework adapters (LangGraph, Swarm…)
├── observability/     # Metrics and tracing hooks
└── storage/           # Pluggable backends (memory, Redis, Postgres)
```

## Request Flow

1. **Agent registers** → L1 issues `did:mesh:<hash>`, stores public key.
2. **Agent requests action** → L3 PolicyEngine evaluates YAML rules (<5 ms).
   - If denied → returns `PolicyDecision(allowed=False)` with suggestion.
   - If allowed → action proceeds.
3. **Audit** → every decision is appended to the Merkle-chained log.
4. **Signal** → L4 RewardEngine receives a `RewardSignal` for the dimension
   (policy_compliance, resource_efficiency, output_quality,
   security_posture, collaboration_health).
5. **Score update** → EMA recalculates the agent's trust score (0–1000).
   Below threshold → automatic revocation callback fires.

## Storage Backends

| Backend | Use case | Status |
|---------|----------|--------|
| In-memory | Unit tests, local dev | ✅ Default |
| Redis | Distributed cache / pub-sub | ✅ Implemented (requires `redis` extras) |
| PostgreSQL | Persistent audit & scores | ✅ Implemented (requires `asyncpg` extras) |

## Protocol Support

| Protocol | Purpose | Integration point |
|----------|---------|-------------------|
| A2A (Google) | Agent-to-agent calls | `src/agentmesh/integrations/a2a/` |
| MCP (Anthropic) | Tool governance proxy | `packages/mcp-proxy/` |
| IATP | Inter-agent trust | Identity layer |
| SPIFFE | Workload identity | SVID generation in L1 |

## Compliance Automation

AgentMesh maps governance primitives to regulatory controls:

- **EU AI Act** → Risk classification, human oversight, audit trail
- **SOC 2** → Access control, monitoring, change management
- **HIPAA** → PHI access logging, minimum necessary principle
- **GDPR** → Data minimisation, consent verification, right to erasure
