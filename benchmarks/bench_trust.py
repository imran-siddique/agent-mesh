"""Trust engine benchmarks for AgentMesh.

Measures trust score evaluation latency, handshake latency,
score update throughput, decay calculation, and concurrent evaluations.
"""

import asyncio
import math
import statistics
import time

try:
    from agentmesh.identity.agent_id import AgentIdentity
    from agentmesh.trust.handshake import TrustHandshake

    _HAS_AGENTMESH = True
except ImportError:
    _HAS_AGENTMESH = False

ITERATIONS = 1_000
WARMUP = 50


def _percentile(data: list[float], pct: float) -> float:
    s = sorted(data)
    idx = int(len(s) * pct / 100)
    return s[min(idx, len(s) - 1)]


def _bench(fn, n: int = ITERATIONS, warmup: int = WARMUP) -> dict:
    for _ in range(warmup):
        fn()
    times: list[float] = []
    for _ in range(n):
        start = time.perf_counter()
        fn()
        elapsed = (time.perf_counter() - start) * 1_000
        times.append(elapsed)
    mean = statistics.mean(times)
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
        "ops_per_sec": 1_000 / mean if mean > 0 else float("inf"),
    }


def _make_identity(name: str = "bench") -> "AgentIdentity":
    return AgentIdentity.create(
        name=name,
        sponsor=f"{name}@bench.example.com",
        capabilities=["read", "write"],
    )


# ---------------------------------------------------------------------------
# Trust score evaluation (in-memory simulation)
# ---------------------------------------------------------------------------


def bench_trust_score_evaluation() -> dict:
    """Trust score evaluation latency (pure computation)."""
    scores = {f"agent-{i}": 500 + (i * 7 % 500) for i in range(1000)}
    decay_rate = 0.01

    def evaluate():
        for did, score in scores.items():
            _ = max(0, score - decay_rate * score)

    return _bench(evaluate, n=500)


def bench_trust_score_update() -> dict:
    """Score update throughput (records/sec)."""
    records: dict[str, float] = {}
    counter = [0]

    def update():
        key = f"agent-{counter[0] % 10000}"
        records[key] = 500.0 + (counter[0] % 500)
        counter[0] += 1

    return _bench(update, n=10_000)


def bench_decay_calculation() -> dict:
    """Decay calculation overhead."""
    base_score = 800.0
    decay_rate = 0.005

    def decay():
        score = base_score
        for step in range(100):
            score = score * math.exp(-decay_rate * step)
        return score

    return _bench(decay)


def bench_trust_handshake() -> dict | None:
    """Trust verification handshake latency."""
    if not _HAS_AGENTMESH:
        return None
    agent_a = _make_identity("hs-a")
    agent_b = _make_identity("hs-b")
    times: list[float] = []

    async def _run():
        for _ in range(100):
            hs = TrustHandshake(agent_did=str(agent_a.did), identity=agent_a)
            start = time.perf_counter()
            await hs.initiate(
                peer_did=str(agent_b.did),
                required_trust_score=500,
                use_cache=False,
            )
            times.append((time.perf_counter() - start) * 1_000)

    asyncio.run(_run())
    mean = statistics.mean(times)
    return {
        "iterations": len(times),
        "mean_ms": mean,
        "median_ms": statistics.median(times),
        "p50_ms": _percentile(times, 50),
        "p95_ms": _percentile(times, 95),
        "p99_ms": _percentile(times, 99),
        "min_ms": min(times),
        "max_ms": max(times),
        "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0.0,
        "ops_per_sec": 1_000 / mean if mean > 0 else float("inf"),
    }


def bench_concurrent_evaluations() -> dict:
    """Concurrent trust evaluations."""
    scores = {f"agent-{i}": 500 + (i * 13 % 500) for i in range(100)}

    async def _evaluate_one(did: str, score: float):
        await asyncio.sleep(0)  # yield
        return max(0, score * 0.99)

    async def _run_concurrent(n: int):
        tasks = [
            _evaluate_one(did, score)
            for did, score in list(scores.items())[:n]
        ]
        return await asyncio.gather(*tasks)

    times: list[float] = []
    for _ in range(100):
        start = time.perf_counter()
        asyncio.run(_run_concurrent(50))
        times.append((time.perf_counter() - start) * 1_000)

    mean = statistics.mean(times)
    return {
        "iterations": 100,
        "mean_ms": mean,
        "median_ms": statistics.median(times),
        "p50_ms": _percentile(times, 50),
        "p95_ms": _percentile(times, 95),
        "p99_ms": _percentile(times, 99),
        "min_ms": min(times),
        "max_ms": max(times),
        "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0.0,
        "ops_per_sec": 1_000 / mean if mean > 0 else float("inf"),
    }


def run_all() -> dict:
    """Run all trust benchmarks."""
    results: dict = {}
    benchmarks = [
        ("trust_score_evaluation", bench_trust_score_evaluation),
        ("trust_score_update", bench_trust_score_update),
        ("decay_calculation", bench_decay_calculation),
        ("trust_handshake", bench_trust_handshake),
        ("concurrent_evaluations", bench_concurrent_evaluations),
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
    print("=== Trust Benchmarks ===")
    run_all()
