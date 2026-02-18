"""
Identity & Zero-Trust Core (Layer 1)

First-class agent identity with:
- Cryptographically bound identities
- Human sponsor accountability
- Ephemeral credentials (15-min TTL)
- SPIFFE/SVID workload identity
"""

from .agent_id import AgentIdentity, AgentDID
from .credentials import Credential, CredentialManager
from .delegation import DelegationChain, DelegationLink, UserContext
from .sponsor import HumanSponsor
from .risk import RiskScorer, RiskScore
from .spiffe import SPIFFEIdentity, SVID
from .namespace import AgentNamespace, NamespaceRule
from .namespace_manager import NamespaceManager

__all__ = [
    "AgentIdentity",
    "AgentDID",
    "Credential",
    "CredentialManager",
    "DelegationChain",
    "DelegationLink",
    "UserContext",
    "HumanSponsor",
    "RiskScorer",
    "RiskScore",
    "SPIFFEIdentity",
    "SVID",
    "AgentNamespace",
    "NamespaceRule",
    "NamespaceManager",
]
