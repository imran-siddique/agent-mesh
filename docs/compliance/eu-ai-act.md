# EU AI Act — AgentMesh Compliance Mapping

How AgentMesh features map to the requirements of the [EU AI Act](https://artificialintelligenceact.eu/) (Regulation (EU) 2024/1689).

> **Disclaimer:** AgentMesh is a tool that helps achieve compliance — it is not a compliance certification. Consult legal counsel for your specific obligations.

---

## Table of Contents

- [Risk Classification](#risk-classification)
- [Transparency Requirements](#transparency-requirements)
- [Human Oversight](#human-oversight)
- [Technical Documentation](#technical-documentation)
- [Record Keeping](#record-keeping)
- [Accuracy and Robustness](#accuracy-and-robustness)
- [Gaps and Roadmap](#gaps-and-roadmap)

---

## Risk Classification

The EU AI Act classifies AI systems into risk tiers. AgentMesh's governance layer helps operators classify and enforce policies based on risk level.

| EU AI Act Requirement | AgentMesh Feature | Status |
|----------------------|-------------------|--------|
| Risk classification of AI systems (Art. 6) | Policy engine supports risk-tier labels on agents and tools | ✅ Supported |
| Prohibited practices (Art. 5) | Tool blocklists and capability scoping prevent designated prohibited uses | ✅ Supported |
| High-risk system requirements (Art. 8–15) | Governance rules can enforce stricter controls (approval workflows, logging) for high-risk agents | ✅ Supported |

### Mapping Risk Tiers to Trust Scores

| EU AI Act Risk Tier | Recommended Minimum Trust Score | Policy Action |
|--------------------|--------------------------------|---------------|
| Unacceptable | N/A — blocked | `deny` |
| High-risk | ≥ 700 (Trusted) | `require_approval` + enhanced audit |
| Limited-risk | ≥ 500 (Standard) | `allow` + transparency logging |
| Minimal-risk | ≥ 300 (Probationary) | `allow` |

---

## Transparency Requirements

| EU AI Act Requirement | AgentMesh Feature | Status |
|----------------------|-------------------|--------|
| AI system must be transparent to users (Art. 13) | AI Card discovery publishes agent capabilities, identity, and trust score | ✅ Supported |
| Inform users they are interacting with AI (Art. 50) | `AgentIdentity` and `AICard` carry `agent_type` metadata; `UserContext` propagates human-vs-agent origin | ✅ Supported |
| Provide instructions for use (Art. 13) | AI Card schema includes `capabilities`, `description`, and supported protocols | ✅ Supported |
| Labeling of AI-generated content (Art. 50) | Audit trail records which agent produced each output with cryptographic signatures | ✅ Supported |

---

## Human Oversight

| EU AI Act Requirement | AgentMesh Feature | Status |
|----------------------|-------------------|--------|
| Human oversight measures (Art. 14) | `require_approval` policy verdict pauses execution for human review | ✅ Supported |
| Ability to override/intervene (Art. 14) | Credential revocation (≤ 5 s propagation) and trust score override provide kill-switch capability | ✅ Supported |
| Human-in-the-loop for high-risk (Art. 14) | Delegation chains are rooted at a human sponsor; `UserContext` tracks the authorizing human | ✅ Supported |
| Monitoring capability (Art. 14) | Merkle audit logs, anomaly detection (5 classes), and Prometheus metrics provide real-time oversight | ✅ Supported |

---

## Technical Documentation

| EU AI Act Requirement | AgentMesh Feature | Status |
|----------------------|-------------------|--------|
| Technical documentation (Art. 11) | Agent SBOM (RFC), AI Card metadata, architecture documentation | ✅ Supported |
| Description of system purpose (Art. 11) | AI Card `description` and `capabilities` fields | ✅ Supported |
| System architecture description (Art. 11) | ARCHITECTURE.md documents the 4-layer trust stack | ✅ Supported |
| Data governance measures (Art. 10) | Policy engine enforces data access rules; `UserContext` enables per-user data policies | 🚧 Partial |

---

## Record Keeping

| EU AI Act Requirement | AgentMesh Feature | Status |
|----------------------|-------------------|--------|
| Automatic logging (Art. 12) | Merkle-chained audit logs with CloudEvents export (Azure Event Grid, AWS EventBridge, Splunk) | ✅ Supported |
| Log retention for appropriate period (Art. 12) | Persistent audit storage with configurable retention | ✅ Supported |
| Tamper-evident records (Art. 12) | Merkle tree hash chain with `verify_integrity()` tamper detection | ✅ Supported |
| Traceability (Art. 12) | Delegation chains trace every action to a human sponsor | ✅ Supported |

---

## Accuracy and Robustness

| EU AI Act Requirement | AgentMesh Feature | Status |
|----------------------|-------------------|--------|
| Accuracy and robustness (Art. 15) | Trust scoring tracks output quality dimension (20% weight) | ✅ Supported |
| Cybersecurity measures (Art. 15) | Ed25519 cryptographic identity, SPIFFE mTLS, zero-trust verification | ✅ Supported |
| Resilience against errors (Art. 15) | Anomaly detection, trust decay, and automatic credential rotation | ✅ Supported |

---

## Gaps and Roadmap

| EU AI Act Requirement | Gap | Planned Mitigation |
|----------------------|-----|-------------------|
| Conformity assessment (Art. 43) | No built-in conformity self-assessment tooling | Planned: governance rule templates for conformity checklists |
| Fundamental rights impact assessment (Art. 27) | No automated FRIA tooling | Planned: compliance module extension for FRIA templates |
| Per-user data governance (Art. 10) | `UserContext` exists but per-user data access policies are roadmap | In progress: per-user policy rules |
| Market surveillance reporting (Art. 62) | No automated reporting to national authorities | Planned: export templates for regulatory submissions |

---

*See also: [SECURITY.md](../../SECURITY.md) · [SOC2 Mapping](soc2-mapping.md) · [NIST AI RMF](nist-ai-rmf.md) · [ISO 42001](iso-42001.md)*
