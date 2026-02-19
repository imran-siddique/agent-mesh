# NIST AI Risk Management Framework — AgentMesh Alignment

How AgentMesh aligns with the [NIST AI Risk Management Framework (AI RMF 1.0)](https://www.nist.gov/artificial-intelligence/risk-management-framework).

> **Disclaimer:** AgentMesh is a tool that helps achieve compliance — it is not a compliance certification.

---

## Table of Contents

- [Framework Overview](#framework-overview)
- [GOVERN Function](#govern-function)
- [MAP Function](#map-function)
- [MEASURE Function](#measure-function)
- [MANAGE Function](#manage-function)
- [Gaps and Roadmap](#gaps-and-roadmap)

---

## Framework Overview

The NIST AI RMF defines four core functions: **Govern**, **Map**, **Measure**, and **Manage**. Each function contains categories and subcategories. This document maps AgentMesh capabilities to relevant subcategories.

---

## GOVERN Function

Establishes the organizational context and culture for AI risk management.

| NIST Subcategory | AgentMesh Feature | Status |
|-----------------|-------------------|--------|
| **GV-1.1** Legal and regulatory requirements | Compliance module maps actions to EU AI Act, SOC 2, HIPAA, GDPR, PCI DSS | ✅ Supported |
| **GV-1.2** Trustworthy AI characteristics | 5-dimension trust scoring: competence, integrity, availability, predictability, transparency | ✅ Supported |
| **GV-2.1** Roles and responsibilities | Delegation chains with human sponsor root; `UserContext` tracks authorization origin | ✅ Supported |
| **GV-3.1** Decision-making processes | `require_approval` policy verdict enables human-in-the-loop | ✅ Supported |
| **GV-4.1** Organizational practices | Policy engine enforces governance rules across all agents in the mesh | ✅ Supported |
| **GV-6.1** Feedback mechanisms | Trust decay and anomaly detection feed back into trust scores automatically | ✅ Supported |

---

## MAP Function

Identifies and contextualizes AI risks.

| NIST Subcategory | AgentMesh Feature | Status |
|-----------------|-------------------|--------|
| **MP-2.1** Intended purposes are documented | AI Card metadata includes capabilities, description, and supported protocols | ✅ Supported |
| **MP-2.2** Potential misuse is documented | Tool blocklists and capability scoping define prohibited and allowed uses | ✅ Supported |
| **MP-3.1** Benefits vs. costs are assessed | Trust scoring's resource efficiency dimension (15% weight) tracks compute/token costs | ✅ Supported |
| **MP-4.1** Risks identified across lifecycle | Anomaly detection (5 classes) identifies behavioral risks at runtime | ✅ Supported |
| **MP-5.1** Impacts to individuals | `UserContext` propagation enables per-user impact tracking | 🚧 Partial |

---

## MEASURE Function

Assesses, analyzes, and tracks AI risks.

| NIST Subcategory | AgentMesh Feature | Status |
|-----------------|-------------------|--------|
| **MS-1.1** Risk metrics identified | Trust score (0–1000), anomaly severity (LOW/MEDIUM/HIGH), policy violation counts | ✅ Supported |
| **MS-2.1** Systems evaluated for trustworthiness | Trust handshake protocol evaluates every agent interaction with cryptographic verification | ✅ Supported |
| **MS-2.2** Systems evaluated for bias | Not directly addressed — AgentMesh operates at the transport/trust layer | ❌ Out of scope |
| **MS-2.5** Systems tested before deployment | Shadow mode enables dry-run policy testing with < 2% divergence measurement | ✅ Supported |
| **MS-2.6** Evaluation results documented | Merkle audit chain provides tamper-evident evaluation records | ✅ Supported |
| **MS-3.1** Risks tracked over time | Trust decay model (−2 pts/hr), anomaly detection, and Prometheus metrics | ✅ Supported |
| **MS-4.1** Measurement approaches documented | ARCHITECTURE.md, trust-scoring.md, and compliance docs | ✅ Supported |

---

## MANAGE Function

Prioritizes and acts on AI risks.

| NIST Subcategory | AgentMesh Feature | Status |
|-----------------|-------------------|--------|
| **MG-1.1** Risks prioritized | Trust score tiers map to response actions: revoke (< 300), warn (< 500), allow (≥ 500) | ✅ Supported |
| **MG-2.1** Risk responses planned | Policy engine supports `allow`, `deny`, `warn`, `require_approval`, and `log` verdicts | ✅ Supported |
| **MG-2.2** Contingency processes | Credential revocation (≤ 5 s), trust score override, and cascading delegation revocation | ✅ Supported |
| **MG-3.1** Pre-deployment risk mitigation | Shadow mode tests new policies in parallel before enforcement | ✅ Supported |
| **MG-3.2** Post-deployment monitoring | Anomaly detection, trust decay, audit logging, and CloudEvents export for SIEM integration | ✅ Supported |
| **MG-4.1** Incidents documented | Merkle audit logs + CloudEvents export to Azure Event Grid / AWS EventBridge / Splunk | ✅ Supported |

---

## Gaps and Roadmap

| NIST Area | Gap | Planned Mitigation |
|-----------|-----|-------------------|
| **MS-2.2** Bias evaluation | AgentMesh does not evaluate inference-level bias | Out of scope — recommend pairing with LLM evaluation tools |
| **MP-5.1** Individual impact assessment | `UserContext` exists but per-user impact tracking is not yet automated | Planned: per-user policy rules and impact dashboards |
| **GV-5.1** Third-party risk management | TrustBridge verifies external agents but no formal third-party risk assessment | Planned: vendor risk scoring integration |
| **MG-2.3** Decommissioning processes | No automated agent decommissioning workflow | Planned: agent lifecycle management module |

---

*See also: [EU AI Act](eu-ai-act.md) · [ISO 42001](iso-42001.md) · [SOC2 Mapping](soc2-mapping.md) · [SECURITY.md](../../SECURITY.md)*
