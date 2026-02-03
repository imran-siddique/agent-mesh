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

## Contact

- **Security Reports:** security@agentmesh.dev / imran.siddique@microsoft.com
- **General Questions:** hello@agentmesh.dev
- **GitHub:** [@imran-siddique](https://github.com/imran-siddique)

---

*This security policy follows the [disclose.io](https://disclose.io/) safe harbor guidelines.*

*Last updated: February 2026*
