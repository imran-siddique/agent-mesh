# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for AgentMesh.

ADRs document significant architectural decisions made during the development of the
trust-first communication layer for AI agents.

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [001](001-ed25519-keys.md) | Ed25519 for Agent Identity Keys | Accepted | 2025-01-15 |
| [002](002-trust-scoring-algorithm.md) | 5-Dimension Weighted Trust Scoring (0–1000) | Accepted | 2025-01-20 |
| [003](003-delegation-chain-design.md) | Chained Delegation vs Flat Authorization | Accepted | 2025-02-01 |
| [004](004-http-middleware-approach.md) | Framework-Specific HTTP Middleware | Accepted | 2025-02-10 |

## Template

New ADRs should follow this structure:

```markdown
# ADR-NNN: Title

## Status
Accepted | Proposed | Deprecated | Superseded by ADR-NNN

## Context
What is the issue that we're seeing that is motivating this decision?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or more difficult to do because of this change?
```
