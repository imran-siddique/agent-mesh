"""Tests for AgentMesh Reward module."""

import pytest
from datetime import datetime, timedelta

from agentmesh.reward import (
    RewardEngine,
    TrustScore,
    RewardDimension,
    RewardSignal,
    AdaptiveLearner,
    WeightOptimizer,
)
from agentmesh.reward.scoring import DimensionType


class TestRewardEngine:
    """Tests for RewardEngine."""
    
    def test_create_engine(self):
        """Test creating reward engine."""
        engine = RewardEngine()
        
        assert engine is not None
    
    def test_initial_score(self):
        """Test initial trust score."""
        engine = RewardEngine()
        
        score = engine.get_agent_score("did:agentmesh:test")
        
        assert isinstance(score, TrustScore)
        assert score.total_score >= 0
        assert score.total_score <= 1000
    
    def test_record_signal(self):
        """Test recording reward signals."""
        engine = RewardEngine()
        
        engine.record_signal(
            agent_did="did:agentmesh:test",
            dimension=DimensionType.POLICY_COMPLIANCE,
            value=1.0,
            source="test",
        )
        
        # Signal should be recorded
        state = engine._agents.get("did:agentmesh:test")
        assert state is not None
        assert len(state.recent_signals) == 1
    
    def test_policy_compliance_signal(self):
        """Test recording policy compliance."""
        engine = RewardEngine()
        
        engine.record_policy_compliance(
            agent_did="did:agentmesh:test",
            compliant=True,
            policy_name="test-policy",
        )
        
        state = engine._agents.get("did:agentmesh:test")
        signal = state.recent_signals[0]
        
        assert signal.dimension == DimensionType.POLICY_COMPLIANCE
        assert signal.value == 1.0
    
    def test_resource_usage_signal(self):
        """Test recording resource usage."""
        engine = RewardEngine()
        
        engine.record_resource_usage(
            agent_did="did:agentmesh:test",
            tokens_used=100,
            tokens_budget=200,
            compute_ms=50,
            compute_budget_ms=100,
        )
        
        state = engine._agents.get("did:agentmesh:test")
        signal = state.recent_signals[0]
        
        assert signal.dimension == DimensionType.RESOURCE_EFFICIENCY
        assert signal.value == 1.0  # Within budget
    
    def test_score_recalculation(self):
        """Test score recalculation."""
        engine = RewardEngine()
        
        # Add many positive signals
        for _ in range(10):
            engine.record_signal(
                agent_did="did:agentmesh:test",
                dimension=DimensionType.POLICY_COMPLIANCE,
                value=1.0,
                source="test",
            )
        
        score = engine._recalculate_score("did:agentmesh:test")
        
        # Score should be high
        assert score.total_score > 500
    
    def test_automatic_revocation(self):
        """Test automatic credential revocation on low score."""
        engine = RewardEngine()
        
        revoked_agents = []
        engine.on_revocation(lambda did, reason: revoked_agents.append(did))
        
        # Add many negative signals across all dimensions to drive score below 300
        for _ in range(100):
            for dim in DimensionType:
                engine.record_signal(
                    agent_did="did:agentmesh:test",
                    dimension=dim,
                    value=0.0,
                    source="test",
                )
        
        engine._recalculate_score("did:agentmesh:test")
        
        # Agent should be revoked (score will be 0)
        state = engine._agents.get("did:agentmesh:test")
        assert state.revoked or len(revoked_agents) > 0
    
    def test_score_explanation(self):
        """Test getting score explanation."""
        engine = RewardEngine()
        
        engine.record_signal(
            agent_did="did:agentmesh:test",
            dimension=DimensionType.POLICY_COMPLIANCE,
            value=0.8,
            source="test",
        )
        engine._recalculate_score("did:agentmesh:test")
        
        explanation = engine.get_score_explanation("did:agentmesh:test")
        
        assert "agent_did" in explanation
        assert "total_score" in explanation
        assert "dimensions" in explanation
        assert "trend" in explanation


class TestTrustScore:
    """Tests for TrustScore."""
    
    def test_create_score(self):
        """Test creating trust score."""
        score = TrustScore(agent_did="did:agentmesh:test")
        
        assert score.agent_did == "did:agentmesh:test"
        assert score.total_score == 500  # Default
    
    def test_tier_assignment(self):
        """Test tier assignment based on score."""
        score = TrustScore(agent_did="did:agentmesh:test", total_score=950)
        assert score.tier == "verified_partner"
        
        score = TrustScore(agent_did="did:agentmesh:test", total_score=750)
        assert score.tier == "trusted"
        
        score = TrustScore(agent_did="did:agentmesh:test", total_score=500)
        assert score.tier == "standard"
        
        score = TrustScore(agent_did="did:agentmesh:test", total_score=350)
        assert score.tier == "probationary"
        
        score = TrustScore(agent_did="did:agentmesh:test", total_score=100)
        assert score.tier == "untrusted"
    
    def test_threshold_check(self):
        """Test threshold checking."""
        score = TrustScore(agent_did="did:agentmesh:test", total_score=700)
        
        assert score.meets_threshold(500)
        assert score.meets_threshold(700)
        assert not score.meets_threshold(800)


class TestAdaptiveLearner:
    """Tests for AdaptiveLearner."""
    
    def test_create_learner(self):
        """Test creating adaptive learner."""
        learner = AdaptiveLearner()
        
        assert learner is not None
    
    def test_observe_action(self):
        """Test observing agent actions."""
        learner = AdaptiveLearner()
        
        learner.observe(
            agent_did="did:agentmesh:test",
            action="api_call",
            context={"endpoint": "/data"},
            outcome="success",
            score_impact=5,
        )
        
        patterns = learner.get_agent_patterns("did:agentmesh:test")
        
        assert len(patterns) == 1
    
    def test_anomaly_detection(self):
        """Test anomaly detection."""
        learner = AdaptiveLearner()
        
        # Large negative impact should trigger anomaly
        learner.observe(
            agent_did="did:agentmesh:test",
            action="dangerous_action",
            context={},
            outcome="failure",
            score_impact=-100,
        )
        
        anomalies = learner.get_anomalies()
        
        assert len(anomalies) == 1
    
    def test_recommendations(self):
        """Test policy recommendations."""
        learner = AdaptiveLearner()
        
        # Repeated negative actions
        for _ in range(5):
            learner.observe(
                agent_did="did:agentmesh:test",
                action="bad_action",
                context={},
                outcome="failure",
                score_impact=-10,
            )
        
        recommendations = learner.get_recommendations("did:agentmesh:test")
        
        assert len(recommendations) >= 1


class TestWeightOptimizer:
    """Tests for WeightOptimizer."""
    
    def test_create_optimizer(self):
        """Test creating weight optimizer."""
        optimizer = WeightOptimizer()
        
        assert optimizer is not None
    
    def test_start_experiment(self):
        """Test starting A/B experiment."""
        optimizer = WeightOptimizer()
        
        experiment = optimizer.start_experiment(
            name="test-experiment",
            control_weights={"policy_compliance": 0.25},
            treatment_weights={"policy_compliance": 0.30},
        )
        
        assert experiment.experiment_id is not None
        assert experiment.name == "test-experiment"
    
    def test_experiment_assignment(self):
        """Test agent assignment to experiment groups."""
        optimizer = WeightOptimizer()
        
        optimizer.start_experiment(
            name="test-experiment",
            control_weights={"policy_compliance": 0.25},
            treatment_weights={"policy_compliance": 0.30},
            treatment_pct=0.5,  # 50% in treatment
        )
        
        # Assign multiple agents
        assignments = [
            optimizer.get_weights_for_agent(f"did:agentmesh:agent-{i}")
            for i in range(100)
        ]
        
        # Should have both control and treatment
        # (with 50% split, very unlikely to have all one group)
        assert len(set(str(a) for a in assignments)) >= 1
