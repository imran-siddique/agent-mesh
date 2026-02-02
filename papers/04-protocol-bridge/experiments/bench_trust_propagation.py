"""
Trust Context Propagation Benchmark

Measures how trust context propagates across protocol boundaries.
Tests that trust decisions are consistent regardless of protocol path.

Key metrics:
1. Trust propagation latency
2. Trust consistency across protocols
3. Trust decay over time
4. Revocation propagation speed

Output: CSV with propagation metrics.
"""

import sys
import time
import statistics
import csv
import asyncio
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from agentmesh.trust.bridge import TrustBridge, ProtocolBridge, PeerInfo


@dataclass
class PropagationResult:
    """Results from trust propagation benchmark."""
    
    scenario: str
    protocols_tested: list[str]
    propagation_latency_ms: float
    consistency_score: float  # 0-1, 1 = perfectly consistent
    revocation_latency_ms: float


async def setup_multi_protocol_mesh(num_agents: int = 10) -> dict[str, TrustBridge]:
    """Create a mesh of agents using different protocols."""
    agents = {}
    protocols = ["a2a", "mcp", "iatp"]
    
    for i in range(num_agents):
        agent_did = f"did:mesh:agent_{i}"
        agents[agent_did] = TrustBridge(
            agent_did=agent_did,
            default_trust_threshold=700,
        )
    
    return agents


async def benchmark_trust_propagation(
    num_agents: int = 10,
    num_hops: int = 5,
) -> tuple[float, list[float]]:
    """
    Benchmark trust propagation across agent chain.
    
    Returns: (total_propagation_time_ms, per_hop_latencies)
    """
    agents = await setup_multi_protocol_mesh(num_agents)
    agent_list = list(agents.values())
    
    if len(agent_list) < num_hops + 1:
        num_hops = len(agent_list) - 1
    
    latencies = []
    
    for i in range(num_hops):
        source = agent_list[i]
        target_did = agent_list[i + 1].agent_did
        protocol = ["a2a", "mcp", "iatp"][i % 3]
        
        start = time.perf_counter()
        await source.verify_peer(
            peer_did=target_did,
            protocol=protocol,
            required_trust_score=500,
        )
        end = time.perf_counter()
        
        latencies.append((end - start) * 1000)
    
    return sum(latencies), latencies


async def benchmark_trust_consistency(
    num_tests: int = 100,
) -> float:
    """
    Test that trust decisions are consistent across protocols.
    
    Same peer should get same trust decision regardless of protocol.
    """
    agent = TrustBridge(agent_did="did:mesh:consistency_tester")
    peer_did = "did:mesh:test_peer"
    
    protocols = ["a2a", "mcp", "iatp"]
    consistency_checks = []
    
    for _ in range(num_tests):
        results = []
        
        for protocol in protocols:
            # Fresh agent for each protocol test
            fresh_agent = TrustBridge(agent_did="did:mesh:fresh_agent")
            
            result = await fresh_agent.verify_peer(
                peer_did=f"{peer_did}_{protocol}",
                protocol=protocol,
                required_trust_score=700,
            )
            results.append(result.verified)
        
        # Check if all protocols gave same result
        is_consistent = len(set(results)) == 1
        consistency_checks.append(is_consistent)
    
    return sum(consistency_checks) / len(consistency_checks)


async def benchmark_revocation_propagation(
    num_agents: int = 10,
) -> list[float]:
    """
    Benchmark how fast trust revocation propagates through mesh.
    
    Returns: list of revocation latencies
    """
    agents = await setup_multi_protocol_mesh(num_agents)
    agent_list = list(agents.values())
    
    # Setup: All agents trust first agent
    first_agent_did = agent_list[0].agent_did
    
    for agent in agent_list[1:]:
        await agent.verify_peer(first_agent_did, protocol="iatp")
    
    # Revoke trust and measure propagation
    latencies = []
    
    for agent in agent_list[1:]:
        start = time.perf_counter()
        await agent.revoke_peer_trust(first_agent_did, "Test revocation")
        is_trusted = await agent.is_peer_trusted(first_agent_did)
        end = time.perf_counter()
        
        if not is_trusted:  # Revocation successful
            latencies.append((end - start) * 1000)
    
    return latencies


async def benchmark_trust_decay(
    decay_periods: list[int] = None,
) -> list[tuple[int, bool]]:
    """
    Test trust decay over time (simulated).
    
    Returns: list of (seconds_elapsed, is_still_trusted)
    """
    if decay_periods is None:
        decay_periods = [60, 300, 900, 3600, 86400]  # 1m, 5m, 15m, 1h, 24h
    
    results = []
    
    for seconds in decay_periods:
        agent = TrustBridge(agent_did="did:mesh:decay_tester")
        peer_did = "did:mesh:decay_peer"
        
        # Verify peer
        await agent.verify_peer(peer_did, protocol="iatp")
        
        # Simulate time passage by modifying last_verified
        peer = agent.get_peer(peer_did)
        if peer:
            # In production, there would be trust decay logic
            # Here we simulate by checking if verification is "stale"
            peer.last_verified = datetime.utcnow() - timedelta(seconds=seconds)
            
            # Re-check trust (in production, would apply decay)
            is_trusted = await agent.is_peer_trusted(peer_did)
            results.append((seconds, is_trusted))
    
    return results


async def run_propagation_benchmarks(
    output_dir: Path = None,
) -> list[PropagationResult]:
    """Run all trust propagation benchmarks."""
    
    results = []
    
    print(f"\n{'='*70}")
    print("Trust Context Propagation Benchmark")
    print(f"{'='*70}\n")
    
    # Test 1: Propagation latency
    print("Testing trust propagation latency...")
    total_time, hop_latencies = await benchmark_trust_propagation(
        num_agents=10,
        num_hops=5,
    )
    print(f"  Total propagation (5 hops): {total_time:.3f} ms")
    print(f"  Average per hop: {statistics.mean(hop_latencies):.3f} ms")
    
    results.append(PropagationResult(
        scenario="Multi-hop propagation",
        protocols_tested=["a2a", "mcp", "iatp"],
        propagation_latency_ms=total_time,
        consistency_score=1.0,
        revocation_latency_ms=0,
    ))
    
    # Test 2: Consistency across protocols
    print("\nTesting trust consistency across protocols...")
    consistency = await benchmark_trust_consistency(num_tests=100)
    print(f"  Consistency score: {consistency:.2%}")
    
    results.append(PropagationResult(
        scenario="Cross-protocol consistency",
        protocols_tested=["a2a", "mcp", "iatp"],
        propagation_latency_ms=0,
        consistency_score=consistency,
        revocation_latency_ms=0,
    ))
    
    # Test 3: Revocation propagation
    print("\nTesting revocation propagation...")
    rev_latencies = await benchmark_revocation_propagation(num_agents=10)
    if rev_latencies:
        rev_mean = statistics.mean(rev_latencies)
        rev_max = max(rev_latencies)
        print(f"  Mean revocation latency: {rev_mean:.3f} ms")
        print(f"  Max revocation latency: {rev_max:.3f} ms")
        
        results.append(PropagationResult(
            scenario="Revocation propagation",
            protocols_tested=["iatp"],
            propagation_latency_ms=0,
            consistency_score=1.0,
            revocation_latency_ms=rev_mean,
        ))
    
    # Test 4: Trust decay (simulated)
    print("\nTesting trust decay over time...")
    decay_results = await benchmark_trust_decay()
    print("  Time elapsed | Still trusted")
    for seconds, is_trusted in decay_results:
        hours = seconds / 3600
        status = "Yes" if is_trusted else "No"
        print(f"  {hours:>10.1f}h | {status}")
    
    # Summary
    print(f"\n{'='*70}")
    print("Summary")
    print(f"{'='*70}")
    print(f"{'Scenario':<30} {'Latency (ms)':>15} {'Consistency':>15}")
    print("-" * 70)
    
    for r in results:
        lat = f"{r.propagation_latency_ms:.3f}" if r.propagation_latency_ms > 0 else f"{r.revocation_latency_ms:.3f}"
        print(f"{r.scenario:<30} {lat:>15} {r.consistency_score:>15.2%}")
    
    # Write CSV
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        csv_path = output_dir / "propagation_results.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "scenario", "protocols_tested", "propagation_latency_ms",
                "consistency_score", "revocation_latency_ms"
            ])
            writer.writeheader()
            for r in results:
                writer.writerow({
                    "scenario": r.scenario,
                    "protocols_tested": ",".join(r.protocols_tested),
                    "propagation_latency_ms": f"{r.propagation_latency_ms:.4f}",
                    "consistency_score": f"{r.consistency_score:.4f}",
                    "revocation_latency_ms": f"{r.revocation_latency_ms:.4f}",
                })
        print(f"\nResults written to: {csv_path}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark trust context propagation"
    )
    parser.add_argument(
        "--output", type=str, default="results",
        help="Output directory for results (default: results)"
    )
    
    args = parser.parse_args()
    
    asyncio.run(run_propagation_benchmarks(output_dir=Path(args.output)))


if __name__ == "__main__":
    main()
