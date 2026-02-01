"""
Continuous Risk Scoring

Updates trust score every ≤30s based on agent behavior.
Score visible in dashboard; configurable alert thresholds.
"""

from datetime import datetime, timedelta
from typing import Optional, Literal
from pydantic import BaseModel, Field
from dataclasses import dataclass, field


@dataclass
class RiskSignal:
    """A single risk signal contributing to the score."""
    
    signal_type: str
    severity: Literal["critical", "high", "medium", "low", "info"]
    value: float  # 0.0 to 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: Optional[str] = None
    details: Optional[str] = None
    
    @property
    def weight(self) -> float:
        """Get weight based on severity."""
        weights = {
            "critical": 1.0,
            "high": 0.75,
            "medium": 0.5,
            "low": 0.25,
            "info": 0.1,
        }
        return weights.get(self.severity, 0.1)


class RiskScore(BaseModel):
    """
    Comprehensive risk score for an agent.
    
    Score ranges from 0 (highest risk) to 1000 (lowest risk).
    Inverted from trust score for clarity: lower = more risky.
    """
    
    agent_did: str
    
    # Overall score (0-1000, higher = safer)
    total_score: int = Field(default=500, ge=0, le=1000)
    risk_level: Literal["critical", "high", "medium", "low", "minimal"] = "medium"
    
    # Component scores (0-100 each)
    identity_score: int = Field(default=50, ge=0, le=100)
    behavior_score: int = Field(default=50, ge=0, le=100)
    network_score: int = Field(default=50, ge=0, le=100)
    compliance_score: int = Field(default=50, ge=0, le=100)
    
    # Signals
    active_signals: int = Field(default=0)
    critical_signals: int = Field(default=0)
    
    # Timestamps
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    next_update_at: datetime = Field(default_factory=datetime.utcnow)
    
    @classmethod
    def get_risk_level(cls, score: int) -> str:
        """Convert score to risk level."""
        if score >= 800:
            return "minimal"
        elif score >= 600:
            return "low"
        elif score >= 400:
            return "medium"
        elif score >= 200:
            return "high"
        else:
            return "critical"
    
    def update(
        self,
        identity: int,
        behavior: int,
        network: int,
        compliance: int,
        active_signals: int = 0,
        critical_signals: int = 0,
    ) -> None:
        """Update component scores and recalculate total."""
        self.identity_score = max(0, min(100, identity))
        self.behavior_score = max(0, min(100, behavior))
        self.network_score = max(0, min(100, network))
        self.compliance_score = max(0, min(100, compliance))
        
        # Weighted total (behavior and compliance weighted higher)
        self.total_score = int(
            self.identity_score * 2 +
            self.behavior_score * 3 +
            self.network_score * 2 +
            self.compliance_score * 3
        )  # Max: 1000
        
        self.risk_level = self.get_risk_level(self.total_score)
        self.active_signals = active_signals
        self.critical_signals = critical_signals
        self.calculated_at = datetime.utcnow()
        self.next_update_at = datetime.utcnow() + timedelta(seconds=30)


class RiskScorer:
    """
    Continuous risk scoring engine.
    
    Updates trust score every ≤30s based on:
    - Identity verification status
    - Behavioral patterns
    - Network activity
    - Compliance violations
    """
    
    UPDATE_INTERVAL = 30  # seconds
    
    # Alert thresholds
    CRITICAL_THRESHOLD = 200
    HIGH_THRESHOLD = 400
    ALERT_THRESHOLD = 600
    
    def __init__(self):
        self._scores: dict[str, RiskScore] = {}
        self._signals: dict[str, list[RiskSignal]] = {}  # agent_did -> signals
        self._alert_callbacks: list[callable] = []
    
    def get_score(self, agent_did: str) -> RiskScore:
        """Get current risk score for an agent."""
        if agent_did not in self._scores:
            self._scores[agent_did] = RiskScore(agent_did=agent_did)
        return self._scores[agent_did]
    
    def add_signal(self, agent_did: str, signal: RiskSignal) -> None:
        """Add a risk signal for an agent."""
        if agent_did not in self._signals:
            self._signals[agent_did] = []
        
        self._signals[agent_did].append(signal)
        
        # Trigger immediate recalculation for critical signals
        if signal.severity == "critical":
            self.recalculate(agent_did)
    
    def recalculate(self, agent_did: str) -> RiskScore:
        """
        Recalculate risk score based on current signals.
        
        This is called every ≤30s or immediately on critical signals.
        """
        score = self.get_score(agent_did)
        signals = self._signals.get(agent_did, [])
        
        # Filter to recent signals (last 24 hours)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_signals = [s for s in signals if s.timestamp > cutoff]
        
        # Calculate component scores
        identity_score = self._calculate_identity_score(recent_signals)
        behavior_score = self._calculate_behavior_score(recent_signals)
        network_score = self._calculate_network_score(recent_signals)
        compliance_score = self._calculate_compliance_score(recent_signals)
        
        # Count signals
        active = len(recent_signals)
        critical = len([s for s in recent_signals if s.severity == "critical"])
        
        # Update score
        old_level = score.risk_level
        score.update(
            identity=identity_score,
            behavior=behavior_score,
            network=network_score,
            compliance=compliance_score,
            active_signals=active,
            critical_signals=critical,
        )
        
        # Check for alerts
        self._check_alerts(agent_did, score, old_level)
        
        return score
    
    def _calculate_identity_score(self, signals: list[RiskSignal]) -> int:
        """Calculate identity component score."""
        base = 80  # Start at 80
        
        for signal in signals:
            if signal.signal_type.startswith("identity."):
                base -= int(signal.value * signal.weight * 20)
        
        return max(0, min(100, base))
    
    def _calculate_behavior_score(self, signals: list[RiskSignal]) -> int:
        """Calculate behavior component score."""
        base = 70
        
        for signal in signals:
            if signal.signal_type.startswith("behavior."):
                base -= int(signal.value * signal.weight * 25)
        
        return max(0, min(100, base))
    
    def _calculate_network_score(self, signals: list[RiskSignal]) -> int:
        """Calculate network component score."""
        base = 75
        
        for signal in signals:
            if signal.signal_type.startswith("network."):
                base -= int(signal.value * signal.weight * 20)
        
        return max(0, min(100, base))
    
    def _calculate_compliance_score(self, signals: list[RiskSignal]) -> int:
        """Calculate compliance component score."""
        base = 85  # Start higher - compliance is important
        
        for signal in signals:
            if signal.signal_type.startswith("compliance."):
                base -= int(signal.value * signal.weight * 30)
        
        return max(0, min(100, base))
    
    def _check_alerts(
        self,
        agent_did: str,
        score: RiskScore,
        old_level: str,
    ) -> None:
        """Check if alerts should be triggered."""
        # Alert on level change
        if score.risk_level != old_level:
            for callback in self._alert_callbacks:
                try:
                    callback({
                        "type": "risk_level_change",
                        "agent_did": agent_did,
                        "old_level": old_level,
                        "new_level": score.risk_level,
                        "score": score.total_score,
                    })
                except Exception:
                    pass
        
        # Alert on threshold breach
        if score.total_score < self.CRITICAL_THRESHOLD:
            for callback in self._alert_callbacks:
                try:
                    callback({
                        "type": "critical_risk",
                        "agent_did": agent_did,
                        "score": score.total_score,
                        "action": "immediate_review_required",
                    })
                except Exception:
                    pass
    
    def on_alert(self, callback: callable) -> None:
        """Register an alert callback."""
        self._alert_callbacks.append(callback)
    
    def get_high_risk_agents(self, threshold: Optional[int] = None) -> list[RiskScore]:
        """Get all agents above risk threshold."""
        thresh = threshold or self.HIGH_THRESHOLD
        return [
            score for score in self._scores.values()
            if score.total_score < thresh
        ]
    
    def clear_signals(self, agent_did: str) -> None:
        """Clear all signals for an agent (e.g., after remediation)."""
        if agent_did in self._signals:
            self._signals[agent_did] = []
        self.recalculate(agent_did)
