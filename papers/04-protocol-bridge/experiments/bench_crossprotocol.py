"""
Cross-Protocol Translation Latency Benchmark

Measures latency overhead of protocol translation through the TrustBridge.
Tests A2A ↔ MCP ↔ IATP translations with trust verification.

Key metrics:
1. Direct protocol call latency (baseline)
2. Cross-protocol translation latency
3. Trust verification overhead
4. End-to-end message delivery latency

Output: CSV with latency metrics for each protocol combination.
"""

import sys
import time
import statistics
import csv
import asyncio
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from agentmesh.trust.bridge import TrustBridge, ProtocolBridge, A2AAdapter, MCPAdapter
from agentmesh.trust.handshake import TrustHandshake


@dataclass
class ProtocolLatencyResult:
    """Results from protocol latency benchmark."""
    
    source_protocol: str
    target_protocol: str
    num_messages: int
    latency_mean_ms: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    trust_verification_ms: float
    translation_overhead_ms: float


class MockPeerNetwork:
    """Simulated peer network for benchmarking."""
    
    def __init__(self, num_peers: int = 10):
        self.peers = {}
        for i in range(num_peers):
            peer_did = f"did:mesh:peer_{i}"
            self.peers[peer_did] = {
                "did": peer_did,
                "name": f"peer-agent-{i}",
                "trust_score": 700 + (i * 20) % 300,  # 700-1000
                "capabilities": [f"cap_{j}" for j in range(i % 5 + 1)],
                "protocol": ["a2a", "mcp", "iatp"][i % 3],
            }
    
    def get_peer(self, peer_did: str) -> Optional[dict]:
        return self.peers.get(peer_did)


async def setup_trust_bridge(agent_did: str, network: MockPeerNetwork) -> TrustBridge:
    """Create and configure a TrustBridge with pre-verified peers."""
    bridge = TrustBridge(agent_did=agent_did)
    
    # Pre-verify all peers for baseline
    for peer_did, peer_info in network.peers.items():
        result = await bridge.verify_peer(
            peer_did=peer_did,
            protocol=peer_info["protocol"],
            required_trust_score=500,
        )
    
    return bridge


async def benchmark_direct_protocol(
    bridge: TrustBridge,
    protocol: str,
    num_messages: int,
    target_peer: str,
) -> list[float]:
    """Benchmark direct protocol calls without translation."""
    latencies = []
    
    if protocol == "a2a":
        adapter = A2AAdapter(bridge.agent_did, bridge)
        for _ in range(num_messages):
            start = time.perf_counter()
            await adapter.create_task(target_peer, "test_task", {"value": 42})
            end = time.perf_counter()
            latencies.append((end - start) * 1000)
    
    elif protocol == "mcp":
        adapter = MCPAdapter(bridge.agent_did, bridge)
        adapter.register_tool(
            name="test_tool",
            description="Test tool",
            input_schema={"type": "object"},
        )
        for _ in range(num_messages):
            start = time.perf_counter()
            await adapter.call_tool(target_peer, "test_tool", {"value": 42})
            end = time.perf_counter()
            latencies.append((end - start) * 1000)
    
    return latencies


async def benchmark_cross_protocol(
    protocol_bridge: ProtocolBridge,
    source_protocol: str,
    target_protocol: str,
    num_messages: int,
    target_peer: str,
) -> list[float]:
    """Benchmark cross-protocol message translation."""
    latencies = []
    
    # Create test message in source protocol format
    if source_protocol == "a2a":
        message = {
            "task_type": "execute",
            "parameters": {"action": "test", "value": 42},
        }
    elif source_protocol == "mcp":
        message = {
            "method": "tools/call",
            "params": {"name": "test", "arguments": {"value": 42}},
        }
    else:
        message = {"type": "iatp_message", "payload": {"value": 42}}
    
    for _ in range(num_messages):
        start = time.perf_counter()
        await protocol_bridge.send_message(
            peer_did=target_peer,
            message=message,
            source_protocol=source_protocol,
            target_protocol=target_protocol,
        )
        end = time.perf_counter()
        latencies.append((end - start) * 1000)
    
    return latencies


async def benchmark_trust_verification_overhead(
    num_verifications: int,
) -> list[float]:
    """Measure trust verification latency alone."""
    bridge = TrustBridge(agent_did="did:mesh:benchmark_agent")
    latencies = []
    
    for i in range(num_verifications):
        peer_did = f"did:mesh:new_peer_{i}"
        
        start = time.perf_counter()
        await bridge.verify_peer(peer_did=peer_did, protocol="iatp")
        end = time.perf_counter()
        
        latencies.append((end - start) * 1000)
    
    return latencies


async def run_protocol_benchmarks(
    num_messages: int = 1000,
    output_dir: Path = None,
) -> list[ProtocolLatencyResult]:
    """Run all cross-protocol latency benchmarks."""
    
    protocols = ["a2a", "mcp", "iatp"]
    results = []
    
    print(f"\n{'='*80}")
    print("Cross-Protocol Translation Latency Benchmark")
    print(f"Messages per test: {num_messages:,}")
    print(f"{'='*80}\n")
    
    # Setup network and bridge
    network = MockPeerNetwork(num_peers=30)
    agent_did = "did:mesh:benchmark_agent"
    trust_bridge = await setup_trust_bridge(agent_did, network)
    protocol_bridge = ProtocolBridge(agent_did=agent_did, trust_bridge=trust_bridge)
    
    # Benchmark trust verification overhead
    print("Measuring trust verification overhead...")
    trust_latencies = await benchmark_trust_verification_overhead(100)
    trust_overhead = statistics.mean(trust_latencies)
    print(f"  Trust verification: {trust_overhead:.3f} ms (mean)\n")
    
    print(f"{'Source':<10} {'Target':<10} {'Mean (ms)':>12} {'p95 (ms)':>12} {'p99 (ms)':>12} {'Overhead':>12}")
    print("-" * 80)
    
    # Get a peer for each protocol
    peers_by_protocol = {}
    for peer_did, peer_info in network.peers.items():
        proto = peer_info["protocol"]
        if proto not in peers_by_protocol:
            peers_by_protocol[proto] = peer_did
    
    # Benchmark each protocol combination
    for source in protocols:
        for target in protocols:
            target_peer = peers_by_protocol.get(target, list(network.peers.keys())[0])
            
            # Run benchmark
            latencies = await benchmark_cross_protocol(
                protocol_bridge,
                source,
                target,
                num_messages,
                target_peer,
            )
            
            sorted_latencies = sorted(latencies)
            mean = statistics.mean(latencies)
            p50 = sorted_latencies[int(len(sorted_latencies) * 0.50)]
            p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)]
            p99 = sorted_latencies[int(len(sorted_latencies) * 0.99)]
            
            # Calculate translation overhead (compared to same-protocol baseline)
            if source == target:
                baseline = mean
            overhead = mean - baseline if source != target else 0
            
            result = ProtocolLatencyResult(
                source_protocol=source,
                target_protocol=target,
                num_messages=num_messages,
                latency_mean_ms=mean,
                latency_p50_ms=p50,
                latency_p95_ms=p95,
                latency_p99_ms=p99,
                trust_verification_ms=trust_overhead,
                translation_overhead_ms=overhead,
            )
            results.append(result)
            
            overhead_str = f"+{overhead:.3f}" if overhead > 0 else f"{overhead:.3f}"
            print(f"{source:<10} {target:<10} {mean:>12.3f} {p95:>12.3f} {p99:>12.3f} {overhead_str:>12}")
    
    # Summary
    print(f"\n{'='*80}")
    print("Analysis: Cross-Protocol Translation Overhead")
    print(f"{'='*80}")
    
    same_protocol = [r for r in results if r.source_protocol == r.target_protocol]
    cross_protocol = [r for r in results if r.source_protocol != r.target_protocol]
    
    if same_protocol and cross_protocol:
        same_avg = statistics.mean([r.latency_mean_ms for r in same_protocol])
        cross_avg = statistics.mean([r.latency_mean_ms for r in cross_protocol])
        overhead_pct = ((cross_avg / same_avg) - 1) * 100 if same_avg > 0 else 0
        
        print(f"Same-protocol average:  {same_avg:.3f} ms")
        print(f"Cross-protocol average: {cross_avg:.3f} ms")
        print(f"Translation overhead:   {overhead_pct:.1f}%")
    
    # Write CSV
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        csv_path = output_dir / "crossprotocol_results.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "source_protocol", "target_protocol", "num_messages",
                "latency_mean_ms", "latency_p50_ms", "latency_p95_ms",
                "latency_p99_ms", "trust_verification_ms", "translation_overhead_ms"
            ])
            writer.writeheader()
            for r in results:
                writer.writerow({
                    "source_protocol": r.source_protocol,
                    "target_protocol": r.target_protocol,
                    "num_messages": r.num_messages,
                    "latency_mean_ms": f"{r.latency_mean_ms:.4f}",
                    "latency_p50_ms": f"{r.latency_p50_ms:.4f}",
                    "latency_p95_ms": f"{r.latency_p95_ms:.4f}",
                    "latency_p99_ms": f"{r.latency_p99_ms:.4f}",
                    "trust_verification_ms": f"{r.trust_verification_ms:.4f}",
                    "translation_overhead_ms": f"{r.translation_overhead_ms:.4f}",
                })
        print(f"\nResults written to: {csv_path}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark cross-protocol translation latency"
    )
    parser.add_argument(
        "--messages", type=int, default=1000,
        help="Number of messages per test (default: 1000)"
    )
    parser.add_argument(
        "--output", type=str, default="results",
        help="Output directory for results (default: results)"
    )
    
    args = parser.parse_args()
    
    asyncio.run(run_protocol_benchmarks(
        num_messages=args.messages,
        output_dir=Path(args.output),
    ))


if __name__ == "__main__":
    main()
