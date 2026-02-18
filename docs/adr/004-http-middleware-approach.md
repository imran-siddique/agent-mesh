# ADR-004: Framework-Specific HTTP Middleware

## Status

Accepted

## Context

AgentMesh needs to provide HTTP middleware that verifies agent identity and trust scores
on incoming requests. Web applications using AgentMesh must validate `X-Agent-DID`,
`X-Agent-Public-Key`, `X-Agent-Signature`, and `X-Agent-Capabilities` headers before
processing requests from other agents.

Two approaches were considered:

1. **Single generic middleware**: One WSGI/ASGI middleware that works with any Python web
   framework. Framework-agnostic, but requires manual integration and does not leverage
   framework-specific patterns (dependency injection, request context, decorators).
2. **Framework-specific middleware**: Separate implementations for Flask, FastAPI, and
   Django that use each framework's idiomatic patterns — Flask decorators with `g`
   context, FastAPI dependency injection, Django middleware classes with settings.

Key factors:

- **Developer experience**: Most users already know their framework's patterns. Asking
  them to learn a custom middleware API adds friction.
- **Error handling**: Each framework has its own error response conventions (Flask
  `abort()`, FastAPI `HTTPException`, Django `JsonResponse`).
- **Configuration**: Django uses `settings.py`, FastAPI uses Pydantic config, Flask uses
  `app.config` — a generic approach cannot naturally integrate with any of them.
- **Testing**: Framework-specific middleware can use each framework's test client,
  reducing the testing burden on users.

## Decision

Provide **framework-specific middleware** for Flask, FastAPI, and Django, plus a shared
`TrustMiddleware` base class for the core verification logic.

### Architecture

```
TrustMiddleware (base)
├── verify_request(headers) → VerificationResult
├── response_headers() → dict
└── Core Ed25519 signature verification

Flask Integration
├── @flask_trust_required decorator
├── Sets g.trust_result, g.peer_did
└── Returns 401/403 JSON on failure

FastAPI Integration
├── fastapi_trust_required dependency
├── Returns VerificationResult or raises HTTPException
└── Works with FastAPI dependency injection

Django Integration
├── AgentTrustMiddleware class
├── AGENTMESH_* settings in settings.py
├── Sets request.agent_did, request.agent_trust_score
├── @trust_exempt and @trust_required decorators
└── Configurable exempt paths
```

### Framework-Specific Features

| Feature | Flask | FastAPI | Django |
|---------|-------|---------|--------|
| Pattern | `@decorator` | `Depends()` | Middleware class |
| Config | `app.config` | Constructor args | `settings.py` |
| Request context | `flask.g` | Return value | `request.*` attrs |
| Error format | `jsonify` + status | `HTTPException` | `JsonResponse` |
| Per-route override | Decorator presence | Dependency override | `@trust_required(min_score=)` |
| Exempt routes | No decorator | No dependency | `@trust_exempt`, `AGENTMESH_EXEMPT_PATHS` |
| Default min score | 500 | 500 | 500 (`AGENTMESH_MIN_TRUST_SCORE`) |

### Installation

All framework integrations are **optional dependencies** to avoid pulling in Flask,
FastAPI, or Django for users who do not need them:

```toml
[project.optional-dependencies]
flask = ["flask>=2.0"]
fastapi = ["fastapi>=0.100", "uvicorn"]
django = ["django>=4.0"]
```

## Consequences

### Positive

- **Better developer experience**: Users write idiomatic code for their framework.
  A Flask developer uses `@flask_trust_required`, a FastAPI developer uses `Depends()`,
  and a Django developer adds middleware to `MIDDLEWARE` in `settings.py`.
- **Native error handling**: Each integration returns errors in the framework's expected
  format, so API consumers get consistent error responses regardless of whether the
  error came from AgentMesh or the application.
- **Optional dependencies**: Installing `agentmesh[flask]` only pulls in Flask, not
  Django or FastAPI. This keeps the dependency tree minimal.
- **Per-route control**: Django's `@trust_exempt` and `@trust_required(min_score=800)`
  decorators give fine-grained control without global configuration changes.
- **Shared core**: The `TrustMiddleware` base class ensures all frameworks use the same
  signature verification and trust evaluation logic — no divergence in security behavior.

### Negative

- **Maintenance burden**: Three separate integrations must be kept in sync when the core
  verification logic changes. Mitigated by the shared `TrustMiddleware` base class and
  integration-specific test suites.
- **Incomplete coverage**: Only Flask, FastAPI, and Django are supported. Users of other
  frameworks (Starlette, Falcon, Bottle) must use `TrustMiddleware` directly. Mitigated
  by documenting the base class API for custom integrations.
- **Version compatibility**: Each integration must track breaking changes in its target
  framework. Mitigated by pinning minimum versions (`flask>=2.0`, `fastapi>=0.100`,
  `django>=4.0`) and testing against the latest releases in CI.
