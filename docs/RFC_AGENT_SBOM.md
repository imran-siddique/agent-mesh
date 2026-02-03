# RFC: Agent-SBOM - Software Bill of Materials for AI Agents

**Status:** Draft  
**Author:** Imran Siddique (@imran-siddique)  
**Created:** 2026-02-03  
**Target:** LF AI & Data Foundation

## Abstract

This RFC proposes a standardized format for describing the capabilities, dependencies, and risk profile of AI agents: the **Agent-SBOM** (Agent Software Bill of Materials).

Just as traditional SBOMs enumerate software dependencies for supply chain security, Agent-SBOMs enumerate an agent's:
- Model dependencies
- Tool access capabilities
- Human sponsor accountability
- Trust boundaries

## Motivation

### The Problem

Modern AI agents are opaque. When an organization deploys an agent, they have no standard way to answer:

1. **What model powers this agent?** (GPT-4, Claude, Llama, fine-tuned?)
2. **What tools can it access?** (filesystem, network, databases, APIs?)
3. **Who is accountable?** (Which human/organization sponsors this agent?)
4. **What are its trust boundaries?** (Can it delegate? To whom?)

### Why This Matters

- **Security teams** need to assess agent risk before deployment
- **Compliance officers** need to audit agent capabilities
- **Platform operators** need to enforce capability boundaries
- **Other agents** need to verify trust before interaction

### Prior Art

| Standard | Domain | Gap for Agents |
|----------|--------|----------------|
| SBOM (SPDX, CycloneDX) | Software dependencies | No model/capability info |
| Model Cards | ML models | No tool/delegation info |
| SLSA | Build provenance | No runtime behavior |
| OAuth Scopes | API permissions | No AI-specific semantics |

## Specification

### Agent-SBOM Format

```json
{
  "$schema": "https://agentmesh.dev/schemas/agent-sbom/v1.json",
  "sbomVersion": "1.0",
  "agentId": "did:mesh:abc123",
  "agentName": "CustomerServiceBot",
  "version": "2.1.0",
  "created": "2026-02-03T12:00:00Z",
  
  "sponsor": {
    "type": "organization",
    "name": "Acme Corp",
    "contact": "ai-governance@acme.com",
    "verificationMethod": "dns-txt"
  },
  
  "model": {
    "provider": "anthropic",
    "model": "claude-3-sonnet",
    "version": "20240229",
    "fineTuned": false,
    "quantization": null
  },
  
  "capabilities": {
    "tools": [
      {
        "name": "database:query",
        "access": "read",
        "constraints": ["no-pii-columns"]
      },
      {
        "name": "api:http",
        "access": "invoke",
        "constraints": ["allowlist-only"],
        "allowlist": ["api.acme.com", "api.partner.com"]
      }
    ],
    "delegation": {
      "canDelegate": true,
      "maxDepth": 2,
      "narrowingRequired": true
    },
    "humanInLoop": {
      "required": ["financial-transactions", "pii-access"],
      "timeout": "5m"
    }
  },
  
  "policies": [
    {
      "id": "policy-no-pii",
      "name": "No PII Exposure",
      "version": "1.0",
      "hash": "sha256:abc123..."
    }
  ],
  
  "trust": {
    "initialScore": 800,
    "tier": "Verified",
    "attestations": [
      {
        "type": "security-audit",
        "auditor": "SecureCo",
        "date": "2026-01-15",
        "reportUrl": "https://..."
      }
    ]
  },
  
  "dependencies": {
    "agents": [
      {
        "did": "did:mesh:helper123",
        "relationship": "delegates-to",
        "capabilities": ["search:web"]
      }
    ],
    "services": [
      {
        "name": "VectorDB",
        "provider": "Pinecone",
        "dataClassification": "internal"
      }
    ]
  },
  
  "riskProfile": {
    "dataAccess": ["internal", "confidential"],
    "networkAccess": true,
    "fileSystemAccess": "read-only",
    "codeExecution": false,
    "estimatedRiskLevel": "medium"
  },
  
  "signatures": {
    "sponsor": "base64:...",
    "platform": "base64:..."
  }
}
```

### Required Fields

| Field | Description |
|-------|-------------|
| `sbomVersion` | Schema version (for forward compatibility) |
| `agentId` | Unique identifier (DID recommended) |
| `agentName` | Human-readable name |
| `sponsor` | Accountable human/organization |
| `model` | AI model information |
| `capabilities.tools` | Enumerated tool access |

### Optional Fields

| Field | Description |
|-------|-------------|
| `capabilities.delegation` | Delegation rules |
| `capabilities.humanInLoop` | HITL requirements |
| `policies` | Attached governance policies |
| `trust` | Trust attestations |
| `dependencies` | Other agents/services used |
| `riskProfile` | Risk assessment summary |
| `signatures` | Cryptographic signatures |

## Use Cases

### 1. Pre-Deployment Risk Assessment

```
Security Team receives Agent-SBOM
→ Checks: Does model meet our approved list?
→ Checks: Are tools within allowed scope?
→ Checks: Is sponsor from trusted organization?
→ Decision: Approve/Deny deployment
```

### 2. Runtime Capability Enforcement

```
Agent attempts to call tool
→ Platform checks Agent-SBOM
→ Tool in capabilities list? 
→ Constraints satisfied?
→ Allow/Block execution
```

### 3. Inter-Agent Trust Verification

```
Agent A wants to delegate to Agent B
→ Agent A retrieves Agent B's SBOM
→ Verifies: Can B handle requested capability?
→ Verifies: Is B's sponsor trusted?
→ Verifies: Does B have required attestations?
→ Proceed/Refuse delegation
```

### 4. Compliance Auditing

```
Auditor requests: "Show all agents with PII access"
→ Query all Agent-SBOMs
→ Filter: riskProfile.dataAccess includes "pii"
→ Generate compliance report
```

## Verification

### Sponsor Verification Methods

| Method | Description |
|--------|-------------|
| `dns-txt` | TXT record at _agentmesh.domain.com |
| `well-known` | /.well-known/agentmesh-sponsor.json |
| `x509` | X.509 certificate chain |
| `did-web` | DID Web resolution |

### SBOM Signing

Agent-SBOMs SHOULD be signed by:
1. **Sponsor:** Attests to agent ownership
2. **Platform:** Attests to capability enforcement

Signature format: JSON Web Signature (JWS)

## Distribution

### Discovery

Agent-SBOMs can be discovered via:

1. **DID Resolution:** `did:mesh:abc123` → SBOM URL
2. **Well-Known:** `https://agent.example.com/.well-known/agent-sbom.json`
3. **Registry:** Query AgentMesh registry by agent ID

### Updates

When agent capabilities change:
1. New SBOM version is published
2. Previous versions remain available (immutable)
3. Changelog included in new version

## Security Considerations

### Tampering
- SBOMs MUST be signed
- Signature verification required before trust decisions

### Information Disclosure
- SBOMs may reveal internal architecture
- Organizations can publish "public" subset
- Full SBOM shared only with authorized parties

### Stale Data
- SBOMs have `created` timestamp
- Consumers SHOULD reject SBOMs older than policy threshold

## Relationship to Other Standards

| Standard | Relationship |
|----------|--------------|
| SPDX | Agent-SBOM extends SBOM concept to agents |
| Model Cards | `model` section inspired by Model Cards |
| SLSA | `signatures` section compatible with SLSA |
| CloudEvents | Audit logs in CloudEvents reference SBOM |
| OPA | Policies can be OPA Rego files |

## Roadmap

### v1.0 (This RFC)
- Core schema definition
- Required/optional fields
- Signing requirements

### v1.1 (Planned)
- Multi-model agent support
- Fine-tuning provenance
- RAG data source attestation

### v2.0 (Future)
- Dynamic capability negotiation
- Real-time SBOM updates
- Cross-platform federation

## Implementation

### Reference Implementation

AgentMesh provides:
- JSON Schema for validation
- Python library for SBOM generation
- CLI tool for SBOM creation/verification

```bash
# Generate SBOM for an agent
agentmesh sbom generate --agent my-agent --output sbom.json

# Verify an SBOM
agentmesh sbom verify sbom.json

# Check agent against SBOM
agentmesh sbom enforce --sbom sbom.json --agent my-agent
```

## Call for Feedback

We invite feedback on:

1. **Schema completeness:** What fields are missing?
2. **Interoperability:** How to align with existing standards?
3. **Adoption:** What would make this useful for your organization?

Submit feedback:
- GitHub: https://github.com/imran-siddique/agent-mesh/discussions
- Email: rfc@agentmesh.dev

---

*This RFC is submitted for consideration by the LF AI & Data Foundation Trusted AI Committee.*
