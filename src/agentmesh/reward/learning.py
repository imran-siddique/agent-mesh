"""
Adaptive Learning

The platform's ability to learn and adapt from agent behavior.
Supports tunable weights with A/B testing.
"""

from datetime import datetime, timedelta
from typing import Optional, Callable
from pydantic import BaseModel, Field
from dataclasses import dataclass
import random


@dataclass
class WeightExperiment:
    """An A/B test experiment for reward weights."""
    
    experiment_id: str
    name: str
    
    # Control weights (current production)
    control_weights: dict[str, float]
    
    # Treatment weights (being tested)
    treatment_weights: dict[str, float]
    
    # Split
    treatment_percentage: float = 0.1  # 10% in treatment
    
    # Assignment
    control_agents: set = None
    treatment_agents: set = None
    
    # Results
    control_scores: list = None
    treatment_scores: list = None
    
    # Status
    started_at: datetime = None
    ended_at: datetime = None
    
    def __post_init__(self):
        self.control_agents = set()
        self.treatment_agents = set()
        self.control_scores = []
        self.treatment_scores = []
        self.started_at = datetime.utcnow()
    
    def assign_agent(self, agent_did: str) -> str:
        """Assign an agent to control or treatment."""
        if agent_did in self.control_agents:
            return "control"
        if agent_did in self.treatment_agents:
            return "treatment"
        
        # Random assignment
        if random.random() < self.treatment_percentage:
            self.treatment_agents.add(agent_did)
            return "treatment"
        else:
            self.control_agents.add(agent_did)
            return "control"
    
    def record_score(self, agent_did: str, score: int) -> None:
        """Record a score observation."""
        if agent_did in self.treatment_agents:
            self.treatment_scores.append(score)
        else:
            self.control_scores.append(score)
    
    def get_results(self) -> dict:
        """Get experiment results."""
        control_avg = (
            sum(self.control_scores) / len(self.control_scores)
            if self.control_scores else 0
        )
        treatment_avg = (
            sum(self.treatment_scores) / len(self.treatment_scores)
            if self.treatment_scores else 0
        )
        
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "control_count": len(self.control_agents),
            "treatment_count": len(self.treatment_agents),
            "control_avg_score": control_avg,
            "treatment_avg_score": treatment_avg,
            "lift": treatment_avg - control_avg,
            "lift_pct": ((treatment_avg - control_avg) / control_avg * 100) if control_avg else 0,
        }


class WeightOptimizer:
    """
    Optimizer for reward dimension weights.
    
    Supports:
    - A/B testing of weight configurations
    - Automatic weight tuning
    - Statistical significance testing
    """
    
    def __init__(self):
        self._experiments: dict[str, WeightExperiment] = {}
        self._active_experiment: Optional[str] = None
    
    def start_experiment(
        self,
        name: str,
        control_weights: dict[str, float],
        treatment_weights: dict[str, float],
        treatment_pct: float = 0.1,
    ) -> WeightExperiment:
        """Start a weight A/B test."""
        import uuid
        exp_id = f"exp_{uuid.uuid4().hex[:12]}"
        
        experiment = WeightExperiment(
            experiment_id=exp_id,
            name=name,
            control_weights=control_weights,
            treatment_weights=treatment_weights,
            treatment_percentage=treatment_pct,
        )
        
        self._experiments[exp_id] = experiment
        self._active_experiment = exp_id
        
        return experiment
    
    def get_weights_for_agent(self, agent_did: str) -> dict[str, float]:
        """Get the appropriate weights for an agent (considering experiments)."""
        if not self._active_experiment:
            return {}  # Use default
        
        experiment = self._experiments[self._active_experiment]
        group = experiment.assign_agent(agent_did)
        
        if group == "treatment":
            return experiment.treatment_weights
        else:
            return experiment.control_weights
    
    def record_observation(self, agent_did: str, score: int) -> None:
        """Record a score observation for active experiment."""
        if self._active_experiment:
            self._experiments[self._active_experiment].record_score(agent_did, score)
    
    def end_experiment(self, experiment_id: Optional[str] = None) -> dict:
        """End an experiment and get results."""
        exp_id = experiment_id or self._active_experiment
        if not exp_id or exp_id not in self._experiments:
            return {"error": "No experiment found"}
        
        experiment = self._experiments[exp_id]
        experiment.ended_at = datetime.utcnow()
        
        if exp_id == self._active_experiment:
            self._active_experiment = None
        
        return experiment.get_results()
    
    def should_adopt_treatment(self, experiment_id: str, min_lift_pct: float = 5.0) -> bool:
        """Check if treatment should be adopted."""
        if experiment_id not in self._experiments:
            return False
        
        results = self._experiments[experiment_id].get_results()
        
        # Check statistical significance (simplified)
        if results["control_count"] < 100 or results["treatment_count"] < 10:
            return False  # Not enough data
        
        return results["lift_pct"] >= min_lift_pct


class AdaptiveLearner:
    """
    Learns optimal policies from agent behavior.
    
    Features:
    - Behavioral pattern detection
    - Anomaly identification
    - Policy recommendation
    """
    
    def __init__(self):
        self._patterns: dict[str, list] = {}  # agent_did -> [patterns]
        self._anomalies: list = []
    
    def observe(
        self,
        agent_did: str,
        action: str,
        context: dict,
        outcome: str,
        score_impact: int,
    ) -> None:
        """Observe an agent action for learning."""
        if agent_did not in self._patterns:
            self._patterns[agent_did] = []
        
        observation = {
            "action": action,
            "context_keys": list(context.keys()),
            "outcome": outcome,
            "score_impact": score_impact,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        self._patterns[agent_did].append(observation)
        
        # Detect anomalies
        if score_impact < -50:  # Large negative impact
            self._anomalies.append({
                "agent_did": agent_did,
                "observation": observation,
                "type": "large_negative_impact",
            })
    
    def get_agent_patterns(self, agent_did: str) -> list:
        """Get learned patterns for an agent."""
        return self._patterns.get(agent_did, [])
    
    def get_recommendations(self, agent_did: str) -> list[str]:
        """Get policy recommendations based on patterns."""
        patterns = self._patterns.get(agent_did, [])
        
        if not patterns:
            return []
        
        recommendations = []
        
        # Analyze patterns
        negative_actions = [
            p["action"] for p in patterns
            if p["score_impact"] < 0
        ]
        
        # Count frequent negative actions
        action_counts = {}
        for action in negative_actions:
            action_counts[action] = action_counts.get(action, 0) + 1
        
        # Recommend blocking frequent negative actions
        for action, count in action_counts.items():
            if count >= 3:
                recommendations.append(
                    f"Consider blocking action '{action}' - caused {count} negative impacts"
                )
        
        return recommendations
    
    def get_anomalies(
        self,
        agent_did: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> list:
        """Get detected anomalies."""
        anomalies = self._anomalies
        
        if agent_did:
            anomalies = [a for a in anomalies if a["agent_did"] == agent_did]
        
        if since:
            anomalies = [
                a for a in anomalies
                if datetime.fromisoformat(a["observation"]["timestamp"]) >= since
            ]
        
        return anomalies
    
    def get_learning_summary(self) -> dict:
        """Get summary of learning state."""
        total_observations = sum(len(p) for p in self._patterns.values())
        
        return {
            "agents_tracked": len(self._patterns),
            "total_observations": total_observations,
            "anomalies_detected": len(self._anomalies),
            "patterns_per_agent": {
                agent: len(patterns)
                for agent, patterns in self._patterns.items()
            },
        }
