"""
Trust Handshake

IATP-compatible trust handshakes for cross-agent and cross-cloud
communication. Handshake completes in <200ms.
"""

from datetime import datetime, timedelta
from typing import Optional, Literal
from pydantic import BaseModel, Field
import hashlib
import secrets
import asyncio
from agentmesh.identity.agent_id import AgentIdentity


class HandshakeChallenge(BaseModel):
    """Challenge issued during trust handshake."""
    
    challenge_id: str
    nonce: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    expires_in_seconds: int = 30
    
    @classmethod
    def generate(cls) -> "HandshakeChallenge":
        """Generate a new challenge."""
        return cls(
            challenge_id=f"challenge_{secrets.token_hex(8)}",
            nonce=secrets.token_hex(32),
        )
    
    def is_expired(self) -> bool:
        """Check if challenge has expired."""
        elapsed = (datetime.utcnow() - self.timestamp).total_seconds()
        return elapsed > self.expires_in_seconds


class HandshakeResponse(BaseModel):
    """Response to a handshake challenge."""
    
    challenge_id: str
    response_nonce: str
    
    # Agent attestation
    agent_did: str
    capabilities: list[str] = Field(default_factory=list)
    trust_score: int = Field(default=0, ge=0, le=1000)
    
    # Cryptographic proof
    signature: str  # Signature over challenge + response
    public_key: str  # For verification
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HandshakeResult(BaseModel):
    """Result of a trust handshake."""
    
    verified: bool
    peer_did: str
    peer_name: Optional[str] = None
    
    # Trust details
    trust_score: int = Field(default=0, ge=0, le=1000)
    trust_level: Literal["verified_partner", "trusted", "standard", "untrusted"] = "untrusted"
    
    # Capabilities
    capabilities: list[str] = Field(default_factory=list)
    
    # Timing
    handshake_started: datetime = Field(default_factory=datetime.utcnow)
    handshake_completed: Optional[datetime] = None
    latency_ms: Optional[int] = None
    
    # Rejection reason (if not verified)
    rejection_reason: Optional[str] = None
    
    @classmethod
    def success(
        cls,
        peer_did: str,
        trust_score: int,
        capabilities: list[str],
        peer_name: Optional[str] = None,
        started: Optional[datetime] = None,
    ) -> "HandshakeResult":
        """Create a successful handshake result."""
        now = datetime.utcnow()
        start = started or now
        latency = int((now - start).total_seconds() * 1000)
        
        # Determine trust level
        if trust_score >= 900:
            level = "verified_partner"
        elif trust_score >= 700:
            level = "trusted"
        elif trust_score >= 400:
            level = "standard"
        else:
            level = "untrusted"
        
        return cls(
            verified=True,
            peer_did=peer_did,
            peer_name=peer_name,
            trust_score=trust_score,
            trust_level=level,
            capabilities=capabilities,
            handshake_started=start,
            handshake_completed=now,
            latency_ms=latency,
        )
    
    @classmethod
    def failure(
        cls,
        peer_did: str,
        reason: str,
        started: Optional[datetime] = None,
    ) -> "HandshakeResult":
        """Create a failed handshake result."""
        now = datetime.utcnow()
        start = started or now
        latency = int((now - start).total_seconds() * 1000)
        
        return cls(
            verified=False,
            peer_did=peer_did,
            trust_score=0,
            handshake_started=start,
            handshake_completed=now,
            latency_ms=latency,
            rejection_reason=reason,
        )


class TrustHandshake:
    """
    Implements IATP trust handshakes.
    
    The handshake verifies:
    1. Agent identity (via signature verification)
    2. Trust score (from registry/Nexus)
    3. Capabilities (attestation)
    
    Target: <200ms for cross-cloud handshakes.
    
    Features (from A2A review):
    - TTL-based verification caching
    - Synchronous verification option
    """
    
    MAX_HANDSHAKE_MS = 200
    DEFAULT_CACHE_TTL_SECONDS = 900  # 15 minutes
    
    def __init__(self, agent_did: str, identity: Optional[AgentIdentity] = None, cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS):
        self.agent_did = agent_did
        self.identity = identity
        self._pending_challenges: dict[str, HandshakeChallenge] = {}
        self._verified_peers: dict[str, tuple[HandshakeResult, datetime]] = {}
        self._cache_ttl = timedelta(seconds=cache_ttl_seconds)
    
    def _get_cached_result(self, peer_did: str) -> Optional[HandshakeResult]:
        """Get cached verification result if still valid."""
        if peer_did in self._verified_peers:
            result, timestamp = self._verified_peers[peer_did]
            if datetime.utcnow() - timestamp < self._cache_ttl:
                return result
            # Expired - remove from cache
            del self._verified_peers[peer_did]
        return None
    
    def _cache_result(self, peer_did: str, result: HandshakeResult) -> None:
        """Cache a verification result with timestamp."""
        self._verified_peers[peer_did] = (result, datetime.utcnow())
    
    def clear_cache(self) -> None:
        """Clear all cached verification results."""
        self._verified_peers.clear()
    
    async def initiate(
        self,
        peer_did: str,
        protocol: str = "iatp",
        required_trust_score: int = 700,
        required_capabilities: Optional[list[str]] = None,
        use_cache: bool = True,
    ) -> HandshakeResult:
        """
        Initiate a trust handshake with a peer.
        
        Three-phase handshake:
        1. Challenge: Send nonce to peer
        2. Response: Peer signs nonce + attestation
        3. Verification: Verify signature + trust score
        
        Args:
            peer_did: The peer's DID
            protocol: Protocol to use (default: iatp)
            required_trust_score: Minimum trust score required
            required_capabilities: Required capabilities (optional)
            use_cache: Whether to use cached results (default: True)
            
        Returns:
            HandshakeResult with verification status
        """
        # Check cache first
        if use_cache:
            cached = self._get_cached_result(peer_did)
            if cached:
                return cached
        
        start = datetime.utcnow()
        
        try:
            # Phase 1: Generate and send challenge
            challenge = HandshakeChallenge.generate()
            self._pending_challenges[challenge.challenge_id] = challenge
            
            # Phase 2: Get response (would be async HTTP in production)
            response = await self._get_peer_response(peer_did, challenge)
            
            if not response:
                result = HandshakeResult.failure(
                    peer_did, "No response from peer", start
                )
                return result
            
            # Phase 3: Verify response
            verification = await self._verify_response(
                response, challenge, required_trust_score, required_capabilities
            )
            
            if not verification["valid"]:
                result = HandshakeResult.failure(
                    peer_did, verification["reason"], start
                )
                return result
            
            result = HandshakeResult.success(
                peer_did=peer_did,
                trust_score=response.trust_score,
                capabilities=response.capabilities,
                started=start,
            )
            
            # Cache successful result
            self._cache_result(peer_did, result)
            return result
            
        except asyncio.TimeoutError:
            return HandshakeResult.failure(
                peer_did, "Handshake timeout", start
            )
        except Exception as e:
            return HandshakeResult.failure(
                peer_did, f"Handshake error: {str(e)}", start
            )
        finally:
            # Cleanup
            if challenge.challenge_id in self._pending_challenges:
                del self._pending_challenges[challenge.challenge_id]
    
    async def respond(
        self,
        challenge: HandshakeChallenge,
        my_capabilities: list[str],
        my_trust_score: int,
        private_key: any = None,  # Deprecated; use identity parameter
        identity: Optional[AgentIdentity] = None,
    ) -> HandshakeResponse:
        """
        Respond to a trust handshake challenge.
        
        Signs the challenge with our private key and attests capabilities.
        """
        # Check challenge not expired
        if challenge.is_expired():
            raise ValueError("Challenge expired")
        
        # Generate response nonce
        response_nonce = secrets.token_hex(16)
        
        # Create signature payload
        payload = f"{challenge.challenge_id}:{challenge.nonce}:{response_nonce}:{self.agent_did}"
        
        # Sign with Ed25519 if identity available, fall back to SHA256
        _id = identity or (self.identity if hasattr(self, 'identity') else None)
        if _id and _id._private_key is not None:
            signature = _id.sign(payload.encode())
            pub_key = _id.public_key
        else:
            signature = hashlib.sha256(payload.encode()).hexdigest()
            pub_key = hashlib.sha256(self.agent_did.encode()).hexdigest()
        
        return HandshakeResponse(
            challenge_id=challenge.challenge_id,
            response_nonce=response_nonce,
            agent_did=self.agent_did,
            capabilities=my_capabilities,
            trust_score=my_trust_score,
            signature=signature,
            public_key=pub_key,
        )
    
    async def _get_peer_response(
        self,
        peer_did: str,
        challenge: HandshakeChallenge,
    ) -> Optional[HandshakeResponse]:
        """
        Send challenge to peer and get response.
        
        In production, this would:
        1. Resolve peer DID to endpoint
        2. POST challenge to peer's IATP endpoint
        3. Receive and parse response
        """
        # Simulate peer response for now
        # In production, would make HTTP request to peer
        await asyncio.sleep(0.05)  # Simulate network latency
        
        response_nonce = secrets.token_hex(16)
        sim_payload = f"{challenge.challenge_id}:{challenge.nonce}:{response_nonce}:{peer_did}"
        
        return HandshakeResponse(
            challenge_id=challenge.challenge_id,
            response_nonce=response_nonce,
            agent_did=peer_did,
            capabilities=["read:data", "write:reports"],
            trust_score=750,
            signature=hashlib.sha256(sim_payload.encode()).hexdigest(),
            public_key=hashlib.sha256(peer_did.encode()).hexdigest(),
        )
    
    async def _verify_response(
        self,
        response: HandshakeResponse,
        challenge: HandshakeChallenge,
        required_score: int,
        required_capabilities: Optional[list[str]],
    ) -> dict:
        """
        Verify a handshake response.
        
        Checks:
        1. Challenge ID matches
        2. Signature is valid
        3. Trust score meets threshold
        4. Required capabilities present
        """
        # Verify challenge ID
        if response.challenge_id != challenge.challenge_id:
            return {"valid": False, "reason": "Challenge ID mismatch"}
        
        # Verify not expired
        if challenge.is_expired():
            return {"valid": False, "reason": "Challenge expired"}
        
        # Verify signature: try Ed25519 first, fall back to SHA256
        payload = f"{response.challenge_id}:{challenge.nonce}:{response.response_nonce}:{response.agent_did}"
        try:
            temp = AgentIdentity.model_construct(public_key=response.public_key)
            sig_valid = temp.verify_signature(payload.encode(), response.signature)
        except Exception:
            sig_valid = False
        if not sig_valid:
            expected = hashlib.sha256(payload.encode()).hexdigest()
            if response.signature != expected:
                return {"valid": False, "reason": "Signature verification failed"}
        
        # Verify trust score
        if response.trust_score < required_score:
            return {
                "valid": False,
                "reason": f"Trust score {response.trust_score} below required {required_score}"
            }
        
        # Verify capabilities
        if required_capabilities:
            missing = set(required_capabilities) - set(response.capabilities)
            if missing:
                return {
                    "valid": False,
                    "reason": f"Missing capabilities: {missing}"
                }
        
        return {"valid": True, "reason": None}
    
    def create_challenge(self) -> HandshakeChallenge:
        """Create a new challenge for incoming handshake."""
        challenge = HandshakeChallenge.generate()
        self._pending_challenges[challenge.challenge_id] = challenge
        return challenge
    
    def validate_challenge(self, challenge_id: str) -> bool:
        """Check if a challenge ID is valid and pending."""
        challenge = self._pending_challenges.get(challenge_id)
        if not challenge:
            return False
        return not challenge.is_expired()
