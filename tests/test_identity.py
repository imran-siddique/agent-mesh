"""Tests for AgentMesh Identity module."""

import pytest
from datetime import datetime, timedelta

from agentmesh.identity import (
    AgentIdentity,
    Credential,
    CredentialManager,
    DelegationChain,
    HumanSponsor,
    RiskScorer,
)


class TestAgentIdentity:
    """Tests for AgentIdentity."""
    
    def test_create_identity(self):
        """Test creating a new agent identity."""
        identity = AgentIdentity.create("test-agent")
        
        assert identity.name == "test-agent"
        assert identity.did.startswith("did:agentmesh:")
        assert identity.public_key is not None
        assert identity.private_key is not None
    
    def test_identity_unique(self):
        """Test that each identity is unique."""
        id1 = AgentIdentity.create("agent-1")
        id2 = AgentIdentity.create("agent-2")
        
        assert id1.did != id2.did
        assert id1.public_key != id2.public_key
    
    def test_delegation(self):
        """Test delegating to create sub-agent."""
        parent = AgentIdentity.create("parent-agent")
        child = parent.delegate("child-agent", capabilities=["read", "write"])
        
        assert child.parent_did == parent.did
        assert set(child.capabilities) == {"read", "write"}
    
    def test_signature(self):
        """Test signing and verification."""
        identity = AgentIdentity.create("signer")
        
        message = b"Hello, AgentMesh!"
        signature = identity.sign(message)
        
        assert identity.verify(message, signature)
        assert not identity.verify(b"Modified message", signature)


class TestCredentials:
    """Tests for Credential and CredentialManager."""
    
    def test_credential_creation(self):
        """Test creating credentials."""
        cred = Credential(
            agent_did="did:agentmesh:test",
            scopes=["read", "write"],
        )
        
        assert cred.agent_did == "did:agentmesh:test"
        assert not cred.is_expired()
    
    def test_credential_expiry(self):
        """Test credential expiration."""
        cred = Credential(
            agent_did="did:agentmesh:test",
            expires_at=datetime.utcnow() - timedelta(minutes=1),
        )
        
        assert cred.is_expired()
    
    def test_credential_manager(self):
        """Test credential manager."""
        manager = CredentialManager()
        
        cred = manager.issue("did:agentmesh:test", scopes=["read"])
        
        assert cred is not None
        assert manager.validate(cred)
    
    def test_credential_revocation(self):
        """Test credential revocation."""
        manager = CredentialManager()
        
        cred = manager.issue("did:agentmesh:test")
        assert manager.validate(cred)
        
        manager.revoke(cred.credential_id)
        assert not manager.validate(cred)


class TestDelegation:
    """Tests for DelegationChain."""
    
    def test_create_chain(self):
        """Test creating delegation chain."""
        chain = DelegationChain.create(
            root_sponsor="sponsor@example.com",
            root_did="did:agentmesh:root",
        )
        
        assert chain.root_sponsor == "sponsor@example.com"
        assert len(chain.links) == 0
    
    def test_add_delegation(self):
        """Test adding delegation links."""
        chain = DelegationChain.create(
            root_sponsor="sponsor@example.com",
            root_did="did:agentmesh:root",
        )
        
        chain.add_link(
            from_did="did:agentmesh:root",
            to_did="did:agentmesh:child",
            capabilities=["read"],
        )
        
        assert len(chain.links) == 1
        assert chain.get_capabilities("did:agentmesh:child") == ["read"]
    
    def test_capability_narrowing(self):
        """Test that capabilities can only narrow, never widen."""
        chain = DelegationChain.create(
            root_sponsor="sponsor@example.com",
            root_did="did:agentmesh:root",
        )
        
        # First delegation with limited capabilities
        chain.add_link(
            from_did="did:agentmesh:root",
            to_did="did:agentmesh:child",
            capabilities=["read"],
        )
        
        # Attempt to widen should fail
        with pytest.raises(ValueError):
            chain.add_link(
                from_did="did:agentmesh:child",
                to_did="did:agentmesh:grandchild",
                capabilities=["read", "write"],  # Can't add "write"
            )


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
        
        sponsor.sponsor_agent("did:agentmesh:test")
        
        assert "did:agentmesh:test" in sponsor.sponsored_agents


class TestRiskScoring:
    """Tests for RiskScorer."""
    
    def test_initial_score(self):
        """Test initial risk score."""
        scorer = RiskScorer()
        
        score = scorer.calculate("did:agentmesh:new-agent")
        
        assert score.total >= 0
        assert score.total <= 100
    
    def test_risk_factors(self):
        """Test adding risk factors."""
        scorer = RiskScorer()
        
        scorer.add_risk_event(
            agent_did="did:agentmesh:test",
            event_type="policy_violation",
            severity="high",
        )
        
        score_after = scorer.calculate("did:agentmesh:test")
        assert score_after.total > 0  # Risk increased
