"""
Merkle Audit Throughput Benchmark

Measures write throughput for the Merkle-chained audit log system.
Target: 10,000+ entries/second sustained throughput.

Baselines:
1. MerkleAuditChain: Full Merkle tree rebuild on each write
2. SimpleChain: Linear hash chain (no tree)
3. NoChain: Unprotected append-only log

Output: CSV with throughput metrics and latency percentiles.
"""

import sys
import time
import statistics
import csv
from pathlib import Path
from dataclasses import dataclass
from typing import Callable
import hashlib
import json
from datetime import datetime
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from agentmesh.governance.audit import AuditLog, AuditEntry, MerkleAuditChain


@dataclass
class BenchmarkResult:
    """Results from a throughput benchmark run."""
    
    method: str
    total_entries: int
    total_time_seconds: float
    throughput_per_second: float
    latency_mean_ms: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    memory_mb: float


class SimpleChainAuditLog:
    """Baseline: Simple linear hash chain (no Merkle tree)."""
    
    def __init__(self):
        self._entries = []
        self._previous_hash = ""
    
    def log(self, event_type: str, agent_did: str, action: str, **kwargs) -> dict:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "agent_did": agent_did,
            "action": action,
            "previous_hash": self._previous_hash,
        }
        entry["hash"] = hashlib.sha256(
            json.dumps(entry, sort_keys=True).encode()
        ).hexdigest()
        
        self._previous_hash = entry["hash"]
        self._entries.append(entry)
        return entry
    
    def verify_chain(self) -> tuple[bool, str | None]:
        previous = ""
        for i, entry in enumerate(self._entries):
            if entry["previous_hash"] != previous:
                return False, f"Chain broken at entry {i}"
            previous = entry["hash"]
        return True, None


class NoChainAuditLog:
    """Baseline: No tamper protection (append-only list)."""
    
    def __init__(self):
        self._entries = []
    
    def log(self, event_type: str, agent_did: str, action: str, **kwargs) -> dict:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "agent_did": agent_did,
            "action": action,
        }
        self._entries.append(entry)
        return entry


def get_memory_mb() -> float:
    """Get current process memory usage in MB."""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except ImportError:
        return 0.0


def benchmark_write_throughput(
    logger,
    log_func: Callable,
    num_entries: int,
    batch_size: int = 100,
) -> BenchmarkResult:
    """
    Benchmark write throughput for an audit log implementation.
    
    Args:
        logger: Audit log instance
        log_func: Function to call for logging
        num_entries: Total entries to write
        batch_size: Size of batches for intermediate timing
    
    Returns:
        BenchmarkResult with metrics
    """
    latencies = []
    
    start_memory = get_memory_mb()
    start_time = time.perf_counter()
    
    for i in range(num_entries):
        entry_start = time.perf_counter()
        
        log_func(
            event_type="benchmark_event",
            agent_did=f"did:mesh:agent_{i % 100}",
            action="benchmark_action",
            resource=f"/resource/{i}",
            data={"iteration": i, "batch": i // batch_size},
        )
        
        entry_end = time.perf_counter()
        latencies.append((entry_end - entry_start) * 1000)  # ms
    
    end_time = time.perf_counter()
    end_memory = get_memory_mb()
    
    total_time = end_time - start_time
    throughput = num_entries / total_time if total_time > 0 else 0
    
    sorted_latencies = sorted(latencies)
    
    return BenchmarkResult(
        method=type(logger).__name__,
        total_entries=num_entries,
        total_time_seconds=total_time,
        throughput_per_second=throughput,
        latency_mean_ms=statistics.mean(latencies),
        latency_p50_ms=sorted_latencies[int(len(sorted_latencies) * 0.50)],
        latency_p95_ms=sorted_latencies[int(len(sorted_latencies) * 0.95)],
        latency_p99_ms=sorted_latencies[int(len(sorted_latencies) * 0.99)],
        memory_mb=end_memory - start_memory,
    )


def run_benchmarks(
    num_entries: int = 10000,
    output_dir: Path = None,
) -> list[BenchmarkResult]:
    """Run all throughput benchmarks."""
    
    results = []
    
    print(f"\n{'='*60}")
    print(f"Merkle Audit Throughput Benchmark")
    print(f"Entries: {num_entries:,}")
    print(f"{'='*60}\n")
    
    # Benchmark 1: Full MerkleAuditChain
    print("Running: MerkleAuditChain (full Merkle tree)...")
    merkle_log = AuditLog()
    result = benchmark_write_throughput(
        merkle_log,
        merkle_log.log,
        num_entries,
    )
    results.append(result)
    print(f"  Throughput: {result.throughput_per_second:,.1f} entries/sec")
    print(f"  Latency p95: {result.latency_p95_ms:.3f} ms")
    
    # Benchmark 2: SimpleChain (linear chain, no tree)
    print("\nRunning: SimpleChain (linear hash chain)...")
    simple_log = SimpleChainAuditLog()
    result = benchmark_write_throughput(
        simple_log,
        simple_log.log,
        num_entries,
    )
    results.append(result)
    print(f"  Throughput: {result.throughput_per_second:,.1f} entries/sec")
    print(f"  Latency p95: {result.latency_p95_ms:.3f} ms")
    
    # Benchmark 3: NoChain (no protection)
    print("\nRunning: NoChain (no tamper protection)...")
    nochain_log = NoChainAuditLog()
    result = benchmark_write_throughput(
        nochain_log,
        nochain_log.log,
        num_entries,
    )
    results.append(result)
    print(f"  Throughput: {result.throughput_per_second:,.1f} entries/sec")
    print(f"  Latency p95: {result.latency_p95_ms:.3f} ms")
    
    # Print summary table
    print(f"\n{'='*60}")
    print("Summary Results")
    print(f"{'='*60}")
    print(f"{'Method':<25} {'Throughput':>12} {'p95 (ms)':>10} {'p99 (ms)':>10}")
    print("-" * 60)
    
    for r in results:
        print(f"{r.method:<25} {r.throughput_per_second:>12,.0f} {r.latency_p95_ms:>10.3f} {r.latency_p99_ms:>10.3f}")
    
    # Write CSV output
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        csv_path = output_dir / "throughput_results.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "method", "total_entries", "total_time_seconds",
                "throughput_per_second", "latency_mean_ms",
                "latency_p50_ms", "latency_p95_ms", "latency_p99_ms",
                "memory_mb"
            ])
            writer.writeheader()
            for r in results:
                writer.writerow({
                    "method": r.method,
                    "total_entries": r.total_entries,
                    "total_time_seconds": f"{r.total_time_seconds:.3f}",
                    "throughput_per_second": f"{r.throughput_per_second:.1f}",
                    "latency_mean_ms": f"{r.latency_mean_ms:.3f}",
                    "latency_p50_ms": f"{r.latency_p50_ms:.3f}",
                    "latency_p95_ms": f"{r.latency_p95_ms:.3f}",
                    "latency_p99_ms": f"{r.latency_p99_ms:.3f}",
                    "memory_mb": f"{r.memory_mb:.2f}",
                })
        print(f"\nResults written to: {csv_path}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark Merkle audit log write throughput"
    )
    parser.add_argument(
        "--entries", type=int, default=10000,
        help="Number of entries to write (default: 10000)"
    )
    parser.add_argument(
        "--output", type=str, default="results",
        help="Output directory for results (default: results)"
    )
    
    args = parser.parse_args()
    
    run_benchmarks(
        num_entries=args.entries,
        output_dir=Path(args.output),
    )


if __name__ == "__main__":
    main()
