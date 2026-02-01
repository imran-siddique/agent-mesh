"""
Reward & Learning Engine (Layer 4)

Continuous behavioral feedback loop that scores every agent action
against a multi-dimensional governance rubric.
"""

from .engine import RewardEngine
from .scoring import TrustScore, RewardDimension, RewardSignal
from .learning import AdaptiveLearner, WeightOptimizer

__all__ = [
    "RewardEngine",
    "TrustScore",
    "RewardDimension",
    "RewardSignal",
    "AdaptiveLearner",
    "WeightOptimizer",
]
