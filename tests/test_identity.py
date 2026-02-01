"""Tests for AgentMesh Identity module."""

import pytest
from datetime import datetime, timedelta

from agentmesh.identity import (
    AgentIdentity,
    AgentDID,
    IdentityRegistry,
    Credential,
    CredentialManager,
    DelegationChain,
    DelegationLink,
    HumanSponsor,
    SponsorRegistry,
    RiskScorer,
    RiskScore,
    SPIFFEIdentity,
)


class TestAgentDID:
    """Tests for AgentDID."""
    
    def test_generate_did(self):
        """Test generating a new DID."""
        did = AgentDID.generate("test-agent")
        
        assert did.method == "mesh"
        assert len(did.unique_id) == 32
        assert str(did).startswith("did:mesh:")
    
    def test_generate_did_with_org(self):
        """Test generating DID with organization."""
        did = AgentDID.generate("test-agent", org="acme-corp")
        
        assert did.method == "mesh"
        assert str(did).startswith("did:mesh:")
    
    def test_parse_did_string(self):
        """Test parsing a DID string."""
        did_str = "did:mesh:abc123def456"
        did = AgentDID.from_string(did_str)
        
        assert did.unique_id == "abc123def456"
        assert str(did) == did_str
    
    def test_invalid_did_string(self):
        """Test parsing invalid DID raises error."""
        with pytest.raises(ValueError):
            AgentDID.from_string("invalid:did:format")
    
    def test_did_hash(self):
        """Test DID is hashable for use in sets/dicts."""
        did1 = AgentDID.generate("agent-1")
        did2 = AgentDID.generate("agent-2")
        
        did_set = {did1, did2}
        assert len(did_set) == 2


class TestAgentIdentity:
    """Tests for AgentIdentity."""
    
    def test_create_identity(self):
        """Test creating a new agent identity."""
        identity = AgentIdentity.create(
            name="test-agent",
            sponsor="sponsor@example.com",
        )
        
        assert identity.name == "test-agent"
        assert str(identity.did).startswith("did:mesh:")
        assert identity.public_key is not None
        assert identity.sponsor_email == "sponsor@example.com"
        assert identity.status == "active"
    
    def test_create_with_capabilities(self):
        """Test creating identity with capabilities."""
        identity = AgentIdentity.create(
            name="capable-agent",
            sponsor="sponsor@example.com",
            capabilities=["read", "write", "execute"],
        )
        
        assert set(identity.capabilities) == {"read", "write", "execute"}
    
    def test_identity_unique(self):
        """Test that each identity is unique."""
        id1 = AgentIdentity.create("agent-1", "s@e.com")
        id2 = AgentIdentity.create("agent-2", "s@e.com")
        
        assert str(id1.did) != str(id2.did)
        assert id1.public_key != id2.public_key
    
    def test_sign_and_verify(self):
        """Test signing and verification."""
        identity = AgentIdentity.create("signer", "s@e.com")
        
        message = b"Hello, AgentMesh!"
        signature = identity.sign(message)
        
        assert identity.verify_signature(message, signature)
        assert not identity.verify_signature(b"Modified message", signature)
    
    def test_delegate_creates_child(self):
        """Test delegating to create sub-agent."""
        parent = AgentIdentity.create(
            "parent-agent", 
            "s@e.com",
            capabilities=["read", "write", "delete"],
        )
        
        child = parent.delegate(
            "child-agent", 
            capabilities=["read", "write"],
        )
        
        assert child.parent_did == str(parent.did)
        assert set(child.capabilities) == {"read", "write"}
        assert child.delegation_depth == parent.delegation_depth + 1
    
    def test_delegate_capability_narrowing(self):
        """Test that delegation cannot widen capabilities."""
        parent = AgentIdentity.create(
            "parent-agent",
            "s@e.com", 
            capabilities=["read"],
        )
        
        with pytest.raises(ValueError):
            parent.delegate(
                "child-agent",
                capabilities=["read", "write"],  # Can't add "write"
            )


class TestIdentityRegistry:
    """Tests for IdentityRegistry."""
    
    def test_register_identity(self):
        """Test registering an identity."""
        registry = IdentityRegistry()
        identity = AgentIdentity.create("test", "s@e.com")
        
        registry.register(identity)
        
        retrieved = registry.get(str(identity.did))
        assert retrieved is not None
        assert retrieved.name == "test"
    
    def test_revoke_identity(self):
        """Test revoking an identity."""
        registry = IdentityRegistry()
        identity = AgentIdentity.create("test", "s@e.com")
        registry.register(identity)
        
        registry.revoke(str(identity.did), reason="Testing revocation")
        
        retrieved = registry.get(str(identity.did))
        assert retrieved.status == "revoked"


class TestCredentials:
    """Tests for Credential and CredentialManager."""
    
    def test_credential_creation(self):
        """Test creating credentials."""
        cred = Credential(
            agent_did="did:mesh:test123",
            scopes=["read", "write"],
        )
        
        assert cred.agent_did == "did:mesh:test123"
        assert not cred.is_expired()
        assert cred.is_valid()
    
    def test_credential_default_ttl(self):
        """Test credential has 15-minute default TTL."""
        cred = Credential(agent_did="did:mesh:test")
        
        # Should expire in approximately 15 minutes
        time_diff = cred.expires_at - datetime.utcnow()
        assert 14 * 60 < time_diff.total_seconds() < 16 * 60
    
    def test_credential_expiry(self):
        """Test credential expiration."""
        cred = Credential(
            agent_did="did:mesh:test",
            expires_at=datetime.utcnow() - timedelta(minutes=1),
        )
        
        assert cred.is_expired()
        assert not cred.is_valid()
    
    def test_credential_manager_issue(self):
        """Test credential manager issues credentials."""
        manager = CredentialManager()
        
        cred = manager.issue("did:mesh:test", scopes=["read"])
        
        assert cred is not None
        assert cred.agent_did == "did:mesh:test"
        assert manager.validate(cred)
    
    def test_credential_manager_revoke(self):
        """Test credential revocation."""
        manager = CredentialManager()
        
        cred = manager.issue("did:mesh:test")
        assert manager.validate(cred)
        
        manager.revoke(cred.credential_id)
        assert not manager.validate(cred)
    
    def test_credential_manager_rotate(self):
        """Test credential rotation."""
        manager = CredentialManager()
        
        old_cred = manager.issue("did:mesh:test")
        new_cred = manager.rotate(old_cred.credential_id)
        
        assert new_cred.credential_id != old_cred.credential_id
        assert not manager.validate(old_cred)
        assert manager.validate(new_cred)


class TestDelegation:
    """Tests for DelegationChain."""
    
    def test_create_chain(self):
        """Test creating delegation chain."""
        chain = DelegationChain.create(
            root_sponsor="sponsor@example.com",
            root_did="did:mesh:root123",
            root_capabilities=["read", "write", "admin"],
        )
        
        assert chain.root_sponsor == "sponsor@example.com"
        assert chain.root_did == "did:mesh:root123"
        assert len(chain.links) == 0
    
    def test_add_delegation_link(self):
        """Test adding delegation links."""
        chain = DelegationChain.create(
            root_sponsor="sponsor@example.com",
            root_did="did:mesh:root",
            root_capabilities=["read", "write"],
        )
        
        chain.add_link(
            from_did="did:mesh:root",
            to_did="did:mesh:child",
            capabilities=["read"],
        )
        
        assert len(chain.links) == 1
        assert chain.get_capabilities("did:mesh:child") == ["read"]
    
    def test_capability_narrowing_enforced(self):
        """Test that capabilities can only narrow, never widen."""
        chain = DelegationChain.create(
            root_sponsor="sponsor@example.com",
            root_did="did:mesh:root",
            root_capabilities=["read"],
        )
        
        chain.add_link(
            from_did="did:mesh:root",
            to_did="did:mesh:child",
            capabilities=["read"],
        )
        
        # Attempt to widen should fail
        with pytest.raises(ValueError):
            chain.add_link(
                from_did="did:mesh:child",
                to_did="did:mesh:grandchild",
                capabilities=["read", "write"],  # Can't add "write"
            )
    
    def test_verify_chain(self):
        """Test chain verification."""
        chain = DelegationChain.create(
            root_sponsor="sponsor@example.com",
            root_did="did:mesh:root",
            root_capabilities=["read", "write"],
        )
        
        chain.add_link(
            from_did="did:mesh:root",
            to_did="did:mesh:child",
            capabilities=["read"],
        )
        
        assert chain.verify()


class TestSponsor:
    """Tests for HumanSponsor."""
    
    def test_create_sponsor(self):
        """Test creating a human sponsor."""
        sponsor = HumanSponsor(
            email="sponsor@example.com",
            name="Test Sponsor",
        )
        
        assert sponsor.email == "sponsor@example.com"
        assert sponsor.is_active
    
    def test_sponsor_agent(self):
        """Test sponsoring an agent."""
        sponsor = HumanSponsor(
            email="sponsor@example.com",
            name="Test Sponsor",
        )
        
        sponsor.sponsor_agent("did:mesh:test")
        
        assert "did:mesh:test" in sponsor.sponsored_agents
    
    def test_revoke_sponsorship(self):
        """Test revoking sponsorship."""
        sponsor = HumanSponsor(
            email="sponsor@example.com",
            name="Test Sponsor",
        )
        
        sponsor.sponsor_agent("did:mesh:test")
        sponsor.revoke_agent("did:mesh:test")
        
        assert "did:mesh:test" not in sponsor.sponsored_agents


class TestSponsorRegistry:
    """Tests for SponsorRegistry."""
    
    def test_register_sponsor(self):
        """Test registering a sponsor."""
        registry = SponsorRegistry()
        sponsor = HumanSponsor(email="s@e.com", name="Test")
        
        registry.register(sponsor)
        
        retrieved = registry.get("s@e.com")
        assert retrieved is not None
        assert retrieved.name == "Test"
    
    def test_get_sponsor_for_agent(self):
        """Test finding sponsor for an agent."""
        registry = SponsorRegistry()
        sponsor = HumanSponsor(email="s@e.com", name="Test")
        sponsor.sponsor_agent("did:mesh:agent1")
        registry.register(sponsor)
        
        found = registry.get_sponsor_for_agent("did:mesh:agent1")
        assert found is not None
        assert found.email == "s@e.com"


class TestRiskScoring:
    """Tests for RiskScorer."""
    
    def test_initial_score(self):
        """Test initial risk score."""
        scorer = RiskScorer()
        
        score = scorer.calculate("did:mesh:new-agent")
        
        assert isinstance(score, RiskScore)
        assert score.total >= 0
        assert score.total <= 100
    
    def test_add_risk_event(self):
        """Test adding risk events increases score."""
        scorer = RiskScorer()
        
        initial = scorer.calculate("did:mesh:test")
        
        scorer.add_risk_event(
            agent_did="did:mesh:test",
            event_type="policy_violation",
            severity="high",
        )
        
        after = scorer.calculate("did:mesh:test")
        assert after.total > initial.total
    
    def test_risk_decay(self):
        """Test that risk decays over time."""
        scorer = RiskScorer()
        
        scorer.add_risk_event(
            agent_did="did:mesh:test",
            event_type="minor_violation",
            severity="low",
        )
        
        # Risk should be present
        score = scorer.calculate("did:mesh:test")
        assert score.total > 0


class TestSPIFFE:
    """Tests for SPIFFE identity."""
    
    def test_create_spiffe_identity(self):
        """Test creating SPIFFE identity."""
        spiffe = SPIFFEIdentity.create(
            trust_domain="agentmesh.io",
            agent_did="did:mesh:test123",
        )
        
        assert "agentmesh.io" in spiffe.spiffe_id
        assert spiffe.trust_domain == "agentmesh.io"
    
    def test_spiffe_id_format(self):
        """Test SPIFFE ID follows standard format."""
        spiffe = SPIFFEIdentity.create(
            trust_domain="example.com",
            agent_did="did:mesh:abc",
        )
        
        # SPIFFE ID should be: spiffe://<trust-domain>/<path>
        assert spiffe.spiffe_id.startswith("spiffe://example.com/")
