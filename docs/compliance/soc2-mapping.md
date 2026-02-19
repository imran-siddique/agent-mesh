# SOC 2 — AgentMesh Trust Services Criteria Mapping

How AgentMesh features map to [SOC 2 Type II](https://www.aicpa-cima.com/topic/audit-assurance/audit-and-assurance-greater-than-soc-2) Trust Services Criteria (TSC).

> **Disclaimer:** AgentMesh is a tool that helps achieve compliance — it is not a compliance certification. SOC 2 attestation requires an independent auditor.

---

## Table of Contents

- [Overview](#overview)
- [CC1 — Control Environment](#cc1--control-environment)
- [CC2 — Communication and Information](#cc2--communication-and-information)
- [CC3 — Risk Assessment](#cc3--risk-assessment)
- [CC5 — Control Activities](#cc5--control-activities)
- [CC6 — Logical and Physical Access Controls](#cc6--logical-and-physical-access-controls)
- [CC7 — System Operations](#cc7--system-operations)
- [CC8 — Change Management](#cc8--change-management)
- [CC9 — Risk Mitigation](#cc9--risk-mitigation)
- [Availability](#availability)
- [Confidentiality](#confidentiality)
- [Gaps and Roadmap](#gaps-and-roadmap)

---

## Overview

SOC 2 evaluates controls relevant to security, availability, processing integrity, confidentiality, and privacy. AgentMesh provides technical controls that support many of these criteria, particularly in the security and availability categories.

---

## CC1 — Control Environment

| TSC Criteria | AgentMesh Feature | Status |
|-------------|-------------------|--------|
| CC1.1 Integrity and ethical values | Governance policy engine enforces organizational rules declaratively | ✅ Supported |
| CC1.2 Board oversight | Human sponsor root in delegation chains; `require_approval` for high-risk actions | ✅ Supported |
| CC1.3 Authority and responsibility | Delegation chains define capability hierarchy; capability narrowing enforces least privilege | ✅ Supported |
| CC1.4 Competence commitment | Trust scoring's competence dimension (tracked per agent) | ✅ Supported |
| CC1.5 Accountability | Merkle audit logs trace every action to an agent identity and human sponsor | ✅ Supported |

---

## CC2 — Communication and Information

| TSC Criteria | AgentMesh Feature | Status |
|-------------|-------------------|--------|
| CC2.1 Information quality for controls | AI Card metadata provides structured agent information | ✅ Supported |
| CC2.2 Internal communication | Agent registry and AI Card discovery enable mesh-wide communication | ✅ Supported |
| CC2.3 External communication | CloudEvents export to SIEM (Splunk, Azure Event Grid, AWS EventBridge) | ✅ Supported |

---

## CC3 — Risk Assessment

| TSC Criteria | AgentMesh Feature | Status |
|-------------|-------------------|--------|
| CC3.1 Relevant objectives | Trust score thresholds define security objectives per tier | ✅ Supported |
| CC3.2 Risk identification | Anomaly detection (5 classes): rapid-fire, action drift, frequency spike, trust degradation, time-of-day | ✅ Supported |
| CC3.3 Fraud risk assessment | Behavioral monitoring detects anomalous patterns; trust decay penalizes inactive agents | ✅ Supported |
| CC3.4 Significant changes | Shadow mode evaluates policy changes in dry-run before enforcement | ✅ Supported |

---

## CC5 — Control Activities

| TSC Criteria | AgentMesh Feature | Status |
|-------------|-------------------|--------|
| CC5.1 Control activities defined | YAML/JSON + Rego policy rules with allow/deny/warn/require_approval verdicts | ✅ Supported |
| CC5.2 Technology controls | Ed25519 cryptographic identity, SPIFFE mTLS, zero-trust handshake | ✅ Supported |
| CC5.3 Policy deployment | Policy engine evaluates all tool invocations (< 5 ms); OPA integration for complex rules | ✅ Supported |

---

## CC6 — Logical and Physical Access Controls

| TSC Criteria | AgentMesh Feature | Status |
|-------------|-------------------|--------|
| CC6.1 Access controls | Capability scoping: `action:resource:qualifier` grants | ✅ Supported |
| CC6.2 Authentication | Ed25519 signatures, DID verification, SPIFFE SVID X.509 certificates | ✅ Supported |
| CC6.3 Authorization | Policy engine + delegation chains enforce least-privilege access | ✅ Supported |
| CC6.5 Credential management | 15-min credential TTL, automatic zero-downtime rotation, revocation ≤ 5 s | ✅ Supported |
| CC6.6 Access revocation | Cascading delegation revocation; trust score-based automatic access restriction | ✅ Supported |
| CC6.7 Data access restrictions | Tool-level access control via policy engine; capability narrowing | ✅ Supported |
| CC6.8 Data transmission protection | SPIFFE mTLS (planned), Ed25519 signed messages | 🚧 Partial |

---

## CC7 — System Operations

| TSC Criteria | AgentMesh Feature | Status |
|-------------|-------------------|--------|
| CC7.1 Infrastructure monitoring | Prometheus metrics (ports 9090/9091), anomaly detection, trust decay monitoring | ✅ Supported |
| CC7.2 Security event detection | Anomaly detection triggers alerts; policy violation logging | ✅ Supported |
| CC7.3 Security incident evaluation | Trust score drops, anomaly severity classification (LOW/MEDIUM/HIGH) | ✅ Supported |
| CC7.4 Incident response | Credential revocation (≤ 5 s), trust override, cascading delegation revocation | ✅ Supported |
| CC7.5 Recovery activities | Credential rotation, trust score recovery via positive signals | ✅ Supported |

---

## CC8 — Change Management

| TSC Criteria | AgentMesh Feature | Status |
|-------------|-------------------|--------|
| CC8.1 Changes to infrastructure | Shadow mode tests policy changes before enforcement (< 2% divergence) | ✅ Supported |
| CC8.1 Configuration management | Declarative policy files (YAML/JSON) under version control | ✅ Supported |

---

## CC9 — Risk Mitigation

| TSC Criteria | AgentMesh Feature | Status |
|-------------|-------------------|--------|
| CC9.1 Risk mitigation activities | Trust scoring, anomaly detection, policy enforcement, credential rotation | ✅ Supported |
| CC9.2 Vendor risk management | TrustBridge verifies external agents with configurable trust threshold (default ≥ 700) | ✅ Supported |

---

## Availability

| TSC Criteria | AgentMesh Feature | Status |
|-------------|-------------------|--------|
| A1.1 Processing capacity | Resource efficiency trust dimension (15% weight) | ✅ Supported |
| A1.2 Environmental protections | Kubernetes deployment with health checks, scaling, and monitoring | ✅ Supported |
| A1.3 Recovery procedures | Zero-downtime credential rotation; sidecar pattern for fault isolation | ✅ Supported |

---

## Confidentiality

| TSC Criteria | AgentMesh Feature | Status |
|-------------|-------------------|--------|
| C1.1 Confidential information identified | Capability scoping restricts access to specific resources | ✅ Supported |
| C1.2 Confidential information disposed | Credential TTL ensures automatic expiry; revocation propagation ≤ 5 s | ✅ Supported |

---

## Gaps and Roadmap

| SOC 2 Area | Gap | Planned Mitigation |
|-----------|-----|-------------------|
| CC6.8 Transmission encryption | mTLS not yet enforced (SPIFFE mTLS is planned) | Planned: mutual TLS for all MCP communication |
| CC6.4 Physical access | AgentMesh is software-only; physical access controls are deployment-dependent | Out of scope — document in deployment guides |
| Privacy TSC | No built-in PII detection or data classification | Planned: data classification labels in policy engine |
| Processing Integrity | No built-in output validation beyond trust scoring | Planned: output validation hooks in governance layer |

---

*See also: [EU AI Act](eu-ai-act.md) · [NIST AI RMF](nist-ai-rmf.md) · [ISO 42001](iso-42001.md) · [SECURITY.md](../../SECURITY.md)*
