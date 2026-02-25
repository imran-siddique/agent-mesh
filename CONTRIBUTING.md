# Contributing to AgentMesh

Thank you for your interest in contributing! AgentMesh is the secure nervous system for cloud-native agent ecosystems. This guide will help you get set up and make your first contribution.

---

## Table of Contents

- [Getting Started](#-getting-started)
- [Development Setup](#-development-setup)
- [Code Style](#-code-style)
- [Making Changes](#-making-changes)
- [Testing](#-testing)
- [Issue Guidelines](#-issue-guidelines)
- [Architecture Overview](#-architecture-overview)
- [Design Philosophy](#-design-philosophy)
- [Integration Bounties](#-integration-bounties)
- [Getting Help](#-getting-help)

---

## 🚀 Getting Started

### Fork and Clone

```bash
# 1. Fork the repository on GitHub, then clone your fork
git clone https://github.com/<your-username>/agent-mesh.git
cd agent-mesh

# 2. Add upstream remote
git remote add upstream https://github.com/imran-siddique/agent-mesh.git

# 3. Install in development mode
pip install -e ".[dev]"

# 4. Run tests to verify your setup
python -m pytest

# 5. Install pre-commit hooks
pip install pre-commit
pre-commit install

# 6. Verify the CLI works
agentmesh --help
```

### Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to enforce code quality on every commit. The hooks include:

- **Trailing whitespace** and **end-of-file** fixes
- **YAML validation** and **merge conflict** detection
- **Private key detection** (security)
- **Ruff** linting and formatting
- **mypy** type checking (excludes tests)
- **pytest** check on push

Hooks are configured in `.pre-commit-config.yaml`. After installing with `pre-commit install`, they run automatically on `git commit`.

---

## 🛠️ Development Setup

### Python Version

AgentMesh requires **Python 3.11 or higher**. We recommend using [pyenv](https://github.com/pyenv/pyenv) to manage Python versions:

```bash
pyenv install 3.12
pyenv local 3.12
```

### Virtual Environment

Always use a virtual environment for development:

```bash
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate

# Install all dev dependencies
pip install -e ".[dev]"
```

### Optional Extras

Depending on what you're working on, install additional extras:

```bash
pip install -e ".[dev,server]"        # FastAPI server components
pip install -e ".[dev,storage]"       # Redis/SQLAlchemy storage backends
pip install -e ".[dev,observability]" # OpenTelemetry & Prometheus
pip install -e ".[dev,grpc]"          # gRPC transport
pip install -e ".[dev,agent-os]"      # Agent-OS/IATP integration
pip install -e ".[dev,all]"           # Everything
```

### IDE Recommendations

- **VS Code** with the [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python), [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff), and [mypy](https://marketplace.visualstudio.com/items?itemName=ms-python.mypy-type-checker) extensions
- **PyCharm** Professional with built-in type checking enabled
- Enable format-on-save with Ruff for consistent formatting

---

## 📝 Code Style

### Formatting and Linting

We use **Ruff** for linting and formatting, and **mypy** for type checking:

```bash
# Format code
ruff format .

# Lint (with auto-fix)
ruff check . --fix

# Type check
mypy src/
```

### Rules

| Rule | Details |
|------|---------|
| **Line length** | 100 characters maximum |
| **Target version** | Python 3.11 |
| **Type hints** | Required on all function signatures |
| **Docstrings** | Required for all public modules, classes, and functions |
| **Docstring style** | Google style |
| **Import order** | Enforced by Ruff (`I` rule) — stdlib → third-party → local |

### Type Hints

All function signatures must include type hints. Use `from __future__ import annotations` for modern syntax:

```python
from __future__ import annotations

def verify_agent(
    agent_id: str,
    credentials: AgentCredentials,
    *,
    strict: bool = True,
) -> VerificationResult:
    """Verify an agent's identity and credentials.

    Args:
        agent_id: The unique identifier of the agent.
        credentials: The agent's cryptographic credentials.
        strict: If True, enforce strict verification rules.

    Returns:
        The verification result containing trust score and status.

    Raises:
        VerificationError: If the agent cannot be verified.
    """
    ...
```

### Docstrings (Google Style)

```python
class TrustBridge:
    """Bridge for cross-protocol trust verification.

    Manages trust relationships between agents using different
    identity protocols (SPIFFE, DID, X.509).

    Attributes:
        protocol: The primary protocol for this bridge.
        trust_anchors: Set of trusted root certificates.

    Example:
        >>> bridge = TrustBridge(protocol="spiffe")
        >>> result = bridge.verify(agent_id="spiffe://example/agent-1")
    """
```

---

## 🔀 Making Changes

### Branch Naming

Create a branch from `main` using one of these prefixes:

| Prefix | Use For |
|--------|---------|
| `feat/` | New features (e.g., `feat/oidc-identity-provider`) |
| `fix/` | Bug fixes (e.g., `fix/trust-score-overflow`) |
| `docs/` | Documentation changes (e.g., `docs/api-reference`) |
| `test/` | Test additions/improvements (e.g., `test/governance-edge-cases`) |
| `refactor/` | Code refactoring (e.g., `refactor/identity-module`) |
| `security/` | Security changes (e.g., `security/key-rotation-fix`) |

```bash
# Sync with upstream before branching
git fetch upstream
git checkout -b feat/my-feature upstream/main
```

### Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:** `feat`, `fix`, `docs`, `test`, `refactor`, `security`, `chore`, `ci`

**Scopes** (optional): `identity`, `trust`, `governance`, `reward`, `cli`, `transport`, `storage`

**Examples:**

```
feat(trust): add SPIFFE workload identity verification
fix(identity): handle expired certificates in rotation
docs: update architecture diagrams for L2 trust
test(governance): add OPA policy evaluation edge cases
security(identity): rotate default key algorithm to Ed25519
```

### Pull Request Process

1. **Fork** the repository and create your branch
2. **Make changes** following the code style and design philosophy
3. **Write/update tests** — all new features need test coverage
4. **Run the full check suite:**
   ```bash
   ruff format .
   ruff check .
   mypy src/
   python -m pytest
   ```
5. **Push** your branch and open a Pull Request
6. **Fill out the PR description** with:
   - What changed and why
   - How to test the changes
   - Related issue numbers (e.g., `Closes #167`)
7. **Address review feedback** — maintainers may request changes
8. **Merge** — a maintainer will merge once approved

### Review Criteria

PRs are evaluated on:
- Correctness and security implications
- Test coverage for new/changed behavior
- Adherence to the layer dependency guidelines
- Type safety (mypy must pass with `--strict`)
- Documentation for public APIs

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run a specific test file
python -m pytest tests/test_identity.py -v

# Run a specific test
python -m pytest tests/test_trust.py::test_trust_score_calculation -v

# Run tests by marker
python -m pytest -m "not slow"          # Skip long-running tests
python -m pytest -m fuzz                # Fuzzing tests only
python -m pytest -m benchmark           # Benchmark tests only

# Run with coverage report
python -m pytest --cov=src/agentmesh --cov-report=html --cov-report=term-missing

# Run examples as smoke tests
python examples/mcp_secure_relay.py
python examples/a2a_customer_service.py
```

### Writing Tests

- **Test file location:** Place tests in `tests/` at the repo root, mirroring the module structure
- **Naming convention:** `test_<module>.py` for files, `test_<behavior>` for functions
- **Async tests:** Use `pytest-asyncio` — tests are auto-detected (`asyncio_mode = "auto"`)
- **Property-based tests:** Use [Hypothesis](https://hypothesis.readthedocs.io/) for fuzzing (mark with `@pytest.mark.fuzz`)

```python
import pytest
from agentmesh.identity import AgentIdentity

class TestAgentIdentity:
    """Tests for agent identity creation and verification."""

    def test_create_identity_with_valid_params(self) -> None:
        identity = AgentIdentity(name="test-agent", protocol="spiffe")
        assert identity.name == "test-agent"
        assert identity.agent_id is not None

    def test_create_identity_rejects_empty_name(self) -> None:
        with pytest.raises(ValueError, match="name"):
            AgentIdentity(name="", protocol="spiffe")

    @pytest.mark.asyncio
    async def test_async_credential_fetch(self) -> None:
        identity = AgentIdentity(name="async-agent", protocol="did")
        creds = await identity.fetch_credentials()
        assert creds.is_valid()
```

### Coverage Requirements

- **Minimum coverage:** 80% for new code
- **Critical paths** (identity, trust, governance): aim for 90%+
- Run `python -m pytest --cov=src/agentmesh --cov-report=term-missing` to identify uncovered lines

### Test Markers

| Marker | Description |
|--------|-------------|
| `@pytest.mark.fuzz` | Fuzzing tests with malformed inputs |
| `@pytest.mark.benchmark` | Crypto operation benchmarks |
| `@pytest.mark.slow` | Long-running load tests (skip with `-m "not slow"`) |

---

## 📋 Issue Guidelines

### Bug Reports

When filing a bug, include:

1. **AgentMesh version** (`agentmesh --version` or `pip show agentmesh-platform`)
2. **Python version** (`python --version`)
3. **Operating system**
4. **Steps to reproduce** — minimal code snippet or CLI commands
5. **Expected behavior** vs. **actual behavior**
6. **Full error traceback** if applicable

### Feature Requests

For feature requests, describe:

1. **Use case** — what problem does this solve?
2. **Proposed solution** — how should it work?
3. **Alternatives considered** — what else did you look at?
4. **Which layer** does this belong to (L1–L4)?

### Good First Issues

New to the project? Look for issues labeled:

| Label | Description |
|-------|-------------|
| [`good-first-issue`](https://github.com/imran-siddique/agent-mesh/labels/good-first-issue) | Small, well-defined tasks |
| [`documentation`](https://github.com/imran-siddique/agent-mesh/labels/documentation) | Improve docs and examples |
| [`needs-tests`](https://github.com/imran-siddique/agent-mesh/labels/needs-tests) | Add test coverage |

---

## 🏗️ Architecture Overview

### Project Structure

```
agent-mesh/
├── src/agentmesh/          # Main package
│   ├── identity/           # L1: Agent identity & credentials
│   ├── trust/              # L2: Trust protocols & bridges
│   ├── governance/         # L3: Policies, compliance & audit
│   ├── reward/             # L4: Reputation & learning
│   ├── cli/                # Command-line interface (Click)
│   ├── core/               # Shared core utilities
│   ├── events/             # Event bus and messaging
│   ├── integrations/       # Third-party integrations (LangChain, Django)
│   ├── marketplace/        # Agent marketplace
│   ├── observability/      # OpenTelemetry & Prometheus metrics
│   ├── sdk/                # Public SDK for consumers
│   ├── services/           # Backend service layer (FastAPI)
│   ├── storage/            # Storage backends (Redis, SQL)
│   ├── transport/          # gRPC & WebSocket transport
│   ├── dashboard/          # Dashboard rendering
│   ├── constants.py        # Shared constants
│   ├── exceptions.py       # Exception hierarchy
│   └── providers.py        # Dependency injection providers
├── schemas/                # JSON schemas for validation
├── proto/                  # Protocol buffer definitions
├── services/               # Microservice definitions
├── integrations/           # Integration packages
├── sdks/                   # SDK packages
├── examples/               # Working demos and tutorials
├── docs/                   # Documentation
├── tests/                  # Test suite (50+ test modules)
├── charts/                 # Helm charts for Kubernetes
├── dashboards/             # Grafana dashboards
├── deployments/            # Deployment configurations
└── notebooks/              # Jupyter notebooks
```

### Key Modules

| Module | Purpose | Key Abstractions |
|--------|---------|------------------|
| **identity** | Agent IDs, credentials, key management | `AgentIdentity`, `Credential`, `KeyStore` |
| **trust** | Cross-protocol trust verification | `TrustBridge`, `TrustScore`, `HandshakeProtocol` |
| **governance** | Policy enforcement, audit trails | `Policy`, `AuditLog`, `ComplianceChecker` |
| **reward** | Reputation scoring, incentive learning | `RewardEngine`, `ReputationScore` |
| **transport** | Network communication (gRPC, WS) | `Transport`, `Channel`, `Message` |
| **storage** | Persistence (Redis, SQL) | `StorageBackend`, `AuditStore` |
| **events** | Internal event bus | `EventBus`, `Event` |
| **observability** | Metrics and tracing | `Tracer`, `MetricsExporter` |

### Layer Dependency Rules

Layers follow strict dependency rules — **never depend upward**:

| Layer | May Depend On | Focus |
|-------|---------------|-------|
| **L1: Identity** | Nothing | Agent IDs, credentials |
| **L2: Trust** | L1 | Protocol bridges, verification |
| **L3: Governance** | L1, L2 | Policies, compliance, audit |
| **L4: Reward** | L1, L2, L3 | Reputation, learning |

---

## 🎯 Design Philosophy

**"Zero-Trust by Default"** — Every agent interaction is verified, every action is audited.

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

---

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

---

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

---

## 💬 Getting Help

- **Questions?** Open a [Discussion](https://github.com/imran-siddique/agent-mesh/discussions)
- **Found a bug?** Open an [Issue](https://github.com/imran-siddique/agent-mesh/issues)
- **Security issue?** See [SECURITY.md](SECURITY.md)

---

## 📜 License

By contributing, you agree that your contributions will be licensed under the [Apache-2.0 License](LICENSE).
