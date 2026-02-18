"""
Reward & Learning Engine (Layer 4)

Continuous behavioral feedback loop that scores every agent action
against a multi-dimensional governance rubric.
"""

from .engine import RewardEngine
from .scoring import TrustScore, RewardDimension, RewardSignal
from .learning import AdaptiveLearner, WeightOptimizer
from .anomaly import BehavioralAnomalyDetector, AnomalyReport
from .trust_decay import NetworkTrustEngine, TrustEvent, RegimeChangeAlert
from .distribution import (
    ContributionWeightedStrategy,
    DistributionResult,
    EqualSplitStrategy,
    HierarchicalStrategy,
    ParticipantInfo,
    RewardAllocation,
    RewardPool,
    RewardStrategy,
    TrustWeightedStrategy,
)
from .distributor import RewardDistributor

__all__ = [
    "RewardEngine",
    "TrustScore",
    "RewardDimension",
    "RewardSignal",
    "AdaptiveLearner",
    "WeightOptimizer",
    "BehavioralAnomalyDetector",
    "AnomalyReport",
    "NetworkTrustEngine",
    "TrustEvent",
    "RegimeChangeAlert",
    "ContributionWeightedStrategy",
    "DistributionResult",
    "EqualSplitStrategy",
    "HierarchicalStrategy",
    "ParticipantInfo",
    "RewardAllocation",
    "RewardPool",
    "RewardStrategy",
    "TrustWeightedStrategy",
    "RewardDistributor",
]
