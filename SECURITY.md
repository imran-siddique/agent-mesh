# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow our responsible disclosure process.

### DO NOT

- ❌ Open a public GitHub issue for security vulnerabilities
- ❌ Disclose the vulnerability publicly before it's fixed
- ❌ Exploit the vulnerability beyond what's necessary to demonstrate it

### DO

- ✅ Report privately using the process below
- ✅ Provide sufficient detail to reproduce the issue
- ✅ Allow reasonable time for us to respond and fix

## Vulnerability Disclosure Policy (VDP)

### Scope

This policy applies to:
- AgentMesh core libraries (`agentmesh-platform`)
- AgentMesh MCP Server (`agentos-mcp-server`)
- AgentMesh API (`agentmesh-api`)
- AgentMesh Benchmark API
- Official documentation and examples

### Out of Scope

- Third-party dependencies (report to upstream)
- Social engineering attacks
- Denial of service attacks
- Issues in forks or unofficial distributions

### How to Report

**Email:** security@agentmesh.dev (or imran.siddique@microsoft.com)

**GitHub Security Advisories:** [Report a vulnerability](https://github.com/imran-siddique/agent-mesh/security/advisories/new)

### What to Include

1. **Description:** Clear explanation of the vulnerability
2. **Impact:** What an attacker could achieve
3. **Steps to Reproduce:** Detailed reproduction steps
4. **Affected Versions:** Which versions are impacted
5. **Suggested Fix:** (Optional) If you have a proposed solution
6. **Your Contact:** Email for follow-up questions

### Example Report

```
Subject: [SECURITY] Policy bypass via Unicode normalization

Description:
The policy engine's string matching can be bypassed using Unicode 
homoglyphs. An attacker can execute "ᵣᵤₙ_ₛₕₑₗₗ" which visually 
resembles "run_shell" but bypasses the blocklist.

Impact:
Attackers can execute blocked tools by using Unicode variants.

Steps to Reproduce:
1. Create policy blocking "run_shell" tool
2. Request tool "ᵣᵤₙ_ₛₕₑₗₗ" (Unicode subscript letters)
3. Policy check passes, tool executes

Affected Versions: 1.0.0 - 1.2.3

Suggested Fix:
Apply Unicode normalization (NFKC) before policy matching.
```

## Response Timeline

| Phase | Target Time |
|-------|-------------|
| Initial acknowledgment | 24 hours |
| Severity assessment | 72 hours |
| Fix development | 7-30 days (severity dependent) |
| Public disclosure | After fix is released |

### Severity Levels

| Level | Description | Target Fix Time |
|-------|-------------|-----------------|
| **Critical** | Remote code execution, auth bypass | 7 days |
| **High** | Policy bypass, data exposure | 14 days |
| **Medium** | Limited impact vulnerabilities | 30 days |
| **Low** | Minor issues, hardening | 90 days |

## Coordinated Disclosure

We follow coordinated disclosure practices:

1. **Private Report:** You report to us privately
2. **Acknowledgment:** We confirm receipt within 24 hours
3. **Investigation:** We assess severity and develop fix
4. **Notification:** We notify you when fix is ready
5. **Release:** We release the fix
6. **Disclosure:** We publish a security advisory (crediting you)
7. **Embargo Lift:** You may publish your findings

### Embargo Period

- Default embargo: 90 days from report
- May be extended for complex issues
- May be shortened if actively exploited

## Security Advisories

Published advisories are available at:
- [GitHub Security Advisories](https://github.com/imran-siddique/agent-mesh/security/advisories)

## Bug Bounty

We currently do not operate a paid bug bounty program. However, we recognize security researchers in:

- Security advisory credits
- Hall of Fame in CONTRIBUTORS.md
- Social media acknowledgment (with permission)

## Security Best Practices

When using AgentMesh:

### Policy Configuration
- Use allowlists over blocklists when possible
- Enable strict mode in production
- Regularly audit policy files

### Deployment
- Run with minimal privileges
- Use network isolation where possible
- Enable audit logging
- Rotate API keys regularly

### Monitoring
- Monitor audit logs for anomalies
- Set up alerts for policy violations
- Use `verify_integrity()` to detect log tampering

## Security Architecture

### Identity & Credential Lifecycle

AgentMesh separates **identity** (long-lived) from **credentials** (ephemeral):

| Layer | TTL | Rotation | Status |
|-------|-----|----------|--------|
| **Agent Identity** (`AgentIdentity`) | Optional `expires_at` field | Manual revocation/reactivation | ✅ Implemented |
| **Ephemeral Credentials** (`Credential`) | 15 minutes (configurable) | Automatic via `rotate_if_needed()` | ✅ Implemented |
| **SVID Certificates** (`SVID`) | 15 minutes (configurable) | Via CA `rotate_credentials()` | ✅ Implemented |
| **Integration Identity** (`CMVKIdentity`) | Optional `ttl_seconds` param | Manual (identity-layer only) | ✅ Implemented |

Credential rotation is zero-downtime — old credentials are marked `"rotated"` and remain valid during a brief overlap period. Revocation propagates in ≤5 seconds.

### On-Behalf-Of (OBO) User Context

When agents act on behalf of end users, `UserContext` propagates through the trust layer:

- **Core**: `UserContext` model in `agentmesh.identity.delegation` with `user_id`, `user_email`, `roles`, `permissions`, and TTL
- **Handshake**: `HandshakeResponse` and `HandshakeResult` carry `user_context` so downstream agents know which user triggered the request
- **Integration**: `TrustedAgentCard` includes `user_context`; `ToolInvocationRecord` logs it for audit
- **Future Roadmap**: Per-user data access policies (e.g., "Agent B trusts Agent A, but User X cannot access file Y")

### Service Discovery

Trusted agents find each other through a layered discovery model:

| Layer | Component | Description | Status |
|-------|-----------|-------------|--------|
| **Core Registry** | `AgentRegistry` | Central "Yellow Pages" with DIDs, capabilities, trust scores | ✅ Implemented |
| **Card Registry** | `CardRegistry` | Signed agent cards with TTL-based verification caching | ✅ Implemented |
| **SPIFFE Registry** | `SPIFFERegistry` | Maps agent DIDs to SPIFFE workload identities | ✅ Implemented |
| **Integration Discovery** | `AgentDirectory` | Framework-level peer lookup by DID or capability | ✅ Implemented |
| **Network Discovery** | DID resolution to endpoints | Resolve DIDs to HTTP endpoints for cross-cloud handshakes | 🚧 Future Roadmap |

The integration layer (`AgentDirectory`) provides local discovery for framework users. Production deployments pair this with the core `AgentRegistry` service for centralized, network-wide discovery.

## Security Features

AgentMesh includes several security features:

| Feature | Description | Status |
|---------|-------------|--------|
| **Cryptographic Identity** | Ed25519/X.509 agent credentials | ✅ Stable |
| **Capability Scoping** | Fine-grained permission control | ✅ Stable |
| **Policy Engine** | Tool-level access control | ✅ Stable |
| **Merkle Audit** | Immutable Merkle-chained logs | ✅ Stable |
| **Tamper Detection** | Hash chain verification | ✅ Stable |
| **Shadow Mode** | Test policies before enforcement | ✅ Stable |
| **Zero-Trust** | Verify every interaction | ✅ Stable |
| **Rate Limiting** | Prevent resource exhaustion | 🚧 Planned |
| **mTLS** | Mutual TLS for MCP | 🚧 Planned |

## Compliance

AgentMesh supports compliance with:

| Standard | Coverage |
|----------|----------|
| **SOC 2 Type II** | Audit logging, access controls |
| **HIPAA** | PHI protection policies |
| **GDPR** | Data minimization, consent tracking |
| **PCI DSS** | Cardholder data policies |
| **EU AI Act** | Human oversight, transparency |

*Note: AgentMesh is a tool to help achieve compliance, not a compliance certification.*

## OpenSSF Best Practices

We are committed to the [OpenSSF Best Practices](https://bestpractices.coreinfrastructure.org/):

- ✅ HTTPS for all project sites
- ✅ Version control (Git)
- ✅ Automated testing (CI/CD)
- ✅ Static analysis (linting)
- ✅ Documented security policy
- ✅ Vulnerability reporting process

## Threat Model

AgentMesh's security model assumes a **zero-trust mesh** where every agent interaction is authenticated, authorized, and audited. The table below summarizes what IS and ISN'T protected.

### What IS Protected

| Threat | Mitigation | Layer |
|--------|-----------|-------|
| **Identity spoofing** | Ed25519 cryptographic identity; every message is signed and verified | Identity |
| **Capability escalation** | Delegation chains enforce capability narrowing — delegatees cannot gain capabilities the delegator does not possess | Identity |
| **Unauthorized tool access** | Policy engine evaluates every tool invocation against YAML/Rego rules (< 5 ms) | Governance |
| **Audit tampering** | Merkle-chained audit logs with hash verification via `verify_integrity()` | Governance |
| **Stale credentials** | 15-minute credential TTL with automatic zero-downtime rotation | Identity |
| **Trust decay after compromise** | Automated trust score decay (−2 pts/hr) and anomaly detection (5 classes) | Reward |
| **Cross-protocol trust** | TrustBridge verifies peers across A2A, MCP, IATP, and ACP with score threshold (default ≥ 700) | Trust |
| **Cascading delegation revocation** | Revoking any link invalidates all downstream links; propagation ≤ 5 seconds | Identity |

### What ISN'T Protected

| Threat | Status | Notes |
|--------|--------|-------|
| **Prompt injection in agent inputs** | ⚠️ Not mitigated | AgentMesh operates at the transport/trust layer, not the inference layer. Prompt content is opaque to the mesh. See [Known Limitations](#known-limitations). |
| **Credential exfiltration within TTL window** | ⚠️ Partially mitigated | Credentials are short-lived (15 min) but a compromised agent can use them until expiry or revocation. |
| **Side-channel attacks on host** | ❌ Out of scope | AgentMesh does not provide OS-level sandboxing or memory isolation. |
| **Compromised root sponsor key** | ⚠️ Partially mitigated | Mitigated by credential TTL and SVID rotation, but all delegation chains are compromised until key rotation. |
| **Malicious agent spawning child processes** | ⚠️ Not mitigated | Shadow mode agents and compromised agents can spawn OS processes that bypass the AgentMesh proxy entirely. |
| **Cyclic delegation graphs** | ⚠️ Not mitigated | The delegation model assumes tree-structured chains. See [Known Limitations](#known-limitations). |

---

## Known Limitations

This section documents honest gaps in the current security model. These are areas where AgentMesh either provides incomplete protection or where fundamental unsolved problems exist.

### 1. Prompt Injection Sanitization

**What we do:** AgentMesh enforces tool-level access control via the policy engine. If a policy says Agent X cannot call `run_shell`, the engine blocks the invocation regardless of how the request was constructed.

**What we don't do:** AgentMesh does not inspect, sanitize, or validate the *content* of prompts or tool arguments. Prompt injection is an inference-layer concern — a compromised or manipulated prompt can cause an agent to make legitimate-looking tool calls that pass policy checks.

**Unsolved problems:**
- There is no reliable, general-purpose prompt injection detector today. Heuristic filters produce false positives and false negatives.
- Even if we added content inspection, adversarial inputs can be designed to evade any static filter.
- Defense in depth means combining AgentMesh's policy enforcement with framework-level input validation and LLM-level guardrails.

### 2. Credential TTL Does Not Prevent Exfiltration Within the Window

Credentials have a 15-minute TTL (configurable). If an agent is compromised, the attacker has up to 15 minutes of valid credential use before automatic rotation invalidates them. Explicit revocation (propagation ≤ 5 s) is the intended mitigation, but this requires *detecting* the compromise first.

**Implications:**
- Anomaly detection can flag rapid-fire or unusual actions, but detection latency means some unauthorized actions may succeed.
- Operators should tune credential TTL based on risk tolerance (shorter TTL = more rotation overhead, less exposure window).

### 3. Shadow Agents Can Bypass the Proxy

Shadow mode (`governance/shadow.py`) runs policy evaluation in dry-run mode. However, any agent — shadow or otherwise — that spawns an OS-level child process (e.g., `subprocess.Popen`, `os.exec`) creates a process that communicates directly on the network, bypassing the AgentMesh sidecar proxy entirely.

**Implications:**
- Network-level isolation (Kubernetes NetworkPolicy, service mesh mTLS) is required to ensure all traffic routes through the proxy.
- AgentMesh alone cannot prevent process-level escape. It must be paired with container sandboxing and network policies.

### 4. Delegation Model Assumes Trees, Not Cycles

The delegation chain model (see [ADR-003](docs/adr/003-delegation-chain-design.md)) is designed as a **directed tree** rooted at a human sponsor. The verification algorithm walks the chain linearly from leaf to root.

**Current gap:** There is no cycle detection in delegation chain construction. If Agent A delegates to Agent B and Agent B delegates back to Agent A (via a separate chain), the system does not detect or prevent this. Each individual chain is valid, but the combined graph contains a cycle.

**Risks:**
- Circular delegation can create confused-deputy scenarios where capability provenance is ambiguous.
- Revocation of a link in a cycle may not fully invalidate the expected set of agents.

**Planned mitigation:** Add a graph-level cycle detection check at delegation link creation time. Track the global delegation graph (not just individual chains) and reject links that would create cycles. See [ADR-003](docs/adr/003-delegation-chain-design.md) for the delegation chain design.

---

## Contact

- **Security Reports:** security@agentmesh.dev / imran.siddique@microsoft.com
- **General Questions:** hello@agentmesh.dev
- **GitHub:** [@imran-siddique](https://github.com/imran-siddique)

---

*This security policy follows the [disclose.io](https://disclose.io/) safe harbor guidelines.*

*Last updated: February 2026*
