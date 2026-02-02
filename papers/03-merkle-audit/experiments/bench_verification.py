"""
Merkle Audit Verification Benchmark

Measures verification latency for Merkle proofs vs full chain verification.
Demonstrates O(log n) vs O(n) verification complexity.

Key metrics:
1. Single entry proof generation time
2. Single entry proof verification time
3. Full chain verification time
4. Scalability across log sizes

Output: CSV with verification metrics.
"""

import sys
import time
import statistics
import csv
import random
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from agentmesh.governance.audit import AuditLog, MerkleAuditChain


@dataclass
class VerificationResult:
    """Results from verification benchmark."""
    
    log_size: int
    proof_generation_ms: float
    proof_verification_ms: float
    full_chain_verification_ms: float
    merkle_tree_depth: int
    speedup_factor: float


def create_populated_log(size: int) -> AuditLog:
    """Create an audit log with specified number of entries."""
    log = AuditLog()
    
    for i in range(size):
        log.log(
            event_type=f"event_type_{i % 10}",
            agent_did=f"did:mesh:agent_{i % 50}",
            action=f"action_{i % 20}",
            resource=f"/resource/{i}",
            data={"entry_number": i},
        )
    
    return log


def benchmark_proof_generation(log: AuditLog, num_samples: int = 100) -> float:
    """Benchmark Merkle proof generation time."""
    entries = log._chain._entries
    if not entries:
        return 0.0
    
    sample_ids = [
        random.choice(entries).entry_id
        for _ in range(min(num_samples, len(entries)))
    ]
    
    latencies = []
    for entry_id in sample_ids:
        start = time.perf_counter()
        log.get_proof(entry_id)
        end = time.perf_counter()
        latencies.append((end - start) * 1000)
    
    return statistics.mean(latencies)


def benchmark_proof_verification(log: AuditLog, num_samples: int = 100) -> float:
    """Benchmark Merkle proof verification time."""
    entries = log._chain._entries
    chain = log._chain
    
    if not entries or not chain.get_root_hash():
        return 0.0
    
    # Pre-generate proofs
    proofs = []
    for _ in range(min(num_samples, len(entries))):
        entry = random.choice(entries)
        proof = chain.get_proof(entry.entry_id)
        if proof:
            proofs.append((entry.entry_hash, proof, chain.get_root_hash()))
    
    if not proofs:
        return 0.0
    
    # Benchmark verification
    latencies = []
    for entry_hash, proof, root_hash in proofs:
        start = time.perf_counter()
        chain.verify_proof(entry_hash, proof, root_hash)
        end = time.perf_counter()
        latencies.append((end - start) * 1000)
    
    return statistics.mean(latencies)


def benchmark_full_chain_verification(log: AuditLog, num_iterations: int = 5) -> float:
    """Benchmark full chain verification time."""
    latencies = []
    
    for _ in range(num_iterations):
        start = time.perf_counter()
        log.verify_integrity()
        end = time.perf_counter()
        latencies.append((end - start) * 1000)
    
    return statistics.mean(latencies)


def get_merkle_tree_depth(log: AuditLog) -> int:
    """Get the depth of the Merkle tree."""
    return len(log._chain._tree)


def run_verification_benchmarks(
    sizes: list[int] = None,
    output_dir: Path = None,
) -> list[VerificationResult]:
    """Run verification benchmarks across different log sizes."""
    
    if sizes is None:
        sizes = [100, 500, 1000, 5000, 10000, 50000, 100000]
    
    results = []
    
    print(f"\n{'='*70}")
    print("Merkle Audit Verification Benchmark")
    print(f"{'='*70}\n")
    
    print(f"{'Size':>10} {'Proof Gen':>12} {'Proof Ver':>12} {'Full Chain':>12} {'Speedup':>10}")
    print("-" * 70)
    
    for size in sizes:
        print(f"\rPopulating log with {size:,} entries...", end="", flush=True)
        log = create_populated_log(size)
        print(f"\rBenchmarking {size:,} entries...          ", end="", flush=True)
        
        proof_gen = benchmark_proof_generation(log)
        proof_ver = benchmark_proof_verification(log)
        full_chain = benchmark_full_chain_verification(log)
        tree_depth = get_merkle_tree_depth(log)
        
        # Speedup: how much faster is Merkle proof vs full chain
        speedup = full_chain / proof_ver if proof_ver > 0 else 0
        
        result = VerificationResult(
            log_size=size,
            proof_generation_ms=proof_gen,
            proof_verification_ms=proof_ver,
            full_chain_verification_ms=full_chain,
            merkle_tree_depth=tree_depth,
            speedup_factor=speedup,
        )
        results.append(result)
        
        print(f"\r{size:>10,} {proof_gen:>12.3f} {proof_ver:>12.3f} {full_chain:>12.3f} {speedup:>10.1f}x")
    
    # Summary
    print(f"\n{'='*70}")
    print("Analysis: O(log n) vs O(n) Verification")
    print(f"{'='*70}")
    
    if len(results) >= 2:
        small = results[0]
        large = results[-1]
        
        size_ratio = large.log_size / small.log_size
        proof_ratio = large.proof_verification_ms / small.proof_verification_ms if small.proof_verification_ms > 0 else 0
        chain_ratio = large.full_chain_verification_ms / small.full_chain_verification_ms if small.full_chain_verification_ms > 0 else 0
        
        print(f"Log size increased {size_ratio:.0f}x ({small.log_size:,} → {large.log_size:,})")
        print(f"Merkle proof verification increased {proof_ratio:.1f}x (expected ~{small.merkle_tree_depth/large.merkle_tree_depth if large.merkle_tree_depth > 0 else 0:.1f}x for O(log n))")
        print(f"Full chain verification increased {chain_ratio:.1f}x (expected ~{size_ratio:.0f}x for O(n))")
    
    # Write CSV output
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        csv_path = output_dir / "verification_results.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "log_size", "proof_generation_ms", "proof_verification_ms",
                "full_chain_verification_ms", "merkle_tree_depth", "speedup_factor"
            ])
            writer.writeheader()
            for r in results:
                writer.writerow({
                    "log_size": r.log_size,
                    "proof_generation_ms": f"{r.proof_generation_ms:.4f}",
                    "proof_verification_ms": f"{r.proof_verification_ms:.4f}",
                    "full_chain_verification_ms": f"{r.full_chain_verification_ms:.4f}",
                    "merkle_tree_depth": r.merkle_tree_depth,
                    "speedup_factor": f"{r.speedup_factor:.2f}",
                })
        print(f"\nResults written to: {csv_path}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark Merkle audit verification performance"
    )
    parser.add_argument(
        "--sizes", type=str, default="100,500,1000,5000,10000",
        help="Comma-separated log sizes to benchmark (default: 100,500,1000,5000,10000)"
    )
    parser.add_argument(
        "--output", type=str, default="results",
        help="Output directory for results (default: results)"
    )
    
    args = parser.parse_args()
    
    sizes = [int(s.strip()) for s in args.sizes.split(",")]
    
    run_verification_benchmarks(
        sizes=sizes,
        output_dir=Path(args.output),
    )


if __name__ == "__main__":
    main()
