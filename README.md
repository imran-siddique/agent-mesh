# AgentMesh

**The Secure Nervous System for Cloud-Native Agent Ecosystems**

*Identity · Trust · Reward · Governance*

[![GitHub Stars](https://img.shields.io/github/stars/imran-siddique/agent-mesh?style=social)](https://github.com/imran-siddique/agent-mesh/stargazers)
[![Sponsor](https://img.shields.io/badge/sponsor-❤️-ff69b4)](https://github.com/sponsors/imran-siddique)
[![CI](https://github.com/imran-siddique/agent-mesh/actions/workflows/ci.yml/badge.svg)](https://github.com/imran-siddique/agent-mesh/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Agent-OS Compatible](https://img.shields.io/badge/agent--os-compatible-green.svg)](https://github.com/imran-siddique/agent-os)

> ⭐ **If this project helps you, please star it!** It helps others discover AgentMesh.

> 🔗 **Part of the Agent Ecosystem** — Works seamlessly with [Agent-OS](https://github.com/imran-siddique/agent-os) for IATP trust protocol

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

### Option 1: Secure Claude Desktop (Recommended)

```bash
# Install AgentMesh
pip install agentmesh-platform

# Set up Claude Desktop to use AgentMesh governance
agentmesh init-integration --claude

# Restart Claude Desktop - all MCP tools are now secured!
```

Claude will now route tool calls through AgentMesh for policy enforcement and trust scoring.

### Option 2: Create a Governed Agent

```bash
# Initialize a governed agent in 30 seconds
agentmesh init --name my-agent --sponsor alice@company.com

# Register with the mesh
agentmesh register

# Start with governance enabled
agentmesh run
```

### Option 3: Wrap Any MCP Server

```bash
# Proxy any MCP server with governance
agentmesh proxy --target npx --target -y \
  --target @modelcontextprotocol/server-filesystem \
  --target /path/to/directory

# Use strict policy (blocks writes/deletes)
agentmesh proxy --policy strict --target <your-mcp-server>
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
| [Registration Hello World](./examples/00-registration-hello-world/) | Agent registration walkthrough | Identity, DID, sponsor handshake |
| [MCP Tool Server](./examples/01-mcp-tool-server/) | Secure MCP server with governance | Rate limiting, output sanitization, audit logs |
| [Multi-Agent Customer Service](./examples/02-customer-service/) | Customer support automation | Delegation chains, trust handshakes, A2A |
| [Healthcare HIPAA](./examples/03-healthcare-hipaa/) | HIPAA-compliant data analysis | Compliance automation, PHI protection, Merkle audit |
| [DevOps Automation](./examples/04-devops-automation/) | Just-in-time DevOps credentials | Ephemeral creds, capability scoping |
| [GitHub PR Review](./examples/05-github-integration/) | Code review agent | Output policies, shadow mode, trust decay |

**Framework integrations:**
- **[Claude Desktop](./docs/integrations/claude-desktop.md)** - Secure MCP tools with one command
- [LangChain Integration](./examples/integrations/langchain.md) - Secure LangChain agents with policies
- [CrewAI Integration](./examples/integrations/crewai.md) - Multi-agent crew governance
- [LangGraph](./src/agentmesh/integrations/langgraph/) - Trust checkpoints for graph workflows (built-in)
- [OpenAI Swarm](./src/agentmesh/integrations/swarm/) - Trust-verified handoffs (built-in)
- [Dify](./integrations/dify/) - Trust middleware for Dify workflows

📚 **[Browse all examples →](./examples/)**

## The AgentMesh Proxy: "SSL for AI Agents"

**Problem:** AI agents like Claude Desktop have unfettered access to your filesystem, database, and APIs through MCP servers. One hallucination could be catastrophic.

**Solution:** AgentMesh acts as a transparent governance proxy:

```bash
# Before: Unsafe direct access
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/me"]
    }
  }
}

# After: Protected by AgentMesh
{
  "mcpServers": {
    "filesystem": {
      "command": "agentmesh",
      "args": [
        "proxy", "--policy", "strict",
        "--target", "npx", "--target", "-y",
        "--target", "@modelcontextprotocol/server-filesystem",
        "--target", "/Users/me"
      ]
    }
  }
}
```

**What you get:**
- 🔒 **Policy Enforcement** - Block dangerous operations before they execute
- 📊 **Trust Scoring** - Behavioral monitoring (800-1000 scale)  
- 📝 **Audit Logs** - Tamper-evident record of every action
- ✅ **Verification Footers** - Visual confirmation in outputs

**Set it up in 10 seconds:**
```bash
agentmesh init-integration --claude
# Restart Claude Desktop - done!
```

Learn more: **[Claude Desktop Integration Guide](./docs/integrations/claude-desktop.md)**

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
| A2A | ✅ Alpha | Agent-to-agent coordination (full adapter in `integrations/a2a/`) |
| MCP | ✅ Alpha | Tool and resource binding (trust-gated server/client in `integrations/mcp/`) |
| IATP | ✅ Alpha | Trust handshakes (via [agent-os](https://github.com/imran-siddique/agent-os), graceful fallback if unavailable) |
| ACP | 🔜 Planned | Lightweight messaging (protocol bridge supports routing, adapter not yet implemented) |
| SPIFFE | ✅ Alpha | Workload identity |

## Architecture

```
agentmesh/
├── identity/           # Layer 1: Identity & Zero-Trust
│   ├── agent_id.py     # Agent identity management (DIDs, Ed25519 keys)
│   ├── credentials.py  # Ephemeral credential issuance (15-min TTL)
│   ├── delegation.py   # Cryptographic delegation chains
│   ├── spiffe.py       # SPIFFE/SVID integration
│   ├── risk.py         # Continuous risk scoring
│   └── sponsor.py      # Human sponsor accountability
│
├── trust/              # Layer 2: Trust & Protocol Bridge
│   ├── bridge.py       # Multi-protocol trust bridge (A2A/MCP/IATP/ACP)
│   ├── handshake.py    # IATP trust handshakes
│   ├── cards.py        # Trusted agent cards
│   └── capability.py   # Capability scoping
│
├── governance/         # Layer 3: Governance & Compliance
│   ├── policy.py       # Declarative policy engine (YAML/JSON)
│   ├── compliance.py   # Compliance mapping (EU AI Act, SOC2, HIPAA, GDPR)
│   ├── audit.py        # Merkle-chained audit logs
│   └── shadow.py       # Shadow mode for policy testing
│
├── reward/             # Layer 4: Reward & Learning
│   ├── engine.py       # Multi-dimensional reward engine
│   ├── scoring.py      # 5-dimension trust scoring
│   └── learning.py     # Adaptive learning & weight optimization
│
├── integrations/       # Protocol & framework adapters
│   ├── a2a/            # Google A2A protocol support
│   ├── mcp/            # Anthropic MCP trust-gated server/client
│   ├── langgraph/      # LangGraph trust checkpoints
│   └── swarm/          # OpenAI Swarm trust-verified handoffs
│
├── cli/                # Command-line interface
│   ├── main.py         # agentmesh init/register/status/audit/policy
│   └── proxy.py        # MCP governance proxy
│
├── core/               # Low-level services
│   └── identity/ca.py  # Certificate Authority (SPIFFE/SVID)
│
├── storage/            # Storage abstraction (memory, Redis, PostgreSQL)
│
├── observability/      # OpenTelemetry tracing & Prometheus metrics
│
└── services/           # Service wrappers (registry, audit, reward)
```

## Compliance

AgentMesh automates compliance mapping for:

- **EU AI Act** — Risk classification, transparency requirements
- **SOC 2** — Security, availability, processing integrity
- **HIPAA** — PHI handling, audit controls
- **GDPR** — Data processing, consent, right to explanation

```python
from agentmesh import ComplianceEngine, ComplianceFramework

compliance = ComplianceEngine(frameworks=[ComplianceFramework.SOC2, ComplianceFramework.HIPAA])

# Check an action for violations
violations = compliance.check_compliance(
    agent_did="did:agentmesh:healthcare-agent",
    action_type="data_access",
    context={"data_type": "phi", "encrypted": True},
)

# Generate compliance report
from datetime import datetime, timedelta
report = compliance.generate_report(
    framework=ComplianceFramework.SOC2,
    period_start=datetime.utcnow() - timedelta(days=30),
    period_end=datetime.utcnow(),
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

## Known Limitations & Open Work

> Transparency about what's done and what isn't.

### Not Yet Implemented

| Item | Location | Notes |
|------|----------|-------|
| ACP protocol adapter | `trust/bridge.py` | Bridge routes ACP messages, but no dedicated `ACPAdapter` class yet |
| Service wrapper for audit | `services/audit/` | Core audit module (`governance/audit.py`) is complete; service layer wrapper is a TODO |
| Service wrapper for reward engine | `services/reward_engine/` | Core reward engine (`reward/engine.py`) is complete; service layer wrapper is a TODO |
| Mesh control plane | `services/mesh-control-plane/` | Directory structure exists; implementation is minimal |
| Delegation chain cryptographic verification | `packages/langchain-agentmesh/trust.py` | Simulated verification; full cryptographic chain validation not yet implemented |

### Integration Caveats (Dify)

The [Dify integration](./integrations/dify/) has these documented limitations:
- Request body signature verification (`X-Agent-Signature` header) is not yet verified by middleware
- Trust score time decay is not yet implemented (scores don't decay over time)
- Audit logs are in-memory only (not persistent across multi-worker deployments)
- Environment variable configuration requires programmatic initialization (not auto-wired)

### Infrastructure

- **Redis/PostgreSQL storage providers**: Implemented but require real infrastructure for testing (unit tests use in-memory provider)
- **Kubernetes Operator**: GovernedAgent CRD defined, but no controller/operator to reconcile it
- **SPIRE Integration**: SPIFFE identity module exists; real SPIRE agent integration is stubbed
- **Performance targets**: Latency overhead (<5ms) and throughput (10k reg/sec) are design targets, not yet benchmarked

### Documentation

- `docs/rfcs/` — Directory exists, no RFCs written yet
- `docs/architecture/` — Directory exists, no architecture docs yet (see `IMPLEMENTATION-NOTES.md` for current notes)

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
