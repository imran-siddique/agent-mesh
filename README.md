# AgentMesh

**The Secure Nervous System for Cloud-Native Agent Ecosystems**

*Identity · Trust · Reward · Governance*

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)

---

## Overview

AgentMesh is the first platform purpose-built for the **Governed Agent Mesh** — the cloud-native, multi-vendor network of AI agents that will define enterprise operations.

The protocols exist (A2A, MCP, IATP). The agents are shipping. **The trust layer does not.** AgentMesh fills that gap.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AGENTMESH ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  LAYER 4  │  Reward & Learning Engine                                       │
│           │  Per-agent trust scores · Multi-dimensional rewards · Adaptive  │
├───────────┼─────────────────────────────────────────────────────────────────┤
│  LAYER 3  │  Governance & Compliance Plane                                  │
│           │  Policy engine · EU AI Act / SOC2 / HIPAA · Merkle audit logs   │
├───────────┼─────────────────────────────────────────────────────────────────┤
│  LAYER 2  │  Trust & Protocol Bridge                                        │
│           │  A2A · MCP · IATP · Protocol translation · Capability scoping   │
├───────────┼─────────────────────────────────────────────────────────────────┤
│  LAYER 1  │  Identity & Zero-Trust Core                                     │
│           │  Agent CA · Ephemeral creds · SPIFFE/SVID · Human sponsors      │
└───────────┴─────────────────────────────────────────────────────────────────┘
```

## Why AgentMesh?

### The Problem

- **40:1 to 100:1** — Non-human identities now outnumber human identities in enterprises
- **AI agents** are the fastest-growing, least-governed identity category
- **A2A gives agents a common language. MCP gives agents tools. Neither enforces trust.**

### The Solution

AgentMesh provides:

| Capability | Description |
|------------|-------------|
| **Agent Identity** | First-class identity with human sponsor accountability |
| **Ephemeral Credentials** | 15-minute TTL by default, auto-rotation |
| **Protocol Bridge** | Native A2A, MCP, IATP with unified trust model |
| **Reward Engine** | Continuous behavioral scoring, not static rules |
| **Compliance Automation** | EU AI Act, SOC 2, HIPAA, GDPR mapping |

## Quick Start

```bash
# Install AgentMesh
pip install agentmesh-platform

# Initialize a governed agent in 30 seconds
agentmesh init --name my-agent --sponsor alice@company.com

# Register with the mesh
agentmesh register

# Start with governance enabled
agentmesh run
```

## Installation

```bash
pip install agentmesh-platform
```

Or install with extra dependencies:

```bash
pip install agentmesh-platform[server]  # FastAPI server
pip install agentmesh-platform[dev]     # Development tools
```

Or from source:

```bash
git clone https://github.com/imran-siddique/agent-mesh.git
cd agent-mesh
pip install -e .
```

## Examples & Integrations

**Real-world examples** to get started quickly:

| Example | Use Case | Key Features |
|---------|----------|--------------|
| [MCP Tool Server](./examples/01-mcp-tool-server/) | Secure MCP server with governance | Rate limiting, output sanitization, audit logs |
| [Multi-Agent Customer Service](./examples/02-customer-service/) | Customer support automation | Delegation chains, trust handshakes, A2A |
| [Healthcare HIPAA](./examples/03-healthcare-hipaa/) | HIPAA-compliant data analysis | Compliance automation, PHI protection, Merkle audit |
| [GitHub PR Review](./examples/05-github-integration/) | Code review agent | Output policies, shadow mode, trust decay |

**Framework integrations:**
- [LangChain Integration](./examples/integrations/langchain.md) - Secure LangChain agents with policies
- [CrewAI Integration](./examples/integrations/crewai.md) - Multi-agent crew governance

📚 **[Browse all examples →](./examples/)**

## Core Concepts

### 1. Agent Identity

Every agent gets a unique, cryptographically bound identity:

```python
from agentmesh import AgentIdentity

identity = AgentIdentity.create(
    name="data-analyst-agent",
    sponsor="alice@company.com",  # Human accountability
    capabilities=["read:data", "write:reports"],
)
```

### 2. Delegation Chains

Agents can delegate to sub-agents, but scope **always narrows**:

```python
# Parent agent delegates to child
child_identity = parent_identity.delegate(
    name="summarizer-subagent",
    capabilities=["read:data"],  # Subset of parent's capabilities
)
```

### 3. Trust Handshakes (IATP)

Cross-agent communication requires trust verification:

```python
from agentmesh import TrustBridge

bridge = TrustBridge()

# Verify peer before communication
verification = await bridge.verify_peer(
    peer_id="did:mesh:other-agent",
    required_trust_score=700,
)

if verification.verified:
    await bridge.send_message(peer_id, message)
```

### 4. Reward Scoring

Every action is scored across multiple dimensions:

```python
from agentmesh import RewardEngine

engine = RewardEngine()

# Actions are automatically scored
score = engine.get_agent_score("did:mesh:my-agent")
# {
#   "total": 847,
#   "dimensions": {
#     "policy_compliance": 95,
#     "resource_efficiency": 82,
#     "output_quality": 88,
#     "security_posture": 91,
#     "collaboration_health": 84
#   }
# }
```

### 5. Policy Engine

Declarative governance policies:

```yaml
# policy.yaml
version: "1.0"
agent: "data-analyst-agent"

rules:
  - name: "no-pii-export"
    condition: "action.type == 'export' and data.contains_pii"
    action: "deny"
    
  - name: "rate-limit-api"
    condition: "action.type == 'api_call'"
    limit: "100/hour"
    
  - name: "require-approval-for-delete"
    condition: "action.type == 'delete'"
    action: "require_approval"
    approvers: ["security-team"]
```

## Protocol Support

| Protocol | Status | Description |
|----------|--------|-------------|
| A2A | ✅ Alpha | Agent-to-agent coordination |
| MCP | ✅ Alpha | Tool and resource binding |
| IATP | ✅ Alpha | Trust handshakes (via agent-os) |
| ACP | 🔄 Beta | Lightweight messaging |
| SPIFFE | ✅ Alpha | Workload identity |

## Architecture

```
agentmesh/
├── identity/           # Layer 1: Identity & Zero-Trust
│   ├── agent_id.py     # Agent identity management
│   ├── credentials.py  # Ephemeral credential issuance
│   ├── delegation.py   # Delegation chains
│   └── spiffe.py       # SPIFFE/SVID integration
│
├── trust/              # Layer 2: Trust & Protocol Bridge
│   ├── bridge.py       # Protocol bridge
│   ├── handshake.py    # Trust handshakes
│   └── capability.py   # Capability scoping
│
├── protocols/          # Protocol implementations
│   ├── a2a/            # A2A support
│   ├── mcp/            # MCP support
│   └── iatp/           # IATP (uses agent-os)
│
├── governance/         # Layer 3: Governance & Compliance
│   ├── policy.py       # Policy engine
│   ├── compliance.py   # Compliance mapping
│   ├── audit.py        # Merkle-chained audit logs
│   └── shadow.py       # Shadow mode
│
├── reward/             # Layer 4: Reward & Learning
│   ├── engine.py       # Reward engine
│   ├── scoring.py      # Multi-dimensional scoring
│   └── learning.py     # Adaptive learning
│
├── cli/                # Command-line interface
└── sdk/                # Python SDK
```

## Compliance

AgentMesh automates compliance mapping for:

- **EU AI Act** — Risk classification, transparency requirements
- **SOC 2** — Security, availability, processing integrity
- **HIPAA** — PHI handling, audit controls
- **GDPR** — Data processing, consent, right to explanation

```python
from agentmesh import ComplianceEngine

compliance = ComplianceEngine(frameworks=["soc2", "hipaa"])

# Generate compliance report
report = compliance.generate_report(
    agent_id="did:mesh:healthcare-agent",
    period="2026-01",
)
```

## Threat Model

| Threat | AgentMesh Defense |
|--------|-------------------|
| Prompt Injection | Tool output sanitized at Protocol Bridge |
| Credential Theft | 15-min TTL, instant revocation on trust breach |
| Shadow Agents | Unregistered agents blocked at network layer |
| Delegation Escalation | Chains are cryptographically narrowing |
| Cascade Failure | Per-agent trust scoring isolates blast radius |

## Roadmap

| Phase | Timeline | Deliverables |
|-------|----------|--------------|
| Alpha | Q1 2026 | Identity Core, A2A+MCP bridge, CLI |
| Beta | Q2 2026 | IATP handshake, Reward Engine v1, Dashboard |
| GA | Q3 2026 | Compliance automation, Enterprise features |
| Scale | Q4 2026 | Agent Marketplace, Partner integrations |

## Dependencies

AgentMesh builds on:

- **[agent-os](https://github.com/imran-siddique/agent-os)** — IATP protocol, Nexus trust exchange
- **SPIFFE/SPIRE** — Workload identity
- **OpenTelemetry** — Observability

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Apache 2.0 — See [LICENSE](LICENSE) for details.

---

**Agents shouldn't be islands. But they also shouldn't be ungoverned.**

*AgentMesh is the trust layer that makes the mesh safe enough to scale.*
