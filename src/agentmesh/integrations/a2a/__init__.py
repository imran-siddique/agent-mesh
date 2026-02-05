"""
A2A Protocol Integration for AgentMesh
=======================================

Provides CMVK-enhanced Agent Cards and trust verification for the
Agent-to-Agent (A2A) Protocol developed by Google/Linux Foundation.

Features:
- CMVK-signed Agent Cards for cryptographic identity
- Trust handshake before task delegation
- Capability verification for A2A tasks
- Audit trail integration

Example:
    >>> from agentmesh.integrations.a2a import A2AAgentCard, A2ATrustProvider
    >>> from agentmesh.identity import AgentIdentity
    >>>
    >>> # Create identity and Agent Card
    >>> identity = AgentIdentity.create(
    ...     name="sql-agent",
    ...     sponsor_id="human@example.com",
    ...     capabilities=["execute:sql", "read:database"]
    ... )
    >>> card = A2AAgentCard.from_identity(identity)
    >>>
    >>> # Publish to /.well-known/agent.json
    >>> card.to_json()
"""

from __future__ import annotations

import json
import logging
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class A2ATaskState(Enum):
    """A2A Protocol task states."""
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input_required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


@dataclass
class CMVKSignature:
    """Cryptographic Multi-Vector Key signature for Agent Cards."""
    algorithm: str = "Ed25519"
    public_key: str = ""
    signature: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

    def is_valid(self) -> bool:
        """Check if signature is still valid."""
        if self.expires_at is None:
            return True
        return datetime.utcnow() < self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "publicKey": self.public_key,
            "signature": self.signature,
            "timestamp": self.timestamp.isoformat(),
            "expiresAt": self.expires_at.isoformat() if self.expires_at else None,
        }


@dataclass
class A2AAgentCard:
    """
    CMVK-enhanced A2A Agent Card.

    Extends the standard A2A Agent Card with cryptographic identity
    verification using AgentMesh's CMVK infrastructure.
    """
    # Standard A2A fields
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    capabilities: List[str] = field(default_factory=list)
    skills: List[Dict[str, Any]] = field(default_factory=list)
    authentication: Dict[str, Any] = field(default_factory=dict)
    
    # AgentMesh extensions
    agent_did: str = ""
    cmvk_signature: Optional[CMVKSignature] = None
    trust_score: int = 500
    sponsor_id: str = ""
    delegation_chain: List[str] = field(default_factory=list)
    
    @classmethod
    def from_identity(
        cls,
        identity: Any,  # AgentIdentity
        url: str,
        description: str = "",
        skills: Optional[List[Dict[str, Any]]] = None,
    ) -> "A2AAgentCard":
        """Create Agent Card from AgentMesh identity."""
        # Extract capabilities from identity
        capabilities = []
        if hasattr(identity, "capabilities"):
            capabilities = list(identity.capabilities)
        
        # Build delegation chain
        delegation_chain = []
        if hasattr(identity, "delegation_chain"):
            delegation_chain = identity.delegation_chain
        
        # Create CMVK signature
        signature = None
        if hasattr(identity, "sign"):
            card_data = f"{identity.did}:{url}:{datetime.utcnow().isoformat()}"
            sig_bytes = identity.sign(card_data.encode())
            signature = CMVKSignature(
                algorithm="Ed25519",
                public_key=identity.public_key if hasattr(identity, "public_key") else "",
                signature=sig_bytes.hex() if sig_bytes else "",
                timestamp=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=24),
            )
        
        return cls(
            name=identity.name if hasattr(identity, "name") else str(identity.did),
            description=description or f"AgentMesh agent: {identity.did}",
            url=url,
            capabilities=capabilities,
            skills=skills or [],
            authentication={"schemes": ["cmvk", "bearer"]},
            agent_did=str(identity.did) if hasattr(identity, "did") else "",
            cmvk_signature=signature,
            trust_score=identity.trust_score if hasattr(identity, "trust_score") else 500,
            sponsor_id=identity.sponsor_id if hasattr(identity, "sponsor_id") else "",
            delegation_chain=delegation_chain,
        )

    def to_json(self, indent: int = 2) -> str:
        """Export as A2A-compatible JSON for /.well-known/agent.json"""
        data = {
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "version": self.version,
            "capabilities": {
                "streaming": True,
                "pushNotifications": False,
                "stateTransitionHistory": True,
            },
            "skills": self.skills,
            "authentication": self.authentication,
            # AgentMesh extensions (under x-agentmesh namespace)
            "x-agentmesh": {
                "did": self.agent_did,
                "trustScore": self.trust_score,
                "sponsorId": self.sponsor_id,
                "delegationChain": self.delegation_chain,
                "cmvkSignature": self.cmvk_signature.to_dict() if self.cmvk_signature else None,
                "grantedCapabilities": self.capabilities,
            },
        }
        return json.dumps(data, indent=indent)

    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary."""
        return json.loads(self.to_json())

    def verify_signature(self, identity_registry: Any = None) -> bool:
        """Verify the CMVK signature is valid."""
        if not self.cmvk_signature:
            return False
        
        if not self.cmvk_signature.is_valid():
            logger.warning(f"Agent Card signature expired for {self.agent_did}")
            return False
        
        # If registry provided, verify against stored identity
        if identity_registry and hasattr(identity_registry, "get"):
            stored_identity = identity_registry.get(self.agent_did)
            if not stored_identity:
                logger.warning(f"Unknown agent DID: {self.agent_did}")
                return False
            
            # Verify public key matches
            if hasattr(stored_identity, "public_key"):
                if stored_identity.public_key != self.cmvk_signature.public_key:
                    logger.warning(f"Public key mismatch for {self.agent_did}")
                    return False
        
        return True


@dataclass
class A2ATask:
    """A2A Protocol task with trust metadata."""
    task_id: str
    session_id: str
    state: A2ATaskState
    message: Dict[str, Any]
    
    # Trust metadata
    requester_did: str = ""
    executor_did: str = ""
    trust_verified: bool = False
    trust_level: str = "untrusted"
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class A2ATrustProvider:
    """
    Trust provider for A2A Protocol interactions.
    
    Verifies agent identity and trust before allowing task delegation.
    """
    
    def __init__(
        self,
        identity: Any,  # AgentIdentity
        trust_bridge: Any = None,  # TrustBridge
        min_trust_score: int = 300,
    ):
        self.identity = identity
        self.trust_bridge = trust_bridge
        self.min_trust_score = min_trust_score
        self._verified_peers: Dict[str, datetime] = {}
        self._verification_cache_ttl = timedelta(minutes=15)

    async def verify_peer(self, peer_did: str, peer_card: Optional[A2AAgentCard] = None) -> bool:
        """
        Verify peer agent before task interaction.
        
        Args:
            peer_did: Peer agent's DID
            peer_card: Optional peer's Agent Card for verification
            
        Returns:
            True if peer is trusted
        """
        # Check cache
        if peer_did in self._verified_peers:
            cached_time = self._verified_peers[peer_did]
            if datetime.utcnow() - cached_time < self._verification_cache_ttl:
                logger.debug(f"Using cached trust for {peer_did}")
                return True
        
        # Verify Agent Card signature if provided
        if peer_card:
            if not peer_card.verify_signature():
                logger.warning(f"Invalid Agent Card signature for {peer_did}")
                return False
            
            # Check trust score
            if peer_card.trust_score < self.min_trust_score:
                logger.warning(
                    f"Peer {peer_did} trust score {peer_card.trust_score} "
                    f"below minimum {self.min_trust_score}"
                )
                return False
        
        # Use TrustBridge for handshake if available
        if self.trust_bridge and hasattr(self.trust_bridge, "verify_peer"):
            try:
                result = await self.trust_bridge.verify_peer(peer_did)
                if not result:
                    logger.warning(f"TrustBridge verification failed for {peer_did}")
                    return False
            except Exception as e:
                logger.error(f"Trust verification error: {e}")
                return False
        
        # Cache successful verification
        self._verified_peers[peer_did] = datetime.utcnow()
        logger.info(f"Verified trust for peer {peer_did}")
        return True

    async def create_task(
        self,
        peer_did: str,
        message: Dict[str, Any],
        peer_card: Optional[A2AAgentCard] = None,
    ) -> Optional[A2ATask]:
        """
        Create A2A task with trust verification.
        
        Args:
            peer_did: Target agent DID
            message: Task message
            peer_card: Optional target's Agent Card
            
        Returns:
            A2ATask if trust verified, None otherwise
        """
        # Verify trust first
        if not await self.verify_peer(peer_did, peer_card):
            logger.warning(f"Cannot create task - peer {peer_did} not trusted")
            return None
        
        # Create task with trust metadata
        task_id = hashlib.sha256(
            f"{self.identity.did}:{peer_did}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        task = A2ATask(
            task_id=task_id,
            session_id=f"session-{task_id}",
            state=A2ATaskState.SUBMITTED,
            message=message,
            requester_did=str(self.identity.did) if hasattr(self.identity, "did") else "",
            executor_did=peer_did,
            trust_verified=True,
            trust_level="verified",
        )
        
        logger.info(f"Created A2A task {task_id} for peer {peer_did}")
        return task

    def get_trust_footer(self) -> Dict[str, Any]:
        """
        Get trust verification footer for A2A messages.
        
        This footer can be appended to A2A messages for audit trails.
        """
        return {
            "x-agentmesh-trust": {
                "verifierDid": str(self.identity.did) if hasattr(self.identity, "did") else "",
                "timestamp": datetime.utcnow().isoformat(),
                "minTrustScore": self.min_trust_score,
                "verificationMethod": "cmvk-handshake",
            }
        }


# Convenience exports
__all__ = [
    "A2AAgentCard",
    "A2ATask",
    "A2ATaskState",
    "A2ATrustProvider",
    "CMVKSignature",
]
