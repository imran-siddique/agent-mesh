"""
Shadow Mode

Simulate agent behavior against real policies without execution.
Shadow vs. production divergence target: <2% on replay dataset.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional, Any
from pydantic import BaseModel, Field
from dataclasses import dataclass
import uuid

if TYPE_CHECKING:
    from .policy import PolicyEngine


@dataclass
class SimulatedAction:
    """An action to simulate in shadow mode."""
    
    action_id: str
    agent_did: str
    action_type: str
    context: dict
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class ShadowResult(BaseModel):
    """Result of shadow mode evaluation."""
    
    action_id: str
    
    # Shadow evaluation
    shadow_allowed: bool
    shadow_action: str  # allow, deny, warn, etc.
    shadow_rule: Optional[str] = None
    
    # Production evaluation (if available)
    production_allowed: Optional[bool] = None
    production_action: Optional[str] = None
    production_rule: Optional[str] = None
    
    # Divergence
    diverged: bool = False
    divergence_reason: Optional[str] = None
    
    # Timing
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    shadow_latency_ms: Optional[float] = None
    production_latency_ms: Optional[float] = None


class ShadowSession(BaseModel):
    """A shadow mode evaluation session."""
    
    session_id: str = Field(default_factory=lambda: f"shadow_{uuid.uuid4().hex[:12]}")
    started_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Scope
    agent_dids: list[str] = Field(default_factory=list)
    policy_names: list[str] = Field(default_factory=list)
    
    # Results
    total_evaluated: int = 0
    total_diverged: int = 0
    divergence_rate: float = 0.0
    
    # Detailed results
    results: list[ShadowResult] = Field(default_factory=list)
    
    # Status
    active: bool = True
    ended_at: Optional[datetime] = None


class ShadowMode:
    """
    Shadow mode for policy testing.
    
    Run new policies in shadow mode before production:
    1. Load candidate policies
    2. Replay production traffic or simulate actions
    3. Compare shadow vs production decisions
    4. Report divergence
    
    Target: <2% divergence on replay dataset.
    """
    
    DIVERGENCE_TARGET = 0.02  # 2%
    
    def __init__(self, policy_engine: PolicyEngine):
        """
        Initialize shadow mode.
        
        Args:
            policy_engine: PolicyEngine to test in shadow mode
        """
        self.policy_engine = policy_engine
        self._sessions: dict[str, ShadowSession] = {}
        self._active_session: Optional[str] = None
    
    def start_session(
        self,
        agent_dids: Optional[list[str]] = None,
        policy_names: Optional[list[str]] = None,
    ) -> ShadowSession:
        """Start a new shadow evaluation session."""
        session = ShadowSession(
            agent_dids=agent_dids or [],
            policy_names=policy_names or [],
        )
        
        self._sessions[session.session_id] = session
        self._active_session = session.session_id
        
        return session
    
    def evaluate(
        self,
        action: SimulatedAction,
        production_decision: Optional[dict] = None,
    ) -> ShadowResult:
        """
        Evaluate an action in shadow mode.
        
        Args:
            action: The action to evaluate
            production_decision: Optional actual production decision to compare
            
        Returns:
            ShadowResult with comparison
        """
        start = datetime.utcnow()
        
        # Shadow evaluation
        shadow_decision = self.policy_engine.evaluate(
            agent_did=action.agent_did,
            context=action.context,
        )
        
        shadow_latency = (datetime.utcnow() - start).total_seconds() * 1000
        
        # Build result
        result = ShadowResult(
            action_id=action.action_id,
            shadow_allowed=shadow_decision.allowed,
            shadow_action=shadow_decision.action,
            shadow_rule=shadow_decision.matched_rule,
            shadow_latency_ms=shadow_latency,
        )
        
        # Compare with production if available
        if production_decision:
            result.production_allowed = production_decision.get("allowed")
            result.production_action = production_decision.get("action")
            result.production_rule = production_decision.get("matched_rule")
            result.production_latency_ms = production_decision.get("latency_ms")
            
            # Check for divergence
            if result.shadow_allowed != result.production_allowed:
                result.diverged = True
                result.divergence_reason = (
                    f"Shadow={result.shadow_action}, Production={result.production_action}"
                )
            elif result.shadow_action != result.production_action:
                result.diverged = True
                result.divergence_reason = f"Action mismatch: {result.shadow_action} vs {result.production_action}"
        
        # Record in session
        if self._active_session:
            session = self._sessions[self._active_session]
            session.results.append(result)
            session.total_evaluated += 1
            if result.diverged:
                session.total_diverged += 1
            session.divergence_rate = (
                session.total_diverged / session.total_evaluated
                if session.total_evaluated > 0 else 0.0
            )
        
        return result
    
    def replay_batch(
        self,
        actions: list[SimulatedAction],
        production_decisions: Optional[list[dict]] = None,
    ) -> list[ShadowResult]:
        """
        Replay a batch of actions in shadow mode.
        
        Args:
            actions: List of actions to replay
            production_decisions: Optional list of production decisions to compare
        """
        results = []
        
        for i, action in enumerate(actions):
            prod_decision = None
            if production_decisions and i < len(production_decisions):
                prod_decision = production_decisions[i]
            
            result = self.evaluate(action, prod_decision)
            results.append(result)
        
        return results
    
    def end_session(self, session_id: Optional[str] = None) -> ShadowSession:
        """End a shadow session and return summary."""
        sid = session_id or self._active_session
        if not sid or sid not in self._sessions:
            raise ValueError("No active session")
        
        session = self._sessions[sid]
        session.active = False
        session.ended_at = datetime.utcnow()
        
        if sid == self._active_session:
            self._active_session = None
        
        return session
    
    def get_session(self, session_id: str) -> Optional[ShadowSession]:
        """Get session by ID."""
        return self._sessions.get(session_id)
    
    def get_divergence_report(self, session_id: Optional[str] = None) -> dict[str, Any]:
        """Generate divergence report for a session."""
        sid = session_id or self._active_session
        if not sid or sid not in self._sessions:
            return {"error": "No session found"}
        
        session = self._sessions[sid]
        
        # Group divergences by reason
        divergence_reasons = {}
        for result in session.results:
            if result.diverged:
                reason = result.divergence_reason or "unknown"
                if reason not in divergence_reasons:
                    divergence_reasons[reason] = 0
                divergence_reasons[reason] += 1
        
        # Check if within target
        within_target = session.divergence_rate <= self.DIVERGENCE_TARGET
        
        return {
            "session_id": session.session_id,
            "total_evaluated": session.total_evaluated,
            "total_diverged": session.total_diverged,
            "divergence_rate": session.divergence_rate,
            "divergence_rate_pct": f"{session.divergence_rate * 100:.2f}%",
            "target_rate_pct": f"{self.DIVERGENCE_TARGET * 100:.2f}%",
            "within_target": within_target,
            "divergence_breakdown": divergence_reasons,
            "recommendation": (
                "Ready for production" if within_target
                else "Review divergent cases before production"
            ),
        }
    
    def is_ready_for_production(self, session_id: Optional[str] = None) -> bool:
        """Check if shadow session shows policy is ready for production."""
        report = self.get_divergence_report(session_id)
        return report.get("within_target", False)
