"""Tests for Behavioral Trust Decay with Network Effects."""

import time
import pytest
from agentmesh.reward.trust_decay import (
    InteractionEdge,
    NetworkTrustEngine,
    RegimeChangeAlert,
    TrustEvent,
)


@pytest.fixture
def engine():
    return NetworkTrustEngine()


# =============================================================================
# Basic score management
# =============================================================================


class TestScoreManagement:
    def test_default_score(self, engine):
        assert engine.get_score("did:agent:1") == 500.0

    def test_set_score(self, engine):
        engine.set_score("did:agent:1", 800.0)
        assert engine.get_score("did:agent:1") == 800.0

    def test_score_clamped(self, engine):
        engine.set_score("a", 2000.0)
        assert engine.get_score("a") == 1000.0
        engine.set_score("a", -100.0)
        assert engine.get_score("a") == 0.0

    def test_positive_signal(self, engine):
        engine.set_score("a", 500.0)
        engine.record_positive_signal("a", bonus=10.0)
        assert engine.get_score("a") == 510.0


# =============================================================================
# Interaction graph
# =============================================================================


class TestInteractionGraph:
    def test_record_interaction(self, engine):
        engine.record_interaction("a", "b")
        engine.record_interaction("a", "b")
        neighbors = engine.get_neighbors("a")
        assert len(neighbors) == 1
        peer, weight = neighbors[0]
        assert peer == "b"
        assert weight == 0.02  # 2/100

    def test_bidirectional_neighbors(self, engine):
        engine.record_interaction("a", "b")
        assert len(engine.get_neighbors("a")) == 1
        assert len(engine.get_neighbors("b")) == 1


# =============================================================================
# Trust event processing
# =============================================================================


class TestTrustEvents:
    def test_direct_impact(self, engine):
        engine.set_score("a", 800.0)
        event = TrustEvent(agent_did="a", event_type="violation", severity_weight=0.5)
        deltas = engine.process_trust_event(event)
        assert deltas["a"] == -50.0
        assert engine.get_score("a") == 750.0

    def test_critical_event(self, engine):
        engine.set_score("a", 500.0)
        event = TrustEvent(agent_did="a", event_type="breach", severity_weight=1.0)
        deltas = engine.process_trust_event(event)
        assert deltas["a"] == -100.0
        assert engine.get_score("a") == 400.0

    def test_propagation_to_neighbor(self, engine):
        engine.set_score("a", 800.0)
        engine.set_score("b", 800.0)
        # 50 interactions → weight = 0.5
        for _ in range(50):
            engine.record_interaction("a", "b")

        event = TrustEvent(agent_did="a", event_type="failure", severity_weight=1.0)
        deltas = engine.process_trust_event(event)

        # B should also be affected
        assert "b" in deltas
        assert deltas["b"] < 0
        assert engine.get_score("b") < 800.0

    def test_propagation_depth_limit(self):
        engine = NetworkTrustEngine(propagation_depth=1)
        engine.set_score("a", 800.0)
        engine.set_score("b", 800.0)
        engine.set_score("c", 800.0)
        for _ in range(100):
            engine.record_interaction("a", "b")
            engine.record_interaction("b", "c")

        event = TrustEvent(agent_did="a", event_type="failure", severity_weight=1.0)
        deltas = engine.process_trust_event(event)

        # B affected (depth 0), C should NOT be affected (depth 1 exceeds limit)
        assert "b" in deltas
        assert "c" not in deltas

    def test_no_propagation_without_edges(self, engine):
        engine.set_score("a", 800.0)
        engine.set_score("b", 800.0)
        event = TrustEvent(agent_did="a", event_type="failure", severity_weight=1.0)
        deltas = engine.process_trust_event(event)
        assert "b" not in deltas
        assert engine.get_score("b") == 800.0

    def test_score_change_callback(self, engine):
        events_received = []
        engine.on_score_change(lambda d: events_received.append(d))
        engine.set_score("a", 800.0)
        event = TrustEvent(agent_did="a", event_type="failure", severity_weight=0.5)
        engine.process_trust_event(event)
        assert len(events_received) == 1


# =============================================================================
# Temporal decay
# =============================================================================


class TestTemporalDecay:
    def test_decay_without_positive_signals(self, engine):
        engine.set_score("a", 800.0)
        # Simulate 2 hours without positive signals
        now = time.time()
        engine._last_positive["a"] = now - 7200  # 2 hours ago
        deltas = engine.apply_temporal_decay(now=now)
        assert "a" in deltas
        assert deltas["a"] < 0
        assert engine.get_score("a") < 800.0

    def test_no_decay_with_recent_positive(self, engine):
        engine.set_score("a", 800.0)
        now = time.time()
        engine.record_positive_signal("a")  # Just now
        deltas = engine.apply_temporal_decay(now=now)
        # Score should be 805 (500 default + bonus) — no decay
        assert deltas.get("a", 0) == 0 or abs(deltas.get("a", 0)) < 0.01

    def test_decay_floor(self, engine):
        engine.set_score("a", 150.0)
        now = time.time()
        engine._last_positive["a"] = now - 360000  # 100 hours ago
        engine.apply_temporal_decay(now=now)
        # Should not go below 100 from decay alone
        assert engine.get_score("a") >= 100.0


# =============================================================================
# Regime detection
# =============================================================================


class TestRegimeDetection:
    def _populate_baseline(self, engine, agent_did, now):
        """Add a baseline of mostly 'db_query' actions."""
        baseline_start = now - 86400 * 15  # 15 days ago
        for i in range(100):
            t = baseline_start + i * 1000
            engine._action_history[agent_did].append((t, "db_query"))
        for i in range(10):
            t = baseline_start + 100000 + i * 1000
            engine._action_history[agent_did].append((t, "shell"))

    def test_no_alert_with_stable_behavior(self, engine):
        now = time.time()
        self._populate_baseline(engine, "a", now)
        # Recent actions match baseline
        for i in range(10):
            engine._action_history["a"].append((now - 100 + i * 10, "db_query"))
        alert = engine.detect_regime_change("a", now=now)
        assert alert is None

    def test_alert_on_behavior_shift(self, engine):
        now = time.time()
        self._populate_baseline(engine, "a", now)
        # Recent actions: completely different
        for i in range(20):
            engine._action_history["a"].append((now - 100 + i * 5, "privilege_escalation"))
        alert = engine.detect_regime_change("a", now=now)
        assert alert is not None
        assert isinstance(alert, RegimeChangeAlert)
        assert alert.kl_divergence > engine.regime_threshold

    def test_insufficient_data_returns_none(self, engine):
        # Only 3 actions — not enough
        for i in range(3):
            engine.record_action("a", "db_query")
        assert engine.detect_regime_change("a") is None

    def test_regime_change_callback(self, engine):
        alerts = []
        engine.on_regime_change(lambda a: alerts.append(a))
        now = time.time()
        self._populate_baseline(engine, "a", now)
        for i in range(20):
            engine._action_history["a"].append((now - 100 + i * 5, "code_execution"))
        engine.detect_regime_change("a", now=now)
        assert len(alerts) == 1


# =============================================================================
# Health report & queries
# =============================================================================


class TestQueries:
    def test_agent_count(self, engine):
        assert engine.agent_count == 0
        engine.set_score("a", 500)
        engine.set_score("b", 600)
        assert engine.agent_count == 2

    def test_health_report(self, engine):
        engine.set_score("a", 700)
        engine.record_interaction("a", "b")
        report = engine.get_health_report()
        assert report["agent_count"] >= 1
        assert report["edge_count"] == 1

    def test_alerts_list(self, engine):
        assert engine.alerts == []


# =============================================================================
# InteractionEdge
# =============================================================================


class TestInteractionEdge:
    def test_weight_saturates(self):
        edge = InteractionEdge(from_did="a", to_did="b", interaction_count=200)
        assert edge.weight == 1.0

    def test_weight_linear(self):
        edge = InteractionEdge(from_did="a", to_did="b", interaction_count=50)
        assert edge.weight == 0.5
