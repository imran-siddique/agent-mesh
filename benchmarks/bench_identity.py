"""Identity operation benchmarks for AgentMesh.

Measures Ed25519 key generation, signature creation/verification,
DID generation, and JSON serialization round-trip throughput.
"""

import json
import statistics
import time

from cryptography.hazmat.primitives.asymmetric import ed25519

# Attempt real imports; fall back to stubs if unavailable
try:
    from agentmesh.identity.agent_id import AgentDID, AgentIdentity

    _HAS_AGENTMESH = True
except ImportError:
    _HAS_AGENTMESH = False


ITERATIONS = 1_000
WARMUP = 50
PAYLOAD_1KB = b"x" * 1024


def _percentile(data: list[float], pct: float) -> float:
    """Return the *pct*-th percentile from a sorted list."""
    s = sorted(data)
    idx = int(len(s) * pct / 100)
    return s[min(idx, len(s) - 1)]


def _bench(fn, n: int = ITERATIONS, warmup: int = WARMUP) -> dict:
    """Run *fn* with warmup, return timing stats."""
    for _ in range(warmup):
        fn()
    times: list[float] = []
    for _ in range(n):
        start = time.perf_counter()
        fn()
        elapsed = (time.perf_counter() - start) * 1_000  # ms
        times.append(elapsed)
    mean = statistics.mean(times)
    ops_per_sec = 1_000 / mean if mean > 0 else float("inf")
    return {
        "iterations": n,
        "mean_ms": mean,
        "median_ms": statistics.median(times),
        "p50_ms": _percentile(times, 50),
        "p95_ms": _percentile(times, 95),
        "p99_ms": _percentile(times, 99),
        "min_ms": min(times),
        "max_ms": max(times),
        "stdev_ms": statistics.stdev(times) if n > 1 else 0.0,
        "ops_per_sec": ops_per_sec,
    }


def _make_identity(name: str = "bench") -> "AgentIdentity":
    return AgentIdentity.create(
        name=name,
        sponsor=f"{name}@bench.example.com",
        capabilities=["read", "write"],
    )


# ---------------------------------------------------------------------------
# Benchmarks
# ---------------------------------------------------------------------------


def bench_ed25519_keygen() -> dict:
    """Ed25519 key generation throughput."""
    return _bench(ed25519.Ed25519PrivateKey.generate)


def bench_signature_creation() -> dict:
    """Signature creation throughput (1 KB payload)."""
    key = ed25519.Ed25519PrivateKey.generate()

    def sign():
        key.sign(PAYLOAD_1KB)

    return _bench(sign)


def bench_signature_verification() -> dict:
    """Signature verification throughput (1 KB payload)."""
    key = ed25519.Ed25519PrivateKey.generate()
    sig = key.sign(PAYLOAD_1KB)
    pub = key.public_key()

    def verify():
        pub.verify(sig, PAYLOAD_1KB)

    return _bench(verify)


def bench_did_generation() -> dict | None:
    """DID generation throughput."""
    if not _HAS_AGENTMESH:
        return None

    def generate():
        AgentDID.generate("bench-agent", org="bench-org")

    return _bench(generate)


def bench_json_roundtrip() -> dict | None:
    """JSON serialization/deserialization round-trip."""
    if not _HAS_AGENTMESH:
        return None
    identity = _make_identity()
    doc = identity.to_did_document()

    def roundtrip():
        s = json.dumps(doc)
        json.loads(s)

    return _bench(roundtrip)


def bench_identity_creation() -> dict | None:
    """Full AgentIdentity.create (keygen + DID + model)."""
    if not _HAS_AGENTMESH:
        return None
    return _bench(lambda: _make_identity("bench-create"))


def run_all() -> dict:
    """Run all identity benchmarks and return results dict."""
    results: dict = {}
    benchmarks = [
        ("ed25519_keygen", bench_ed25519_keygen),
        ("signature_creation", bench_signature_creation),
        ("signature_verification", bench_signature_verification),
        ("did_generation", bench_did_generation),
        ("json_roundtrip", bench_json_roundtrip),
        ("identity_creation", bench_identity_creation),
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
    print("=== Identity Benchmarks ===")
    run_all()
