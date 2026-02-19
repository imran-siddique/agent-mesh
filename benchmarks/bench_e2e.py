"""End-to-end governance benchmarks for AgentMesh.

Measures full governance pipeline latency, concurrent agent registration,
and combined handshake + policy + audit flow.
"""

import asyncio
import fnmatch
import hashlib
import statistics
import time
import uuid

try:
    from agentmesh.identity.agent_id import AgentIdentity
    from agentmesh.trust.handshake import TrustHandshake
    from agentmesh.governance.policy import PolicyEngine

    _HAS_AGENTMESH = True
except ImportError:
    _HAS_AGENTMESH = False


ITERATIONS = 500
WARMUP = 20


def _percentile(data: list[float], pct: float) -> float:
    s = sorted(data)
    idx = int(len(s) * pct / 100)
    return s[min(idx, len(s) - 1)]


def _make_identity(name: str = "bench") -> "AgentIdentity":
    return AgentIdentity.create(
        name=name,
        sponsor=f"{name}@bench.example.com",
        capabilities=["read", "write"],
    )


# ---------------------------------------------------------------------------
# Simulated governance pipeline (always available)
# ---------------------------------------------------------------------------

class _SimIdentity:
    def __init__(self, name: str):
        self.did = f"did:mesh:{name}-{uuid.uuid4().hex[:8]}"
        self.name = name

    def sign(self, data: bytes) -> str:
        return hashlib.sha256(data + self.did.encode()).hexdigest()

    def verify(self, data: bytes, sig: str) -> bool:
        return sig == hashlib.sha256(data + self.did.encode()).hexdigest()


class _SimTrustEngine:
    def __init__(self):
        self._scores: dict[str, float] = {}

    def evaluate(self, did: str) -> float:
        if did not in self._scores:
            self._scores[did] = 750.0
        return self._scores[did]

    def handshake(self, a_did: str, b_did: str) -> bool:
        return self.evaluate(a_did) >= 500 and self.evaluate(b_did) >= 500


class _SimPolicyEngine:
    def __init__(self, rules: list[dict]):
        self._rules = rules

    def evaluate(self, did: str, context: dict) -> dict:
        for rule in self._rules:
            match = True
            for key, pattern in rule.get("condition", {}).items():
                if not fnmatch.fnmatch(context.get(key, ""), pattern):
                    match = False
                    break
            if match:
                return {"allowed": True, "rule": rule["name"]}
        return {"allowed": False, "rule": "default_deny"}


class _SimAuditEntry:
    __slots__ = ("entry_id", "timestamp", "agent_did", "action", "outcome", "entry_hash")

    def __init__(self, agent_did: str, action: str, outcome: str):
        self.entry_id = uuid.uuid4().hex[:16]
        self.timestamp = time.time()
        self.agent_did = agent_did
        self.action = action
        self.outcome = outcome
        data = f"{self.entry_id}{self.timestamp}{agent_did}{action}{outcome}"
        self.entry_hash = hashlib.sha256(data.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Benchmarks
# ---------------------------------------------------------------------------

def bench_full_governance_pipeline() -> dict:
    """Full governance pipeline: identity + trust + policy + audit."""
    trust_engine = _SimTrustEngine()
    policy_engine = _SimPolicyEngine([
        {
            "name": "allow-read",
            "condition": {"action": "tool:*"},
            "action": "allow",
        }
    ])
    audit_log: list[_SimAuditEntry] = []

    def pipeline():
        identity = _SimIdentity("bench-agent")
        sig = identity.sign(b"governance-check")
        identity.verify(b"governance-check", sig)
        trust_engine.evaluate(identity.did)
        trust_engine.handshake(identity.did, "did:mesh:peer")
        decision = policy_engine.evaluate(identity.did, {"action": "tool:invoke"})
        entry = _SimAuditEntry(identity.did, "tool:invoke", decision["allowed"])
        audit_log.append(entry)

    # Warmup
    for _ in range(WARMUP):
        pipeline()
    audit_log.clear()

    times: list[float] = []
    for _ in range(ITERATIONS):
        start = time.perf_counter()
        pipeline()
        times.append((time.perf_counter() - start) * 1_000)

    mean = statistics.mean(times)
    return {
        "iterations": ITERATIONS,
        "mean_ms": mean,
        "median_ms": statistics.median(times),
        "p50_ms": _percentile(times, 50),
        "p95_ms": _percentile(times, 95),
        "p99_ms": _percentile(times, 99),
        "min_ms": min(times),
        "max_ms": max(times),
        "stdev_ms": statistics.stdev(times) if ITERATIONS > 1 else 0.0,
        "ops_per_sec": 1_000 / mean if mean > 0 else float("inf"),
    }


def bench_concurrent_agent_registration() -> dict:
    """Concurrent agent registration throughput."""
    registry: dict[str, _SimIdentity] = {}

    async def _register(name: str):
        identity = _SimIdentity(name)
        await asyncio.sleep(0)  # yield
        registry[identity.did] = identity
        return identity

    async def _run(n: int):
        tasks = [_register(f"agent-{i}") for i in range(n)]
        return await asyncio.gather(*tasks)

    batch_size = 100
    times: list[float] = []
    for _ in range(50):
        registry.clear()
        start = time.perf_counter()
        asyncio.run(_run(batch_size))
        times.append((time.perf_counter() - start) * 1_000)

    mean = statistics.mean(times)
    agents_per_sec = batch_size / (mean / 1_000) if mean > 0 else float("inf")
    return {
        "iterations": 50,
        "batch_size": batch_size,
        "mean_ms": mean,
        "median_ms": statistics.median(times),
        "p50_ms": _percentile(times, 50),
        "p95_ms": _percentile(times, 95),
        "p99_ms": _percentile(times, 99),
        "agents_per_sec": agents_per_sec,
        "ops_per_sec": 1_000 / mean if mean > 0 else float("inf"),
    }


def bench_handshake_policy_audit_flow() -> dict:
    """Combined handshake + policy check + audit in one flow."""
    trust_engine = _SimTrustEngine()
    policy_engine = _SimPolicyEngine([
        {
            "name": "allow-trusted",
            "condition": {"action": "tool:*"},
            "action": "allow",
        }
    ])
    audit_log: list[_SimAuditEntry] = []

    def flow():
        agent = _SimIdentity("flow-agent")
        peer = _SimIdentity("flow-peer")
        # Handshake
        trust_engine.handshake(agent.did, peer.did)
        # Policy
        decision = policy_engine.evaluate(agent.did, {"action": "tool:invoke"})
        # Audit
        entry = _SimAuditEntry(agent.did, "tool:invoke", str(decision["allowed"]))
        audit_log.append(entry)

    # Warmup
    for _ in range(WARMUP):
        flow()
    audit_log.clear()

    times: list[float] = []
    for _ in range(ITERATIONS):
        start = time.perf_counter()
        flow()
        times.append((time.perf_counter() - start) * 1_000)

    mean = statistics.mean(times)
    return {
        "iterations": ITERATIONS,
        "mean_ms": mean,
        "median_ms": statistics.median(times),
        "p50_ms": _percentile(times, 50),
        "p95_ms": _percentile(times, 95),
        "p99_ms": _percentile(times, 99),
        "min_ms": min(times),
        "max_ms": max(times),
        "stdev_ms": statistics.stdev(times) if ITERATIONS > 1 else 0.0,
        "ops_per_sec": 1_000 / mean if mean > 0 else float("inf"),
    }


def bench_full_pipeline_with_real_identity() -> dict | None:
    """Full pipeline using real AgentMesh identity (if available)."""
    if not _HAS_AGENTMESH:
        return None

    trust_engine = _SimTrustEngine()
    policy_engine = _SimPolicyEngine([
        {
            "name": "allow-all",
            "condition": {"action": "tool:*"},
            "action": "allow",
        }
    ])
    audit_log: list[_SimAuditEntry] = []
    agent = _make_identity("e2e-agent")
    peer = _make_identity("e2e-peer")

    def pipeline():
        sig = agent.sign(b"e2e-check")
        agent.verify_signature(b"e2e-check", sig)
        trust_engine.evaluate(str(agent.did))
        trust_engine.handshake(str(agent.did), str(peer.did))
        decision = policy_engine.evaluate(str(agent.did), {"action": "tool:invoke"})
        entry = _SimAuditEntry(str(agent.did), "tool:invoke", str(decision["allowed"]))
        audit_log.append(entry)

    # Warmup
    for _ in range(WARMUP):
        pipeline()
    audit_log.clear()

    times: list[float] = []
    for _ in range(ITERATIONS):
        start = time.perf_counter()
        pipeline()
        times.append((time.perf_counter() - start) * 1_000)

    mean = statistics.mean(times)
    return {
        "iterations": ITERATIONS,
        "mean_ms": mean,
        "median_ms": statistics.median(times),
        "p50_ms": _percentile(times, 50),
        "p95_ms": _percentile(times, 95),
        "p99_ms": _percentile(times, 99),
        "min_ms": min(times),
        "max_ms": max(times),
        "stdev_ms": statistics.stdev(times) if ITERATIONS > 1 else 0.0,
        "ops_per_sec": 1_000 / mean if mean > 0 else float("inf"),
    }


def run_all() -> dict:
    """Run all end-to-end benchmarks."""
    results: dict = {}
    benchmarks = [
        ("full_governance_pipeline", bench_full_governance_pipeline),
        ("concurrent_agent_registration", bench_concurrent_agent_registration),
        ("handshake_policy_audit_flow", bench_handshake_policy_audit_flow),
        ("full_pipeline_real_identity", bench_full_pipeline_with_real_identity),
    ]
    for name, fn in benchmarks:
        print(f"  Running {name}...", end=" ", flush=True)
        result = fn()
        if result is not None:
            results[name] = result
            print(f"{result['ops_per_sec']:.0f} ops/sec")
        else:
            print("SKIPPED (import unavailable)")
    return results


if __name__ == "__main__":
    print("=== End-to-End Benchmarks ===")
    run_all()
