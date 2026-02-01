"""Tests for AgentMesh Trust module."""

import pytest
from datetime import datetime

from agentmesh.trust import (
    TrustBridge,
    ProtocolBridge,
    TrustHandshake,
    HandshakeResult,
    CapabilityScope,
    CapabilityGrant,
    CapabilityRegistry,
)


class TestTrustBridge:
    """Tests for TrustBridge."""
    
    def test_create_bridge(self):
        """Test creating a trust bridge."""
        bridge = TrustBridge(agent_did="did:mesh:test")
        
        assert bridge is not None
        assert bridge.agent_did == "did:mesh:test"
    
    def test_default_trust_threshold(self):
        """Test default trust threshold is 700."""
        bridge = TrustBridge(agent_did="did:mesh:test")
        
        assert bridge.default_trust_threshold == 700
    
    def test_get_trusted_peers_empty(self):
        """Test getting trusted peers when none exist."""
        bridge = TrustBridge(agent_did="did:mesh:test")
        
        peers = bridge.get_trusted_peers()
        assert len(peers) == 0
    
    @pytest.mark.asyncio
    async def test_verify_peer(self):
        """Test verifying a peer."""
        bridge = TrustBridge(agent_did="did:mesh:agent-a")
        
        # Verification requires network, so this tests the flow
        result = await bridge.verify_peer(
            peer_did="did:mesh:agent-b",
            protocol="iatp",
        )
        
        assert isinstance(result, HandshakeResult)


class TestProtocolBridge:
    """Tests for ProtocolBridge."""
    
    def test_create_protocol_bridge(self):
        """Test creating a protocol bridge."""
        bridge = ProtocolBridge(agent_did="did:mesh:test")
        
        assert bridge is not None
        assert "a2a" in bridge.supported_protocols
        assert "mcp" in bridge.supported_protocols
        assert "iatp" in bridge.supported_protocols
    
    def test_a2a_to_mcp_translation(self):
        """Test A2A to MCP message translation."""
        bridge = ProtocolBridge(agent_did="did:mesh:test")
        
        a2a_message = {
            "task_type": "summarize",
            "parameters": {"text": "Hello world"},
        }
        
        mcp_message = bridge._a2a_to_mcp(a2a_message)
        
        assert mcp_message["method"] == "tools/call"
        assert mcp_message["params"]["name"] == "summarize"
    
    def test_mcp_to_a2a_translation(self):
        """Test MCP to A2A message translation."""
        bridge = ProtocolBridge(agent_did="did:mesh:test")
        
        mcp_message = {
            "method": "tools/call",
            "params": {
                "name": "analyze",
                "arguments": {"data": [1, 2, 3]},
            },
        }
        
        a2a_message = bridge._mcp_to_a2a(mcp_message)
        
        assert a2a_message["task_type"] == "analyze"


class TestTrustHandshake:
    """Tests for TrustHandshake."""
    
    def test_create_handshake(self):
        """Test creating a trust handshake."""
        handshake = TrustHandshake(agent_did="did:mesh:agent-a")
        
        assert handshake is not None
        assert handshake.agent_did == "did:mesh:agent-a"
    
    def test_create_challenge(self):
        """Test challenge creation."""
        handshake = TrustHandshake(agent_did="did:mesh:agent-a")
        
        challenge = handshake.create_challenge()
        
        assert challenge.nonce is not None
        assert challenge.timestamp is not None
        assert len(challenge.nonce) > 0
    
    @pytest.mark.asyncio
    async def test_handshake_initiate(self):
        """Test initiating a handshake."""
        handshake = TrustHandshake(
            agent_did="did:mesh:agent-a",
            timeout_ms=100,  # Short timeout for test
        )
        
        result = await handshake.initiate(
            peer_did="did:mesh:agent-b",
            required_trust_score=500,
        )
        
        assert isinstance(result, HandshakeResult)


class TestHandshakeResult:
    """Tests for HandshakeResult."""
    
    def test_successful_result(self):
        """Test creating a successful result."""
        result = HandshakeResult(
            verified=True,
            peer_did="did:mesh:peer",
            trust_score=750,
            capabilities=["read", "write"],
        )
        
        assert result.verified
        assert result.trust_score == 750
        assert result.error is None
    
    def test_failed_result(self):
        """Test creating a failed result."""
        result = HandshakeResult(
            verified=False,
            peer_did="did:mesh:peer",
            trust_score=0,
            error="Peer not found",
        )
        
        assert not result.verified
        assert result.error == "Peer not found"


class TestCapabilities:
    """Tests for CapabilityScope and CapabilityRegistry."""
    
    def test_capability_scope_creation(self):
        """Test creating a capability scope."""
        scope = CapabilityScope(
            name="file_access",
            resources=["file:///data/*"],
            actions=["read", "write"],
        )
        
        assert scope.name == "file_access"
        assert "read" in scope.actions
        assert "write" in scope.actions
    
    def test_capability_scope_allows(self):
        """Test checking if action is allowed."""
        scope = CapabilityScope(
            name="limited",
            resources=["api://data"],
            actions=["read"],
        )
        
        assert scope.allows("read")
        assert not scope.allows("write")
        assert not scope.allows("delete")
    
    def test_capability_registry_register(self):
        """Test registering capabilities."""
        registry = CapabilityRegistry()
        
        scope = CapabilityScope(
            name="api_access",
            resources=["https://api.example.com/*"],
            actions=["get", "post"],
        )
        
        registry.register(
            agent_did="did:mesh:test",
            scope=scope,
        )
        
        caps = registry.get_capabilities("did:mesh:test")
        assert len(caps) == 1
        assert caps[0].name == "api_access"
    
    def test_capability_registry_is_allowed(self):
        """Test checking if action is allowed for agent."""
        registry = CapabilityRegistry()
        
        registry.register(
            agent_did="did:mesh:test",
            scope=CapabilityScope(
                name="limited",
                resources=["resource:A"],
                actions=["read"],
            ),
        )
        
        # Should be allowed
        assert registry.is_allowed(
            agent_did="did:mesh:test",
            resource="resource:A",
            action="read",
        )
        
        # Should be denied - wrong resource
        assert not registry.is_allowed(
            agent_did="did:mesh:test",
            resource="resource:B",
            action="read",
        )
        
        # Should be denied - wrong action
        assert not registry.is_allowed(
            agent_did="did:mesh:test",
            resource="resource:A",
            action="write",
        )
    
    def test_capability_grant(self):
        """Test capability grant."""
        grant = CapabilityGrant(
            agent_did="did:mesh:test",
            scope=CapabilityScope(
                name="test",
                resources=["*"],
                actions=["read"],
            ),
            granted_by="did:mesh:admin",
        )
        
        assert grant.is_valid()
        assert not grant.is_expired()


# Note: A2AAdapter and MCPAdapter tests removed as they're not exported from the trust module
# These adapters are internal implementation details of the protocol bridges
