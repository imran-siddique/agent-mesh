"""
Behavioral Anomaly Detection

Statistical anomaly detection for agent behavior.
Detects: frequency spikes, action drift, time-of-day anomalies,
rapid-fire patterns, and trust score degradation.

Usage:
    from agentmesh.reward.anomaly import BehavioralAnomalyDetector

    detector = BehavioralAnomalyDetector()
    detector.observe("did:mesh:agent1", "database_query", {"table": "users"})
    detector.observe("did:mesh:agent1", "database_query", {"table": "users"})
    # ... many more in rapid succession ...

    anomalies = detector.check("did:mesh:agent1")
    # [AnomalyReport(type="rapid_fire", severity="high", ...)]
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
import math


@dataclass
class AnomalyReport:
    """A detected behavioral anomaly."""
    agent_did: str
    anomaly_type: str  # rapid_fire, action_drift, frequency_spike, trust_degradation
    severity: str  # low, medium, high, critical
    description: str
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    details: Dict[str, Any] = field(default_factory=dict)
    recommended_action: str = ""


@dataclass
class AgentBehaviorProfile:
    """Statistical profile of an agent's normal behavior."""
    action_counts: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    action_timestamps: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    hourly_distribution: List[int] = field(default_factory=lambda: [0] * 24)
    total_observations: int = 0
    first_seen: Optional[float] = None
    last_seen: Optional[float] = None
    trust_scores: List[float] = field(default_factory=list)


class BehavioralAnomalyDetector:
    """
    Statistical anomaly detection for agent behavior.

    Detectors:
    1. Rapid-fire: >N actions in M seconds
    2. Action drift: Agent suddenly uses actions it never used before
    3. Frequency spike: Action rate >3σ above mean
    4. Trust degradation: Trust score drops significantly
    5. Time-of-day: Activity outside normal operating hours
    """

    def __init__(
        self,
        rapid_fire_threshold: int = 10,
        rapid_fire_window_seconds: int = 5,
        drift_threshold: float = 0.5,
        frequency_sigma: float = 3.0,
        trust_drop_threshold: float = 0.15,
        max_history_per_action: int = 1000,
    ):
        self.rapid_fire_threshold = rapid_fire_threshold
        self.rapid_fire_window = rapid_fire_window_seconds
        self.drift_threshold = drift_threshold
        self.frequency_sigma = frequency_sigma
        self.trust_drop_threshold = trust_drop_threshold
        self.max_history = max_history_per_action
        self._profiles: Dict[str, AgentBehaviorProfile] = {}
        self._anomalies: List[AnomalyReport] = []

    def observe(
        self,
        agent_did: str,
        action: str,
        context: Optional[Dict] = None,
        trust_score: Optional[float] = None,
    ) -> List[AnomalyReport]:
        """
        Record an agent action and check for anomalies.

        Returns list of anomalies detected (may be empty).
        """
        now = datetime.now(timezone.utc).timestamp()
        profile = self._get_or_create_profile(agent_did)

        # Update profile
        profile.action_counts[action] += 1
        profile.action_timestamps[action].append(now)
        # Trim old timestamps
        if len(profile.action_timestamps[action]) > self.max_history:
            profile.action_timestamps[action] = profile.action_timestamps[action][-self.max_history:]
        profile.total_observations += 1
        if profile.first_seen is None:
            profile.first_seen = now
        profile.last_seen = now

        hour = datetime.now(timezone.utc).hour
        profile.hourly_distribution[hour] += 1

        if trust_score is not None:
            profile.trust_scores.append(trust_score)

        # Run detectors
        new_anomalies = []
        new_anomalies.extend(self._check_rapid_fire(agent_did, action, profile))
        new_anomalies.extend(self._check_action_drift(agent_did, action, profile))
        new_anomalies.extend(self._check_frequency_spike(agent_did, action, profile))
        new_anomalies.extend(self._check_trust_degradation(agent_did, profile))
        new_anomalies.extend(self._check_time_anomaly(agent_did, profile, hour))

        self._anomalies.extend(new_anomalies)
        return new_anomalies

    def check(self, agent_did: str) -> List[AnomalyReport]:
        """Get all anomalies for an agent."""
        return [a for a in self._anomalies if a.agent_did == agent_did]

    def get_profile(self, agent_did: str) -> Optional[AgentBehaviorProfile]:
        """Get the behavioral profile for an agent."""
        return self._profiles.get(agent_did)

    def get_all_anomalies(
        self,
        severity: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[AnomalyReport]:
        """Get all anomalies, optionally filtered."""
        result = self._anomalies
        if severity:
            result = [a for a in result if a.severity == severity]
        if since:
            cutoff = since.isoformat()
            result = [a for a in result if a.detected_at >= cutoff]
        return result

    def clear_anomalies(self, agent_did: Optional[str] = None) -> int:
        """Clear anomaly records. Returns count cleared."""
        if agent_did:
            before = len(self._anomalies)
            self._anomalies = [a for a in self._anomalies if a.agent_did != agent_did]
            return before - len(self._anomalies)
        else:
            count = len(self._anomalies)
            self._anomalies.clear()
            return count

    def summary(self) -> Dict[str, Any]:
        """Get detection summary."""
        by_type = defaultdict(int)
        by_severity = defaultdict(int)
        for a in self._anomalies:
            by_type[a.anomaly_type] += 1
            by_severity[a.severity] += 1

        return {
            "agents_tracked": len(self._profiles),
            "total_anomalies": len(self._anomalies),
            "by_type": dict(by_type),
            "by_severity": dict(by_severity),
        }

    # ── Internal detectors ────────────────────────────────────

    def _get_or_create_profile(self, agent_did: str) -> AgentBehaviorProfile:
        if agent_did not in self._profiles:
            self._profiles[agent_did] = AgentBehaviorProfile()
        return self._profiles[agent_did]

    def _check_rapid_fire(
        self, agent_did: str, action: str, profile: AgentBehaviorProfile
    ) -> List[AnomalyReport]:
        """Detect rapid-fire: too many actions in a short window."""
        timestamps = profile.action_timestamps[action]
        if len(timestamps) < self.rapid_fire_threshold:
            return []

        recent = timestamps[-self.rapid_fire_threshold:]
        window = recent[-1] - recent[0]

        if window <= self.rapid_fire_window:
            return [AnomalyReport(
                agent_did=agent_did,
                anomaly_type="rapid_fire",
                severity="high",
                description=(
                    f"Agent fired {self.rapid_fire_threshold} '{action}' actions "
                    f"in {window:.1f}s (threshold: {self.rapid_fire_window}s)"
                ),
                details={"action": action, "count": self.rapid_fire_threshold, "window_seconds": round(window, 2)},
                recommended_action="Apply rate limiting or investigate for compromised credentials",
            )]
        return []

    def _check_action_drift(
        self, agent_did: str, action: str, profile: AgentBehaviorProfile
    ) -> List[AnomalyReport]:
        """Detect action drift: agent uses a new action after an established baseline."""
        if profile.total_observations < 50:
            return []  # Need baseline first

        # If this action has only been seen 1-2 times and there are many total observations
        action_count = profile.action_counts[action]
        if action_count <= 2 and profile.total_observations > 50:
            known_actions = {a for a, c in profile.action_counts.items() if c > 5}
            if action not in known_actions and len(known_actions) > 0:
                return [AnomalyReport(
                    agent_did=agent_did,
                    anomaly_type="action_drift",
                    severity="medium",
                    description=(
                        f"Agent used new action '{action}' after {profile.total_observations} observations. "
                        f"Known actions: {', '.join(sorted(known_actions))}"
                    ),
                    details={"new_action": action, "known_actions": sorted(known_actions)},
                    recommended_action="Verify agent configuration hasn't been modified",
                )]
        return []

    def _check_frequency_spike(
        self, agent_did: str, action: str, profile: AgentBehaviorProfile
    ) -> List[AnomalyReport]:
        """Detect frequency spike: action rate significantly above historical mean."""
        timestamps = profile.action_timestamps[action]
        if len(timestamps) < 20:
            return []  # Need enough data

        # Calculate intervals between actions
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        if not intervals:
            return []

        mean_interval = sum(intervals) / len(intervals)
        if mean_interval == 0:
            return []

        # Standard deviation
        variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
        std = math.sqrt(variance) if variance > 0 else 0

        # Check if the latest interval is suspiciously short
        latest_interval = intervals[-1]
        if std > 0 and latest_interval < mean_interval - (self.frequency_sigma * std):
            return [AnomalyReport(
                agent_did=agent_did,
                anomaly_type="frequency_spike",
                severity="medium",
                description=(
                    f"Action '{action}' frequency spike: interval {latest_interval:.1f}s "
                    f"vs mean {mean_interval:.1f}s ± {std:.1f}s ({self.frequency_sigma}σ threshold)"
                ),
                details={
                    "action": action,
                    "latest_interval": round(latest_interval, 2),
                    "mean_interval": round(mean_interval, 2),
                    "std_interval": round(std, 2),
                },
                recommended_action="Monitor for sustained spike; consider adaptive rate limiting",
            )]
        return []

    def _check_trust_degradation(
        self, agent_did: str, profile: AgentBehaviorProfile
    ) -> List[AnomalyReport]:
        """Detect trust score degradation over time."""
        scores = profile.trust_scores
        if len(scores) < 5:
            return []

        # Compare latest 3 scores to earlier average
        recent_avg = sum(scores[-3:]) / 3
        earlier_avg = sum(scores[:-3]) / len(scores[:-3])

        drop = earlier_avg - recent_avg
        if drop >= self.trust_drop_threshold:
            return [AnomalyReport(
                agent_did=agent_did,
                anomaly_type="trust_degradation",
                severity="high",
                description=(
                    f"Trust score dropped by {drop:.2f} "
                    f"(from {earlier_avg:.2f} to {recent_avg:.2f})"
                ),
                details={
                    "earlier_avg": round(earlier_avg, 3),
                    "recent_avg": round(recent_avg, 3),
                    "drop": round(drop, 3),
                },
                recommended_action="Review recent agent actions and consider restricting capabilities",
            )]
        return []

    def _check_time_anomaly(
        self, agent_did: str, profile: AgentBehaviorProfile, current_hour: int
    ) -> List[AnomalyReport]:
        """Detect activity outside normal operating hours."""
        total = sum(profile.hourly_distribution)
        if total < 100:
            return []  # Need baseline

        hour_pct = profile.hourly_distribution[current_hour] / total
        # If this hour normally has <1% of activity but agent is active now
        if hour_pct < 0.01 and total > 200:
            return [AnomalyReport(
                agent_did=agent_did,
                anomaly_type="time_anomaly",
                severity="low",
                description=(
                    f"Activity at hour {current_hour}:00 UTC is unusual "
                    f"({hour_pct*100:.1f}% of historical activity)"
                ),
                details={"hour": current_hour, "hour_pct": round(hour_pct, 4)},
                recommended_action="Verify if this is expected scheduled maintenance or drift",
            )]
        return []
