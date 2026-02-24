"""Tests for Trust Decay — Community Edition."""

import time
import pytest
from agentmesh.reward.trust_decay import (
    NetworkTrustEngine,
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
    """Interaction graph is a no-op in Community Edition."""

    def test_record_interaction_noop(self, engine):
        engine.record_interaction("a", "b")
        neighbors = engine.get_neighbors("a")
        assert neighbors == []

    def test_get_neighbors_empty(self, engine):
        assert engine.get_neighbors("a") == []


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
        """No propagation in Community Edition — only direct impact."""
        engine.set_score("a", 800.0)
        engine.set_score("b", 800.0)
        engine.record_interaction("a", "b")

        event = TrustEvent(agent_did="a", event_type="failure", severity_weight=1.0)
        deltas = engine.process_trust_event(event)

        # B should NOT be affected (no propagation)
        assert "b" not in deltas
        assert engine.get_score("b") == 800.0

    def test_propagation_depth_limit(self):
        """No propagation in Community Edition."""
        engine = NetworkTrustEngine(propagation_depth=1)
        engine.set_score("a", 800.0)
        engine.set_score("b", 800.0)
        engine.set_score("c", 800.0)

        event = TrustEvent(agent_did="a", event_type="failure", severity_weight=1.0)
        deltas = engine.process_trust_event(event)

        assert "b" not in deltas
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
    """Regime detection is a no-op in Community Edition."""

    def test_always_returns_none(self, engine):
        engine.record_action("a", "db_query")
        assert engine.detect_regime_change("a") is None

    def test_callback_never_fires(self, engine):
        alerts = []
        engine.on_regime_change(lambda a: alerts.append(a))
        engine.record_action("a", "action")
        engine.detect_regime_change("a")
        assert len(alerts) == 0


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
        assert report["edge_count"] == 0  # No interaction graph in Community Edition

    def test_alerts_list(self, engine):
        assert engine.alerts == []
