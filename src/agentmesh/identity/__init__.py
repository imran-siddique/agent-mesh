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
from .revocation import RevocationList, RevocationEntry
from .rotation import KeyRotationManager
from .jwk import to_jwk, from_jwk, to_jwks, from_jwks
from .mtls import MTLSConfig, MTLSIdentityVerifier

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
    "RevocationList",
    "RevocationEntry",
    "KeyRotationManager",
    "to_jwk",
    "from_jwk",
    "to_jwks",
    "from_jwks",
    "MTLSConfig",
    "MTLSIdentityVerifier",
]
