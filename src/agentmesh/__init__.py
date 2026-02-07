"""
AgentMesh - The Secure Nervous System for Cloud-Native Agent Ecosystems

Identity · Trust · Reward · Governance

AgentMesh is the platform built for the Governed Agent Mesh - the cloud-native,
multi-vendor network of AI agents that will define enterprise operations.

Version: 1.0.0-alpha
"""

__version__ = "1.0.0-alpha"

# Layer 1: Identity & Zero-Trust Core
from .identity import (
    AgentIdentity,
    AgentDID,
    Credential,
    CredentialManager,
    DelegationChain,
    DelegationLink,
    HumanSponsor,
    RiskScorer,
    RiskScore,
    SPIFFEIdentity,
    SVID,
)

# Layer 2: Trust & Protocol Bridge
from .trust import (
    TrustBridge,
    ProtocolBridge,
    TrustHandshake,
    HandshakeResult,
    CapabilityScope,
    CapabilityGrant,
    CapabilityRegistry,
)

# Layer 3: Governance & Compliance Plane
from .governance import (
    PolicyEngine,
    Policy,
    PolicyRule,
    PolicyDecision,
    ComplianceEngine,
    ComplianceFramework,
    ComplianceReport,
    AuditLog,
    AuditEntry,
    MerkleAuditChain,
    ShadowMode,
    ShadowResult,
)

# Layer 4: Reward & Learning Engine
from .reward import (
    RewardEngine,
    TrustScore,
    RewardDimension,
    RewardSignal,
    AdaptiveLearner,
    WeightOptimizer,
)

__all__ = [
    # Version
    "__version__",
    
    # Layer 1: Identity
    "AgentIdentity",
    "AgentDID",
    "Credential",
    "CredentialManager",
    "DelegationChain",
    "DelegationLink",
    "HumanSponsor",
    "RiskScorer",
    "RiskScore",
    "SPIFFEIdentity",
    "SVID",
    
    # Layer 2: Trust
    "TrustBridge",
    "ProtocolBridge",
    "TrustHandshake",
    "HandshakeResult",
    "CapabilityScope",
    "CapabilityGrant",
    "CapabilityRegistry",
    
    # Layer 3: Governance
    "PolicyEngine",
    "Policy",
    "PolicyRule",
    "PolicyDecision",
    "ComplianceEngine",
    "ComplianceFramework",
    "ComplianceReport",
    "AuditLog",
    "AuditEntry",
    "MerkleAuditChain",
    "ShadowMode",
    "ShadowResult",
    
    # Layer 4: Reward
    "RewardEngine",
    "TrustScore",
    "RewardDimension",
    "RewardSignal",
    "AdaptiveLearner",
    "WeightOptimizer",
]
