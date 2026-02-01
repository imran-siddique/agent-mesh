"""
SPIFFE/SVID Integration

Workload identity using SPIFFE (Secure Production Identity Framework
for Everyone) and SVID (SPIFFE Verifiable Identity Documents).

SPIFFE/SVID provides:
- Mutual TLS for all agent transport
- Zero cleartext traffic between agents
- Standard workload identity
"""

from datetime import datetime, timedelta
from typing import Optional, Literal
from pydantic import BaseModel, Field
import hashlib


class SVID(BaseModel):
    """
    SPIFFE Verifiable Identity Document.
    
    An SVID is the document that carries the SPIFFE ID and can be
    validated by a third party. AgentMesh uses X.509-SVID format.
    """
    
    spiffe_id: str = Field(..., description="SPIFFE ID (spiffe://trust-domain/path)")
    svid_type: Literal["x509", "jwt"] = Field(default="x509")
    
    # Certificate data (X.509-SVID)
    certificate_chain: Optional[list[str]] = Field(None, description="PEM-encoded cert chain")
    private_key_type: Optional[str] = Field(None, description="Key type (e.g., 'EC P-256')")
    
    # JWT-SVID fields
    jwt_token: Optional[str] = Field(None, description="JWT-SVID token")
    
    # Metadata
    trust_domain: str = Field(..., description="SPIFFE trust domain")
    issued_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(...)
    
    # Agent binding
    agent_did: str = Field(..., description="AgentMesh DID this SVID belongs to")
    
    @classmethod
    def parse_spiffe_id(cls, spiffe_id: str) -> tuple[str, str]:
        """
        Parse a SPIFFE ID into trust domain and path.
        
        Format: spiffe://trust-domain/path
        """
        if not spiffe_id.startswith("spiffe://"):
            raise ValueError(f"Invalid SPIFFE ID: {spiffe_id}")
        
        parts = spiffe_id[9:].split("/", 1)  # Remove "spiffe://"
        trust_domain = parts[0]
        path = "/" + parts[1] if len(parts) > 1 else "/"
        
        return trust_domain, path
    
    def is_valid(self) -> bool:
        """Check if SVID is currently valid."""
        now = datetime.utcnow()
        return self.issued_at <= now < self.expires_at
    
    def time_remaining(self) -> timedelta:
        """Get time remaining until expiration."""
        return max(timedelta(0), self.expires_at - datetime.utcnow())


class SPIFFEIdentity(BaseModel):
    """
    SPIFFE Identity for an agent.
    
    Maps AgentMesh identity to SPIFFE workload identity,
    enabling mTLS with other SPIFFE-aware workloads.
    """
    
    # AgentMesh identity
    agent_did: str = Field(..., description="AgentMesh DID")
    agent_name: str = Field(...)
    
    # SPIFFE identity
    spiffe_id: str = Field(..., description="Full SPIFFE ID")
    trust_domain: str = Field(...)
    workload_path: str = Field(...)
    
    # Current SVID
    current_svid: Optional[SVID] = Field(None)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @classmethod
    def create(
        cls,
        agent_did: str,
        agent_name: str,
        trust_domain: str = "agentmesh.local",
        organization: Optional[str] = None,
    ) -> "SPIFFEIdentity":
        """
        Create SPIFFE identity for an agent.
        
        SPIFFE ID format: spiffe://trust-domain/agentmesh/org/agent-name
        """
        # Build workload path
        org_part = f"/{organization}" if organization else ""
        workload_path = f"/agentmesh{org_part}/{agent_name}"
        
        spiffe_id = f"spiffe://{trust_domain}{workload_path}"
        
        return cls(
            agent_did=agent_did,
            agent_name=agent_name,
            spiffe_id=spiffe_id,
            trust_domain=trust_domain,
            workload_path=workload_path,
        )
    
    def issue_svid(
        self,
        ttl_hours: int = 1,
        svid_type: Literal["x509", "jwt"] = "x509",
    ) -> SVID:
        """
        Issue a new SVID for this identity.
        
        In production, this would request an SVID from the SPIRE server.
        """
        now = datetime.utcnow()
        
        svid = SVID(
            spiffe_id=self.spiffe_id,
            svid_type=svid_type,
            trust_domain=self.trust_domain,
            issued_at=now,
            expires_at=now + timedelta(hours=ttl_hours),
            agent_did=self.agent_did,
        )
        
        self.current_svid = svid
        return svid
    
    def get_valid_svid(self) -> Optional[SVID]:
        """Get current SVID if valid, None otherwise."""
        if self.current_svid and self.current_svid.is_valid():
            return self.current_svid
        return None
    
    def needs_rotation(self, threshold_minutes: int = 10) -> bool:
        """Check if SVID needs rotation."""
        if not self.current_svid:
            return True
        
        remaining = self.current_svid.time_remaining()
        return remaining < timedelta(minutes=threshold_minutes)


class SPIFFERegistry:
    """
    Registry mapping AgentMesh identities to SPIFFE identities.
    
    In production, this would integrate with SPIRE.
    """
    
    DEFAULT_TRUST_DOMAIN = "agentmesh.local"
    
    def __init__(self, trust_domain: Optional[str] = None):
        self.trust_domain = trust_domain or self.DEFAULT_TRUST_DOMAIN
        self._identities: dict[str, SPIFFEIdentity] = {}  # agent_did -> SPIFFEIdentity
    
    def register(
        self,
        agent_did: str,
        agent_name: str,
        organization: Optional[str] = None,
    ) -> SPIFFEIdentity:
        """Register an agent and create SPIFFE identity."""
        if agent_did in self._identities:
            return self._identities[agent_did]
        
        identity = SPIFFEIdentity.create(
            agent_did=agent_did,
            agent_name=agent_name,
            trust_domain=self.trust_domain,
            organization=organization,
        )
        
        self._identities[agent_did] = identity
        return identity
    
    def get(self, agent_did: str) -> Optional[SPIFFEIdentity]:
        """Get SPIFFE identity for an agent."""
        return self._identities.get(agent_did)
    
    def get_by_spiffe_id(self, spiffe_id: str) -> Optional[SPIFFEIdentity]:
        """Get identity by SPIFFE ID."""
        for identity in self._identities.values():
            if identity.spiffe_id == spiffe_id:
                return identity
        return None
    
    def issue_svid(self, agent_did: str) -> Optional[SVID]:
        """Issue an SVID for an agent."""
        identity = self.get(agent_did)
        if not identity:
            return None
        return identity.issue_svid()
    
    def validate_svid(self, svid: SVID) -> bool:
        """
        Validate an SVID.
        
        In production, would verify against SPIRE bundle.
        """
        # Check basic validity
        if not svid.is_valid():
            return False
        
        # Verify trust domain matches
        if svid.trust_domain != self.trust_domain:
            return False
        
        # Verify agent is registered
        identity = self.get(svid.agent_did)
        if not identity:
            return False
        
        return True
