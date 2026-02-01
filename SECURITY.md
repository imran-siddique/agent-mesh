# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security seriously at AgentMesh. If you discover a security vulnerability, please follow these steps:

### 1. Do NOT Open a Public Issue

Security vulnerabilities should not be reported through public GitHub issues.

### 2. Report Privately

Email security concerns to: **imran.siddique@microsoft.com**

Include in your report:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### 3. What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Resolution Timeline**: Based on severity
  - Critical: 24-72 hours
  - High: 7 days
  - Medium: 30 days
  - Low: 90 days

### 4. Disclosure Policy

- We follow responsible disclosure practices
- We will credit reporters who wish to be acknowledged
- We will coordinate disclosure timing with you

## Security Best Practices

When using AgentMesh:

### Identity Management
- Always use strong cryptographic credentials
- Rotate credentials regularly
- Use short-lived tokens when possible

### Trust Configuration
- Start with deny-all policies
- Grant minimum necessary capabilities
- Regularly audit trust relationships

### Audit Logs
- Enable immutable audit logging
- Store audit logs securely
- Regularly review audit trails

### Deployment
- Use TLS for all communications
- Keep dependencies updated
- Run security scans (Bandit, pip-audit)

## Security Features

AgentMesh includes built-in security features:

| Feature | Description |
|---------|-------------|
| **Cryptographic Identity** | Ed25519/X.509 agent credentials |
| **Capability Scoping** | Fine-grained permission control |
| **Merkle Audit** | Tamper-evident audit trails |
| **Shadow Mode** | Test policies before enforcement |
| **Zero-Trust** | Verify every interaction |

## Compliance

AgentMesh supports compliance with:
- SOC 2 Type II
- HIPAA
- EU AI Act
- GDPR (data minimization)

See documentation for compliance mapping details.
