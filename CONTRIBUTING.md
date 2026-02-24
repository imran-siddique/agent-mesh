# Contributing to AgentMesh

Thank you for your interest in contributing! AgentMesh is the secure nervous system for cloud-native agent ecosystems.

## 🚀 Quick Start (5 minutes)

```bash
# Clone and install
git clone https://github.com/imran-siddique/agent-mesh.git
cd agent-mesh
pip install -e ".[dev]"

# Run tests to make sure everything works
pytest tests/ -v

# Run the CLI
agentmesh --help
```

## 🏷️ Good First Issues

New to the project? Start here:

| Label | Description |
|-------|-------------|
| [`good-first-issue`](https://github.com/imran-siddique/agent-mesh/labels/good-first-issue) | Small, well-defined tasks |
| [`documentation`](https://github.com/imran-siddique/agent-mesh/labels/documentation) | Improve docs and examples |
| [`needs-tests`](https://github.com/imran-siddique/agent-mesh/labels/needs-tests) | Add test coverage |

## 🎁 Integration Bounties

We're actively looking for integration contributions:

| Integration | Description | Status |
|-------------|-------------|--------|
| **A2A Protocol** | Google's Agent-to-Agent | 🟢 Complete |
| **MCP Protocol** | Model Context Protocol | 🟢 Complete |
| **IATP Protocol** | Inter-Agent Trust Protocol | 🟢 Via agent-os |
| **OpenID Connect** | OIDC identity integration | 🟡 In Progress |
| **SPIFFE/SPIRE** | Workload identity | 🟡 In Progress |
| **Kubernetes** | K8s service mesh integration | 🔴 Open |

## 📁 Project Structure

```
agent-mesh/
├── src/agentmesh/          # Main package
│   ├── identity/           # L1: Agent identity & credentials
│   ├── trust/              # L2: Trust protocols & bridges
│   ├── governance/         # L3: Policies & compliance
│   ├── reward/             # L4: Reputation & learning
│   ├── services/           # Backend services
│   └── cli/                # Command-line interface
├── schemas/                # JSON schemas for validation
├── proto/                  # Protocol buffer definitions
├── examples/               # Working demos
├── docs/                   # Documentation
└── tests/                  # Test suite
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific layer
pytest tests/test_identity.py -v

# Run with coverage
pytest tests/ --cov=src/agentmesh --cov-report=html

# Run examples
python examples/mcp_secure_relay.py
python examples/a2a_customer_service.py
```

## 📝 Code Style

```bash
# Format (we use ruff/black)
ruff format .

# Lint
ruff check .

# Type check
mypy src/
```

## 🔀 Pull Request Process

1. **Fork** the repository
2. **Create branch**: `git checkout -b feature/my-feature`
3. **Make changes** (follow the design philosophy below)
4. **Test**: `pytest tests/ -v`
5. **Commit**: `git commit -m "feat: add my feature"`
6. **Push**: `git push origin feature/my-feature`
7. **Open PR** with description of changes

### Commit Message Convention

```
feat: add new feature
fix: fix a bug
docs: documentation only
test: add tests
refactor: code change that neither fixes a bug nor adds a feature
security: security-related changes
```

## 🎯 Design Philosophy

**"Zero-Trust by Default"** - Every agent interaction is verified, every action is audited.

### We ✅ Want

- Protocol-agnostic identity (SPIFFE, DID, X.509)
- Cryptographic trust verification
- Immutable audit trails (hash chain trees)
- Compliance-first design (SOC2, HIPAA, EU AI Act)
- Minimal attack surface
- Agent-OS integration for IATP

### We ❌ Avoid

- Implicit trust between agents
- Unaudited agent actions
- Protocol-specific lock-in
- Centralized identity authorities
- Feature bloat

## 📚 Layer Guidelines

| Layer | May Depend On | Focus |
|-------|---------------|-------|
| **L1: Identity** | Nothing | Agent IDs, credentials |
| **L2: Trust** | L1 | Protocol bridges, verification |
| **L3: Governance** | L1, L2 | Policies, compliance, audit |
| **L4: Reward** | L1, L2, L3 | Reputation, learning |

## 🔗 Relationship with Agent-OS

AgentMesh is designed to work seamlessly with [Agent-OS](https://github.com/imran-siddique/agent-os):

```python
# Install with Agent-OS integration
pip install agentmesh-platform[agent-os]

# This enables IATP protocol support via Agent-OS nexus module
```

**Division of Responsibility:**
- **Agent-OS**: Kernel architecture, verification (CMVK), trust protocol (IATP)
- **AgentMesh**: Identity management, multi-protocol bridges, governance, audit

## 💬 Getting Help

- **Questions?** Open a [Discussion](https://github.com/imran-siddique/agent-mesh/discussions)
- **Found a bug?** Open an [Issue](https://github.com/imran-siddique/agent-mesh/issues)
- **Security issue?** See [SECURITY.md](SECURITY.md)

## 📜 License

By contributing, you agree that your contributions will be licensed under the Apache-2.0 License.
