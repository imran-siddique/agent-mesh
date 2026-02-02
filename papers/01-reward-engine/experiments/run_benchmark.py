"""
Continuous Trust Scoring Experiments
=====================================
Benchmark experiments for the RewardEngine paper.

This module implements:
1. Synthetic agent workload generation
2. Baseline comparisons (binary rules, single-dimension, threshold-only)
3. Ablation studies
4. Result visualization

Usage:
    python run_benchmark.py --agents 1000 --duration 86400 --output results/
"""

import asyncio
import json
import random
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import statistics
import csv

# Import AgentMesh components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from agentmesh.reward.engine import RewardEngine, RewardSignal, TrustScore


class AgentType(Enum):
    """Agent behavior categories for benchmark."""
    BENIGN = "benign"           # Normal behavior with occasional noise
    DEGRADING = "degrading"     # Gradual quality decline
    MALICIOUS = "malicious"     # Policy violations after trusted period
    NOISY = "noisy"             # High variance but non-malicious


@dataclass
class SimulatedAgent:
    """A simulated agent for benchmarking."""
    agent_id: str
    agent_type: AgentType
    start_time: float
    degradation_start: Optional[float] = None  # When malicious/degrading behavior begins
    
    # Behavior parameters
    base_compliance: float = 0.95
    base_efficiency: float = 0.85
    base_quality: float = 0.90
    base_security: float = 0.98
    base_collaboration: float = 0.92
    
    # Noise parameters
    noise_std: float = 0.05
    
    def get_signals(self, current_time: float) -> Dict[str, float]:
        """Generate reward signals based on agent type and time."""
        elapsed = current_time - self.start_time
        
        if self.agent_type == AgentType.BENIGN:
            return self._benign_signals()
        elif self.agent_type == AgentType.DEGRADING:
            return self._degrading_signals(elapsed)
        elif self.agent_type == AgentType.MALICIOUS:
            return self._malicious_signals(elapsed)
        elif self.agent_type == AgentType.NOISY:
            return self._noisy_signals()
        
        return self._benign_signals()
    
    def _benign_signals(self) -> Dict[str, float]:
        """Normal behavior with small noise."""
        return {
            "policy_compliance": self._clamp(self.base_compliance + random.gauss(0, self.noise_std)),
            "resource_efficiency": self._clamp(self.base_efficiency + random.gauss(0, self.noise_std)),
            "output_quality": self._clamp(self.base_quality + random.gauss(0, self.noise_std)),
            "security_posture": self._clamp(self.base_security + random.gauss(0, self.noise_std)),
            "collaboration_health": self._clamp(self.base_collaboration + random.gauss(0, self.noise_std)),
        }
    
    def _degrading_signals(self, elapsed: float) -> Dict[str, float]:
        """Gradual degradation over time."""
        # Degradation starts after 2 hours
        if elapsed < 7200:
            return self._benign_signals()
        
        # Linear degradation: lose 0.1 per hour after start
        degradation_hours = (elapsed - 7200) / 3600
        degradation = min(0.6, degradation_hours * 0.1)  # Cap at 0.6 reduction
        
        return {
            "policy_compliance": self._clamp(self.base_compliance - degradation * 0.3 + random.gauss(0, self.noise_std)),
            "resource_efficiency": self._clamp(self.base_efficiency - degradation * 0.5 + random.gauss(0, self.noise_std)),
            "output_quality": self._clamp(self.base_quality - degradation * 0.8 + random.gauss(0, self.noise_std)),
            "security_posture": self._clamp(self.base_security - degradation * 0.2 + random.gauss(0, self.noise_std)),
            "collaboration_health": self._clamp(self.base_collaboration - degradation * 0.4 + random.gauss(0, self.noise_std)),
        }
    
    def _malicious_signals(self, elapsed: float) -> Dict[str, float]:
        """Policy violations after initial trusted period."""
        # Behave normally for first 4 hours
        if elapsed < 14400:
            return self._benign_signals()
        
        # Then start violating policies
        return {
            "policy_compliance": self._clamp(0.2 + random.gauss(0, 0.1)),  # Major violations
            "resource_efficiency": self._clamp(0.4 + random.gauss(0, 0.15)),
            "output_quality": self._clamp(0.5 + random.gauss(0, 0.1)),
            "security_posture": self._clamp(0.1 + random.gauss(0, 0.05)),  # Security breaches
            "collaboration_health": self._clamp(0.3 + random.gauss(0, 0.1)),
        }
    
    def _noisy_signals(self) -> Dict[str, float]:
        """High variance but generally acceptable."""
        return {
            "policy_compliance": self._clamp(self.base_compliance + random.gauss(0, 0.2)),
            "resource_efficiency": self._clamp(self.base_efficiency + random.gauss(0, 0.25)),
            "output_quality": self._clamp(self.base_quality + random.gauss(0, 0.2)),
            "security_posture": self._clamp(self.base_security + random.gauss(0, 0.15)),
            "collaboration_health": self._clamp(self.base_collaboration + random.gauss(0, 0.2)),
        }
    
    @staticmethod
    def _clamp(value: float) -> float:
        """Clamp value to [0, 1]."""
        return max(0.0, min(1.0, value))


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    method: str
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    revocation_latencies: List[float] = field(default_factory=list)
    
    @property
    def precision(self) -> float:
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_positives)
    
    @property
    def recall(self) -> float:
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)
    
    @property
    def f1_score(self) -> float:
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)
    
    @property
    def false_positive_rate(self) -> float:
        if self.false_positives + self.true_negatives == 0:
            return 0.0
        return self.false_positives / (self.false_positives + self.true_negatives)
    
    @property
    def mean_latency(self) -> float:
        if not self.revocation_latencies:
            return float('inf')
        return statistics.mean(self.revocation_latencies)
    
    def to_dict(self) -> Dict:
        return {
            "method": self.method,
            "precision": round(self.precision * 100, 1),
            "recall": round(self.recall * 100, 1),
            "f1_score": round(self.f1_score * 100, 1),
            "false_positive_rate": round(self.false_positive_rate * 100, 1),
            "mean_latency_seconds": round(self.mean_latency, 1) if self.revocation_latencies else "N/A",
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "true_negatives": self.true_negatives,
            "false_negatives": self.false_negatives,
        }


class BinaryRulesBaseline:
    """Baseline: Static binary allow/deny based on identity."""
    
    def __init__(self, known_malicious: set):
        self.known_malicious = known_malicious
        self.revoked = set()
    
    def update(self, agent_id: str, signals: Dict[str, float]) -> bool:
        """Returns True if agent should be revoked."""
        if agent_id in self.known_malicious:
            self.revoked.add(agent_id)
            return True
        return False
    
    def is_revoked(self, agent_id: str) -> bool:
        return agent_id in self.revoked


class SingleDimensionBaseline:
    """Baseline: Trust based only on policy compliance."""
    
    def __init__(self, threshold: float = 0.5, alpha: float = 0.1):
        self.threshold = threshold
        self.alpha = alpha
        self.scores: Dict[str, float] = {}
        self.revoked = set()
    
    def update(self, agent_id: str, signals: Dict[str, float]) -> bool:
        """Returns True if agent should be revoked."""
        if agent_id in self.revoked:
            return True
        
        compliance = signals.get("policy_compliance", 0.5)
        
        if agent_id not in self.scores:
            self.scores[agent_id] = compliance
        else:
            self.scores[agent_id] = self.alpha * compliance + (1 - self.alpha) * self.scores[agent_id]
        
        if self.scores[agent_id] < self.threshold:
            self.revoked.add(agent_id)
            return True
        
        return False
    
    def is_revoked(self, agent_id: str) -> bool:
        return agent_id in self.revoked


class ThresholdOnlyBaseline:
    """Baseline: Fixed threshold without EMA smoothing."""
    
    def __init__(self, threshold: float = 0.4, window: int = 5):
        self.threshold = threshold
        self.window = window
        self.history: Dict[str, List[float]] = {}
        self.revoked = set()
    
    def update(self, agent_id: str, signals: Dict[str, float]) -> bool:
        """Returns True if agent should be revoked."""
        if agent_id in self.revoked:
            return True
        
        # Compute average across all dimensions
        avg_signal = statistics.mean(signals.values())
        
        if agent_id not in self.history:
            self.history[agent_id] = []
        
        self.history[agent_id].append(avg_signal)
        if len(self.history[agent_id]) > self.window:
            self.history[agent_id].pop(0)
        
        # Revoke if recent average below threshold
        if len(self.history[agent_id]) >= self.window:
            recent_avg = statistics.mean(self.history[agent_id])
            if recent_avg < self.threshold:
                self.revoked.add(agent_id)
                return True
        
        return False
    
    def is_revoked(self, agent_id: str) -> bool:
        return agent_id in self.revoked


class RewardEngineWrapper:
    """Wrapper for AgentMesh RewardEngine."""
    
    def __init__(self, revocation_threshold: int = 300):
        self.engine = RewardEngine()
        self.revocation_threshold = revocation_threshold
        self.revoked = set()
        self.first_violation_time: Dict[str, float] = {}
    
    def update(self, agent_id: str, signals: Dict[str, float], current_time: float) -> bool:
        """Returns True if agent should be revoked."""
        if agent_id in self.revoked:
            return True
        
        # Register agent if needed
        if agent_id not in [a for a in self.engine.scores]:
            self.engine.register_agent(agent_id)
        
        # Record signals
        for dimension, value in signals.items():
            signal = RewardSignal(
                agent_id=agent_id,
                dimension=dimension,
                value=value,
                source="benchmark",
                metadata={}
            )
            self.engine.record_signal(signal)
        
        # Check trust score
        score = self.engine.get_score(agent_id)
        if score and score.total_score < self.revocation_threshold:
            self.revoked.add(agent_id)
            return True
        
        # Check for critical dimension drops
        if score:
            for dim_name, dim in score.dimensions.items():
                if dim.score < 100:  # Critical threshold
                    self.revoked.add(agent_id)
                    return True
        
        return False
    
    def is_revoked(self, agent_id: str) -> bool:
        return agent_id in self.revoked


async def run_benchmark(
    num_agents: int = 1000,
    duration_seconds: int = 86400,  # 24 hours
    update_interval: int = 30,  # seconds
    output_dir: Optional[Path] = None,
) -> Dict[str, BenchmarkResult]:
    """
    Run the complete benchmark comparing all methods.
    
    Args:
        num_agents: Number of simulated agents
        duration_seconds: Simulation duration in seconds
        update_interval: How often to update scores (seconds)
        output_dir: Directory to save results
    
    Returns:
        Dictionary mapping method name to BenchmarkResult
    """
    print(f"\n{'='*60}")
    print(f"Continuous Trust Scoring Benchmark")
    print(f"{'='*60}")
    print(f"Agents: {num_agents}")
    print(f"Duration: {duration_seconds/3600:.1f} hours")
    print(f"Update interval: {update_interval}s")
    print()
    
    # Create agents with specified distribution
    agents = create_agent_population(num_agents)
    
    # Count by type
    type_counts = {}
    for agent in agents:
        type_counts[agent.agent_type.value] = type_counts.get(agent.agent_type.value, 0) + 1
    
    print("Agent Distribution:")
    for agent_type, count in type_counts.items():
        print(f"  {agent_type}: {count} ({count/num_agents*100:.1f}%)")
    print()
    
    # Initialize methods
    # For binary rules, assume we know some (but not all) malicious agents
    known_malicious = {a.agent_id for a in agents 
                       if a.agent_type == AgentType.MALICIOUS and random.random() < 0.3}
    
    methods = {
        "binary_rules": BinaryRulesBaseline(known_malicious),
        "single_dimension": SingleDimensionBaseline(threshold=0.5),
        "threshold_only": ThresholdOnlyBaseline(threshold=0.4),
        "reward_engine": RewardEngineWrapper(revocation_threshold=300),
    }
    
    results = {name: BenchmarkResult(method=name) for name in methods}
    
    # Track first violation times for latency calculation
    first_violation: Dict[str, Dict[str, float]] = {name: {} for name in methods}
    revocation_times: Dict[str, Dict[str, float]] = {name: {} for name in methods}
    
    # Run simulation
    num_updates = duration_seconds // update_interval
    print(f"Running {num_updates} updates...")
    
    for update_idx in range(num_updates):
        current_time = update_idx * update_interval
        
        # Progress reporting
        if update_idx % (num_updates // 10) == 0:
            progress = update_idx / num_updates * 100
            print(f"  Progress: {progress:.0f}% (t={current_time/3600:.1f}h)")
        
        for agent in agents:
            signals = agent.get_signals(current_time)
            
            # Determine if agent is currently "bad" (for ground truth)
            is_bad = False
            if agent.agent_type == AgentType.MALICIOUS and current_time >= 14400:
                is_bad = True
            elif agent.agent_type == AgentType.DEGRADING and current_time >= 7200:
                # Degrading becomes "bad" once quality drops significantly
                quality = signals["output_quality"]
                if quality < 0.5:
                    is_bad = True
            
            # Track first violation time
            for method_name in methods:
                if is_bad and agent.agent_id not in first_violation[method_name]:
                    first_violation[method_name][agent.agent_id] = current_time
            
            # Update each method
            for method_name, method in methods.items():
                if method_name == "reward_engine":
                    revoked = method.update(agent.agent_id, signals, current_time)
                else:
                    revoked = method.update(agent.agent_id, signals)
                
                # Track revocation time
                if revoked and agent.agent_id not in revocation_times[method_name]:
                    revocation_times[method_name][agent.agent_id] = current_time
    
    print("\nComputing results...")
    
    # Compute final metrics
    for agent in agents:
        # Ground truth: should this agent have been revoked?
        should_revoke = agent.agent_type in (AgentType.MALICIOUS, AgentType.DEGRADING)
        
        for method_name, method in methods.items():
            was_revoked = method.is_revoked(agent.agent_id)
            
            if should_revoke and was_revoked:
                results[method_name].true_positives += 1
                
                # Calculate latency
                if agent.agent_id in first_violation[method_name] and agent.agent_id in revocation_times[method_name]:
                    latency = revocation_times[method_name][agent.agent_id] - first_violation[method_name][agent.agent_id]
                    results[method_name].revocation_latencies.append(max(0, latency))
                    
            elif should_revoke and not was_revoked:
                results[method_name].false_negatives += 1
            elif not should_revoke and was_revoked:
                results[method_name].false_positives += 1
            else:
                results[method_name].true_negatives += 1
    
    # Print results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"{'Method':<20} {'Precision':>10} {'Recall':>10} {'F1':>10} {'FPR':>10} {'Latency':>12}")
    print("-"*80)
    
    for method_name, result in results.items():
        latency_str = f"{result.mean_latency:.1f}s" if result.revocation_latencies else "N/A"
        print(f"{method_name:<20} {result.precision*100:>9.1f}% {result.recall*100:>9.1f}% "
              f"{result.f1_score*100:>9.1f}% {result.false_positive_rate*100:>9.1f}% {latency_str:>12}")
    
    print("="*80)
    
    # Save results
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save JSON
        with open(output_dir / "results.json", "w") as f:
            json.dump({name: result.to_dict() for name, result in results.items()}, f, indent=2)
        
        # Save CSV
        with open(output_dir / "results.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(results["reward_engine"].to_dict().keys()))
            writer.writeheader()
            for result in results.values():
                writer.writerow(result.to_dict())
        
        print(f"\nResults saved to {output_dir}")
    
    return results


def create_agent_population(num_agents: int) -> List[SimulatedAgent]:
    """Create agent population with specified distribution."""
    agents = []
    
    # Distribution: 70% benign, 15% degrading, 10% malicious, 5% noisy
    distribution = [
        (AgentType.BENIGN, 0.70),
        (AgentType.DEGRADING, 0.15),
        (AgentType.MALICIOUS, 0.10),
        (AgentType.NOISY, 0.05),
    ]
    
    for i in range(num_agents):
        # Select type based on distribution
        rand = random.random()
        cumulative = 0
        selected_type = AgentType.BENIGN
        
        for agent_type, prob in distribution:
            cumulative += prob
            if rand < cumulative:
                selected_type = agent_type
                break
        
        agents.append(SimulatedAgent(
            agent_id=f"agent-{i:04d}",
            agent_type=selected_type,
            start_time=0,
            noise_std=0.05 if selected_type != AgentType.NOISY else 0.15,
        ))
    
    return agents


async def run_ablation_study(
    num_agents: int = 500,
    duration_seconds: int = 43200,  # 12 hours
    output_dir: Optional[Path] = None,
) -> Dict[str, BenchmarkResult]:
    """
    Ablation study: Remove each dimension and measure impact.
    """
    print(f"\n{'='*60}")
    print(f"Ablation Study: Dimension Contribution")
    print(f"{'='*60}")
    
    dimensions = [
        "policy_compliance",
        "resource_efficiency", 
        "output_quality",
        "security_posture",
        "collaboration_health",
    ]
    
    results = {}
    
    # Full model
    print("\nRunning full model...")
    full_result = await run_single_ablation(
        num_agents, duration_seconds, excluded_dimensions=[]
    )
    results["full_model"] = full_result
    
    # Remove each dimension
    for dim in dimensions:
        print(f"\nRunning without {dim}...")
        result = await run_single_ablation(
            num_agents, duration_seconds, excluded_dimensions=[dim]
        )
        results[f"without_{dim}"] = result
    
    # Print ablation results
    print("\n" + "="*60)
    print("ABLATION RESULTS")
    print("="*60)
    print(f"{'Configuration':<30} {'Precision':>12} {'FPR':>12}")
    print("-"*60)
    
    for config, result in results.items():
        print(f"{config:<30} {result.precision*100:>11.1f}% {result.false_positive_rate*100:>11.1f}%")
    
    # Save results
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "ablation_results.json", "w") as f:
            json.dump({name: result.to_dict() for name, result in results.items()}, f, indent=2)
    
    return results


async def run_single_ablation(
    num_agents: int,
    duration_seconds: int,
    excluded_dimensions: List[str],
) -> BenchmarkResult:
    """Run a single ablation configuration."""
    agents = create_agent_population(num_agents)
    engine = RewardEngineWrapper(revocation_threshold=300)
    
    result = BenchmarkResult(method=f"ablation_{'_'.join(excluded_dimensions) or 'none'}")
    update_interval = 30
    num_updates = duration_seconds // update_interval
    
    for update_idx in range(num_updates):
        current_time = update_idx * update_interval
        
        for agent in agents:
            signals = agent.get_signals(current_time)
            
            # Zero out excluded dimensions
            for dim in excluded_dimensions:
                if dim in signals:
                    signals[dim] = 0.5  # Neutral value
            
            engine.update(agent.agent_id, signals, current_time)
    
    # Compute metrics
    for agent in agents:
        should_revoke = agent.agent_type in (AgentType.MALICIOUS, AgentType.DEGRADING)
        was_revoked = engine.is_revoked(agent.agent_id)
        
        if should_revoke and was_revoked:
            result.true_positives += 1
        elif should_revoke and not was_revoked:
            result.false_negatives += 1
        elif not should_revoke and was_revoked:
            result.false_positives += 1
        else:
            result.true_negatives += 1
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run trust scoring benchmark")
    parser.add_argument("--agents", type=int, default=1000, help="Number of agents")
    parser.add_argument("--duration", type=int, default=86400, help="Duration in seconds")
    parser.add_argument("--output", type=str, default="results", help="Output directory")
    parser.add_argument("--ablation", action="store_true", help="Run ablation study")
    
    args = parser.parse_args()
    
    if args.ablation:
        asyncio.run(run_ablation_study(
            num_agents=args.agents // 2,
            duration_seconds=args.duration // 2,
            output_dir=Path(args.output),
        ))
    else:
        asyncio.run(run_benchmark(
            num_agents=args.agents,
            duration_seconds=args.duration,
            output_dir=Path(args.output),
        ))
