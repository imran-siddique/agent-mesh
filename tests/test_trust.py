"""Tests for AgentMesh Trust module."""

import pytest
from datetime import datetime

from agentmesh.trust import (
    TrustBridge,
    TrustHandshake,
    HandshakeResult,
    CapabilityScope,
    CapabilityRegistry,
)


class TestTrustBridge:
    """Tests for TrustBridge."""
    
    def test_create_bridge(self):
        """Test creating a trust bridge."""
        bridge = TrustBridge()
        
        assert bridge is not None
        assert len(bridge.adapters) > 0  # Has protocol adapters
    
    def test_a2a_support(self):
        """Test A2A protocol support."""
        bridge = TrustBridge()
        
        assert bridge.supports_protocol("a2a")
    
    def test_mcp_support(self):
        """Test MCP protocol support."""
        bridge = TrustBridge()
        
        assert bridge.supports_protocol("mcp")
    
    def test_iatp_support(self):
        """Test IATP protocol support."""
        bridge = TrustBridge()
        
        assert bridge.supports_protocol("iatp")


class TestTrustHandshake:
    """Tests for TrustHandshake."""
    
    @pytest.mark.asyncio
    async def test_handshake_success(self):
        """Test successful trust handshake."""
        handshake = TrustHandshake()
        
        result = await handshake.initiate(
            initiator_did="did:agentmesh:agent-a",
            responder_did="did:agentmesh:agent-b",
            capabilities_requested=["read"],
        )
        
        assert isinstance(result, HandshakeResult)
        # Note: In real implementation, would need peer to respond
    
    @pytest.mark.asyncio
    async def test_handshake_challenge_response(self):
        """Test challenge-response mechanism."""
        handshake = TrustHandshake()
        
        challenge = handshake.create_challenge("did:agentmesh:agent-a")
        
        assert challenge.nonce is not None
        assert challenge.timestamp is not None
    
    @pytest.mark.asyncio
    async def test_handshake_timeout(self):
        """Test handshake timeout behavior."""
        handshake = TrustHandshake(timeout_ms=100)
        
        # This should timeout quickly
        result = await handshake.initiate(
            initiator_did="did:agentmesh:agent-a",
            responder_did="did:agentmesh:nonexistent",
            capabilities_requested=["read"],
        )
        
        # Should fail due to timeout
        assert not result.success or result.error is not None


class TestCapabilities:
    """Tests for CapabilityScope and CapabilityRegistry."""
    
    def test_capability_scope(self):
        """Test capability scope creation."""
        scope = CapabilityScope(
            name="file_access",
            resources=["file:///data/*"],
            actions=["read", "write"],
        )
        
        assert scope.name == "file_access"
        assert scope.allows("read")
        assert not scope.allows("delete")
    
    def test_capability_registry(self):
        """Test capability registry."""
        registry = CapabilityRegistry()
        
        # Register a capability
        registry.register(
            agent_did="did:agentmesh:test",
            scope=CapabilityScope(
                name="api_access",
                resources=["https://api.example.com/*"],
                actions=["get", "post"],
            ),
        )
        
        # Check capabilities
        caps = registry.get_capabilities("did:agentmesh:test")
        assert len(caps) == 1
        assert caps[0].name == "api_access"
    
    def test_capability_validation(self):
        """Test capability validation."""
        registry = CapabilityRegistry()
        
        registry.register(
            agent_did="did:agentmesh:test",
            scope=CapabilityScope(
                name="limited",
                resources=["resource:A"],
                actions=["read"],
            ),
        )
        
        # Should be allowed
        assert registry.is_allowed(
            agent_did="did:agentmesh:test",
            resource="resource:A",
            action="read",
        )
        
        # Should be denied
        assert not registry.is_allowed(
            agent_did="did:agentmesh:test",
            resource="resource:B",
            action="read",
        )
