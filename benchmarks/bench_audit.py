"""Audit logging benchmarks for AgentMesh.

Measures audit entry write throughput, Merkle chain verification,
audit log query latency, and JSONL export throughput.
"""

import hashlib
import json
import statistics
import time
import uuid

try:
    from agentmesh.governance.audit import AuditEntry, MerkleAuditChain

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


# ---------------------------------------------------------------------------
# Simulated audit structures (fallback when agentmesh unavailable)
# ---------------------------------------------------------------------------

class _SimAuditEntry:
    """Lightweight audit entry for benchmarking."""

    __slots__ = (
        "entry_id", "timestamp", "event_type", "agent_did",
        "action", "resource", "outcome", "previous_hash", "entry_hash",
    )

    def __init__(self, agent_did: str, action: str, previous_hash: str = ""):
        self.entry_id = uuid.uuid4().hex[:16]
        self.timestamp = time.time()
        self.event_type = "governance.action"
        self.agent_did = agent_did
        self.action = action
        self.resource = "tool:benchmark"
        self.outcome = "allow"
        self.previous_hash = previous_hash
        self.entry_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        data = f"{self.entry_id}{self.timestamp}{self.agent_did}{self.action}{self.previous_hash}"
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_hash(self) -> bool:
        return self.entry_hash == self._compute_hash()

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "agent_did": self.agent_did,
            "action": self.action,
            "resource": self.resource,
            "outcome": self.outcome,
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
        }


class _SimMerkleChain:
    """Lightweight Merkle chain for benchmarking."""

    def __init__(self):
        self._entries: list[_SimAuditEntry] = []

    def add_entry(self, entry: _SimAuditEntry):
        if self._entries:
            entry.previous_hash = self._entries[-1].entry_hash
            entry.entry_hash = entry._compute_hash()
        self._entries.append(entry)

    def verify_chain(self) -> bool:
        for i, entry in enumerate(self._entries):
            if not entry.verify_hash():
                return False
            if i > 0 and entry.previous_hash != self._entries[i - 1].entry_hash:
                return False
        return True

    def __len__(self):
        return len(self._entries)


# ---------------------------------------------------------------------------
# Benchmarks
# ---------------------------------------------------------------------------


def bench_audit_entry_write() -> dict:
    """Audit entry write throughput (entries/sec)."""
    chain = _SimMerkleChain()

    def write():
        entry = _SimAuditEntry("did:mesh:bench-agent", "tool:invoke")
        chain.add_entry(entry)

    return _bench(write, n=5_000)


def bench_merkle_chain_verification() -> dict:
    """Merkle chain verification time vs chain length."""
    results = {}
    for length in [100, 1_000, 10_000]:
        chain = _SimMerkleChain()
        for i in range(length):
            entry = _SimAuditEntry(f"did:mesh:agent-{i % 100}", "tool:invoke")
            chain.add_entry(entry)

        times: list[float] = []
        runs = max(3, 50 // (length // 100))
        for _ in range(runs):
            start = time.perf_counter()
            assert chain.verify_chain()
            times.append((time.perf_counter() - start) * 1_000)

        mean = statistics.mean(times)
        results[f"verify_{length}"] = {
            "chain_length": length,
            "iterations": runs,
            "mean_ms": mean,
            "p50_ms": _percentile(times, 50),
            "p95_ms": _percentile(times, 95),
            "p99_ms": _percentile(times, 99),
            "ops_per_sec": 1_000 / mean if mean > 0 else float("inf"),
        }
    return results


def bench_audit_log_query() -> dict:
    """Audit log query latency with different log sizes."""
    results = {}
    for size in [10_000, 100_000]:
        entries = [
            _SimAuditEntry(f"did:mesh:agent-{i % 100}", "tool:invoke").to_dict()
            for i in range(size)
        ]
        target_did = "did:mesh:agent-42"

        times: list[float] = []
        runs = 20 if size <= 10_000 else 5
        for _ in range(runs):
            start = time.perf_counter()
            _ = [e for e in entries if e["agent_did"] == target_did]
            times.append((time.perf_counter() - start) * 1_000)

        mean = statistics.mean(times)
        results[f"query_{size}"] = {
            "log_size": size,
            "iterations": runs,
            "mean_ms": mean,
            "p50_ms": _percentile(times, 50),
            "p95_ms": _percentile(times, 95),
            "p99_ms": _percentile(times, 99),
            "ops_per_sec": 1_000 / mean if mean > 0 else float("inf"),
        }
    return results


def bench_jsonl_export() -> dict:
    """JSONL export throughput."""
    entries = [
        _SimAuditEntry(f"did:mesh:agent-{i % 100}", "tool:invoke").to_dict()
        for i in range(1_000)
    ]

    def export():
        lines = [json.dumps(e) for e in entries]
        return "\n".join(lines)

    return _bench(export, n=100)


def run_all() -> dict:
    """Run all audit benchmarks."""
    results: dict = {}
    print("  Running audit_entry_write...", end=" ", flush=True)
    results["audit_entry_write"] = bench_audit_entry_write()
    print(f"{results['audit_entry_write']['ops_per_sec']:.0f} ops/sec")

    print("  Running merkle_chain_verification...", end=" ", flush=True)
    results["merkle_chain_verification"] = bench_merkle_chain_verification()
    for key, val in results["merkle_chain_verification"].items():
        print(f"\n    {key}: {val['mean_ms']:.2f} ms", end="")
    print()

    print("  Running audit_log_query...", end=" ", flush=True)
    results["audit_log_query"] = bench_audit_log_query()
    for key, val in results["audit_log_query"].items():
        print(f"\n    {key}: {val['mean_ms']:.2f} ms", end="")
    print()

    print("  Running jsonl_export...", end=" ", flush=True)
    results["jsonl_export"] = bench_jsonl_export()
    print(f"{results['jsonl_export']['ops_per_sec']:.0f} ops/sec")

    return results


if __name__ == "__main__":
    print("=== Audit Benchmarks ===")
    run_all()
