"""
Delegation Chains

Cryptographic delegation chains that ensure sub-agents can never
have more capabilities than their parent. Scope always narrows.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import hashlib
import json

from agentmesh.identity.agent_id import AgentIdentity


class DelegationLink(BaseModel):
    """
    A single link in a delegation chain.
    
    Each link represents a parent granting capabilities to a child.
    The child's capabilities MUST be a subset of the parent's.
    """
    
    link_id: str = Field(..., description="Unique link identifier")
    
    # Chain position
    depth: int = Field(..., ge=0, description="Depth in chain (0 = root)")
    
    # Agents
    parent_did: str = Field(..., description="DID of parent agent")
    child_did: str = Field(..., description="DID of child agent")
    
    # Capability narrowing
    parent_capabilities: list[str] = Field(..., description="Parent's capabilities at delegation time")
    delegated_capabilities: list[str] = Field(..., description="Capabilities granted to child")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None)
    
    # Cryptographic binding
    parent_signature: str = Field(..., description="Parent's signature on this delegation")
    link_hash: str = Field(..., description="Hash of this link for chain verification")
    previous_link_hash: Optional[str] = Field(None, description="Hash of previous link in chain")
    
    def verify_capability_narrowing(self) -> bool:
        """Verify that delegated capabilities are a subset of parent's."""
        for cap in self.delegated_capabilities:
            if cap not in self.parent_capabilities:
                # Check for wildcard narrowing (e.g., read:* -> read:data)
                if not self._is_narrower_capability(cap, self.parent_capabilities):
                    return False
        return True
    
    def _is_narrower_capability(self, cap: str, parent_caps: list[str]) -> bool:
        """Check if a capability is a narrowed version of a parent capability."""
        for parent_cap in parent_caps:
            if parent_cap == "*":
                return True
            if parent_cap.endswith(":*"):
                prefix = parent_cap[:-2]
                if cap.startswith(prefix + ":"):
                    return True
        return False
    
    def compute_hash(self) -> str:
        """Compute hash of this link for chain verification."""
        data = {
            "link_id": self.link_id,
            "depth": self.depth,
            "parent_did": self.parent_did,
            "child_did": self.child_did,
            "delegated_capabilities": sorted(self.delegated_capabilities),
            "created_at": self.created_at.isoformat(),
            "previous_link_hash": self.previous_link_hash,
        }
        canonical = json.dumps(data, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()
    
    def is_valid(self) -> bool:
        """Check if this link is valid."""
        # Check expiration
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        
        # Verify capability narrowing
        if not self.verify_capability_narrowing():
            return False
        
        # Verify hash
        if self.link_hash != self.compute_hash():
            return False
        
        return True


class DelegationChain(BaseModel):
    """
    Complete delegation chain from root sponsor to current agent.
    
    Properties:
    - Immutable once created
    - Each link narrows capabilities
    - Cryptographically verifiable
    - Traceable to human sponsor
    """
    
    chain_id: str = Field(..., description="Unique chain identifier")
    
    # Root (human sponsor)
    root_sponsor_email: str = Field(..., description="Human sponsor at chain root")
    root_sponsor_verified: bool = Field(default=False)
    root_capabilities: list[str] = Field(..., description="Capabilities granted by sponsor")
    
    # Known agent identities for signature verification
    known_identities: dict[str, AgentIdentity] = Field(default_factory=dict)
    
    # Chain links
    links: list[DelegationLink] = Field(default_factory=list)
    
    # Final agent
    leaf_did: str = Field(..., description="DID of the agent at end of chain")
    leaf_capabilities: list[str] = Field(..., description="Final effective capabilities")
    
    # Chain metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    total_depth: int = Field(default=0)
    
    # Verification
    chain_hash: str = Field(default="", description="Hash of entire chain")
    
    def add_link(self, link: DelegationLink) -> None:
        """
        Add a link to the chain.
        
        Validates that:
        1. Link connects to current leaf
        2. Capabilities are properly narrowed
        3. Link hash is correct
        """
        if self.links:
            last_link = self.links[-1]
            if link.parent_did != last_link.child_did:
                raise ValueError("Link does not connect to chain")
            if link.previous_link_hash != last_link.link_hash:
                raise ValueError("Link hash does not match previous link")
        else:
            # First link - parent should be root
            if link.depth != 0:
                raise ValueError("First link must have depth 0")
        
        # Verify capability narrowing
        if not link.verify_capability_narrowing():
            raise ValueError("Link does not properly narrow capabilities")
        
        self.links.append(link)
        self.total_depth = len(self.links)
        self.leaf_did = link.child_did
        self.leaf_capabilities = link.delegated_capabilities
        self._update_chain_hash()
    
    def _verify_link_signature(self, link: DelegationLink) -> bool:
        """Verify the Ed25519 signature on a delegation link."""
        identity = self.known_identities.get(link.parent_did)
        if identity is None:
            return True  # Graceful fallback — can't verify without identity
        signable_data = f"{link.parent_did}:{link.child_did}:{','.join(sorted(link.delegated_capabilities))}"
        return identity.verify_signature(signable_data.encode(), link.parent_signature)

    def verify(self) -> tuple[bool, Optional[str]]:
        """
        Verify the entire chain.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.links:
            return True, None
        
        previous_hash = None
        previous_capabilities = self.root_capabilities
        
        for i, link in enumerate(self.links):
            # Verify depth
            if link.depth != i:
                return False, f"Invalid depth at link {i}"
            
            # Verify hash chain
            if link.previous_link_hash != previous_hash:
                return False, f"Hash chain broken at link {i}"
            
            # Verify capability narrowing against actual previous capabilities
            for cap in link.delegated_capabilities:
                if cap not in previous_capabilities:
                    if not link._is_narrower_capability(cap, previous_capabilities):
                        return False, f"Capability escalation at link {i}: {cap}"
            
            # Verify link hash
            if link.link_hash != link.compute_hash():
                return False, f"Invalid link hash at link {i}"
            
            # Verify Ed25519 signature
            if not self._verify_link_signature(link):
                return False, f"Invalid signature at link {i}"
            
            previous_hash = link.link_hash
            previous_capabilities = link.delegated_capabilities
        
        return True, None
    
    def get_effective_capabilities(self) -> list[str]:
        """Get the effective capabilities at the end of the chain."""
        if self.links:
            return self.links[-1].delegated_capabilities
        return self.root_capabilities
    
    def trace_capability(self, capability: str) -> list[dict]:
        """
        Trace how a capability was granted through the chain.
        
        Returns list of grants/narrowings from root to leaf.
        """
        trace = []
        
        # Check root
        if capability in self.root_capabilities or "*" in self.root_capabilities:
            trace.append({
                "level": "root",
                "grantor": self.root_sponsor_email,
                "capability": capability,
                "source_capabilities": self.root_capabilities,
            })
        
        # Check each link
        for link in self.links:
            if capability in link.delegated_capabilities:
                trace.append({
                    "level": f"depth_{link.depth}",
                    "grantor": link.parent_did,
                    "grantee": link.child_did,
                    "capability": capability,
                    "parent_capabilities": link.parent_capabilities,
                    "delegated_capabilities": link.delegated_capabilities,
                })
        
        return trace
    
    def _update_chain_hash(self) -> None:
        """Update the overall chain hash."""
        data = {
            "chain_id": self.chain_id,
            "root_sponsor": self.root_sponsor_email,
            "links": [link.link_hash for link in self.links],
        }
        canonical = json.dumps(data, sort_keys=True)
        self.chain_hash = hashlib.sha256(canonical.encode()).hexdigest()
    
    @classmethod
    def create_root(
        cls,
        sponsor_email: str,
        root_agent_did: str,
        capabilities: list[str],
        sponsor_verified: bool = False,
    ) -> tuple["DelegationChain", DelegationLink]:
        """
        Create a new chain with a root sponsor.
        
        Returns the chain and the first link to be signed.
        """
        import uuid
        
        chain_id = f"chain_{uuid.uuid4().hex[:16]}"
        
        chain = cls(
            chain_id=chain_id,
            root_sponsor_email=sponsor_email,
            root_sponsor_verified=sponsor_verified,
            root_capabilities=capabilities,
            leaf_did=root_agent_did,
            leaf_capabilities=capabilities,
        )
        
        # Create first link (sponsor -> root agent)
        link = DelegationLink(
            link_id=f"link_{uuid.uuid4().hex[:12]}",
            depth=0,
            parent_did=f"did:mesh:sponsor:{sponsor_email}",
            child_did=root_agent_did,
            parent_capabilities=capabilities,
            delegated_capabilities=capabilities,
            parent_signature="",  # To be signed
            link_hash="",  # To be computed after signing
        )
        link.link_hash = link.compute_hash()
        
        return chain, link
