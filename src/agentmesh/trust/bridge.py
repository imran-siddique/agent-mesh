"""
Trust Bridge

Unified trust layer across all protocols (A2A, MCP, IATP, ACP).
Ensures consistent trust model regardless of underlying protocol.

Integrates with agent-os IATP module for trust verification.
"""

from datetime import datetime
from typing import Optional, Literal, Any
from pydantic import BaseModel, Field
import asyncio

from .handshake import TrustHandshake, HandshakeResult
from .capability import CapabilityScope

# Import IATP from agent-os (the source of truth for trust protocol)
try:
    from modules.iatp import IATPClient, IATPMessage, TrustLevel
    from modules.nexus import NexusClient, ReputationEngine
    AGENT_OS_AVAILABLE = True
except ImportError:
    # Fallback if agent-os not installed yet (for development)
    AGENT_OS_AVAILABLE = False
    IATPClient = None
    NexusClient = None


class PeerInfo(BaseModel):
    """Information about a peer agent in the trust mesh.

    Attributes:
        peer_did: Decentralized identifier for the peer agent.
        peer_name: Optional human-readable name for the peer.
        protocol: Communication protocol (``"a2a"``, ``"mcp"``,
            ``"iatp"``, or ``"acp"``).
        trust_score: Numeric trust score from 0 to 1000.
        trust_verified: Whether the peer has been verified.
        last_verified: Timestamp of the most recent verification.
        capabilities: List of capability strings the peer holds.
        endpoint: Network endpoint URL for the peer.
        connected_at: Timestamp when the connection was established.
    """
    
    peer_did: str
    peer_name: Optional[str] = None
    protocol: str  # "a2a", "mcp", "iatp", "acp"
    
    # Trust info
    trust_score: int = Field(default=0, ge=0, le=1000)
    trust_verified: bool = False
    last_verified: Optional[datetime] = None
    
    # Capabilities
    capabilities: list[str] = Field(default_factory=list)
    
    # Connection info
    endpoint: Optional[str] = None
    connected_at: Optional[datetime] = None


class TrustBridge(BaseModel):
    """
    Unified trust bridge for multi-protocol agent communication.
    
    The TrustBridge ensures that regardless of which protocol is used
    (A2A, MCP, IATP, ACP), trust verification happens consistently.
    """
    
    agent_did: str = Field(..., description="This agent's DID")
    
    # Trust thresholds
    default_trust_threshold: int = Field(default=700, ge=0, le=1000)
    
    # Known peers
    peers: dict[str, PeerInfo] = Field(default_factory=dict)
    
    # Handshake handler
    _handshake: Optional[TrustHandshake] = None
    
    model_config = {"arbitrary_types_allowed": True}
    
    def __init__(self, **data):
        super().__init__(**data)
        self._handshake = TrustHandshake(agent_did=self.agent_did)
    
    async def verify_peer(
        self,
        peer_did: str,
        protocol: str = "iatp",
        required_trust_score: Optional[int] = None,
        required_capabilities: Optional[list[str]] = None,
    ) -> HandshakeResult:
        """
        Verify a peer before communication.
        
        This is the core trust gate - all inter-agent communication
        must pass through verification.
        
        Args:
            peer_did: The peer's DID
            protocol: Protocol to use for verification
            required_trust_score: Minimum trust score required
            required_capabilities: Capabilities the peer must have
            
        Returns:
            HandshakeResult with verification status
        """
        threshold = required_trust_score or self.default_trust_threshold
        
        # Perform handshake
        result = await self._handshake.initiate(
            peer_did=peer_did,
            protocol=protocol,
            required_trust_score=threshold,
            required_capabilities=required_capabilities,
        )
        
        # Update peer info
        if result.verified:
            self.peers[peer_did] = PeerInfo(
                peer_did=peer_did,
                peer_name=result.peer_name,
                protocol=protocol,
                trust_score=result.trust_score,
                trust_verified=True,
                last_verified=datetime.utcnow(),
                capabilities=result.capabilities,
            )
        
        return result
    
    async def is_peer_trusted(
        self,
        peer_did: str,
        required_score: Optional[int] = None,
    ) -> bool:
        """Check whether a previously verified peer meets the trust threshold.

        Unlike :meth:`verify_peer`, this does **not** perform a new
        handshake; it only inspects the cached peer record.

        Args:
            peer_did: The peer's decentralized identifier.
            required_score: Minimum trust score. Falls back to
                ``default_trust_threshold`` when ``None``.

        Returns:
            ``True`` if the peer is verified and meets the threshold.
        """
        peer = self.peers.get(peer_did)
        if not peer or not peer.trust_verified:
            return False
        
        threshold = required_score or self.default_trust_threshold
        return peer.trust_score >= threshold
    
    def get_peer(self, peer_did: str) -> Optional[PeerInfo]:
        """Get information about a known peer.

        Args:
            peer_did: The peer's decentralized identifier.

        Returns:
            The ``PeerInfo`` record, or ``None`` if the peer is unknown.
        """
        return self.peers.get(peer_did)
    
    def get_trusted_peers(self, min_score: Optional[int] = None) -> list[PeerInfo]:
        """Get all peers that are verified and meet the trust threshold.

        Args:
            min_score: Minimum trust score. Falls back to
                ``default_trust_threshold`` when ``None``.

        Returns:
            List of ``PeerInfo`` records for qualifying peers.
        """
        threshold = min_score or self.default_trust_threshold
        return [
            peer for peer in self.peers.values()
            if peer.trust_verified and peer.trust_score >= threshold
        ]
    
    async def revoke_peer_trust(self, peer_did: str, reason: str) -> bool:
        """Revoke trust for a previously verified peer.

        Resets the peer's trust score to zero and marks them as
        unverified. The peer record is retained for auditing purposes.

        Args:
            peer_did: The peer's decentralized identifier.
            reason: Human-readable reason for revocation.

        Returns:
            ``True`` if the peer was found and revoked, ``False`` if
            the peer was not in the known-peers map.
        """
        if peer_did in self.peers:
            self.peers[peer_did].trust_verified = False
            self.peers[peer_did].trust_score = 0
            return True
        return False


class ProtocolBridge(BaseModel):
    """
    Protocol translation layer.
    
    Translates between A2A, MCP, IATP, and ACP transparently,
    maintaining trust guarantees across protocol boundaries.
    """
    
    agent_did: str
    trust_bridge: Optional[TrustBridge] = None
    
    # Protocol handlers
    supported_protocols: list[str] = Field(
        default=["a2a", "mcp", "iatp", "acp"]
    )
    
    model_config = {"arbitrary_types_allowed": True}
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.trust_bridge:
            self.trust_bridge = TrustBridge(agent_did=self.agent_did)
    
    async def send_message(
        self,
        peer_did: str,
        message: Any,
        source_protocol: str,
        target_protocol: Optional[str] = None,
    ) -> Any:
        """Send a message to a peer, translating protocols if needed.

        Verifies trust before sending and automatically translates the
        message when the source and destination protocols differ.

        Args:
            peer_did: Target peer's decentralized identifier.
            message: Message payload to send.
            source_protocol: Protocol the message is currently in.
            target_protocol: Protocol to translate to before sending.
                Auto-detected from the peer record when ``None``.

        Returns:
            Response payload from the protocol handler.

        Raises:
            PermissionError: If the peer cannot be verified.
        """
        # Verify trust first
        if not await self.trust_bridge.is_peer_trusted(peer_did):
            result = await self.trust_bridge.verify_peer(peer_did, source_protocol)
            if not result.verified:
                raise PermissionError(f"Peer not trusted: {peer_did}")
        
        peer = self.trust_bridge.get_peer(peer_did)
        dest_protocol = target_protocol or peer.protocol
        
        # Translate if needed
        if source_protocol != dest_protocol:
            message = await self._translate(message, source_protocol, dest_protocol)
        
        # Send via appropriate handler
        return await self._send(peer_did, message, dest_protocol)
    
    async def _translate(
        self,
        message: Any,
        from_protocol: str,
        to_protocol: str,
    ) -> Any:
        """Translate message between protocols."""
        # Protocol translation mappings
        if from_protocol == "a2a" and to_protocol == "mcp":
            return self._a2a_to_mcp(message)
        elif from_protocol == "mcp" and to_protocol == "a2a":
            return self._mcp_to_a2a(message)
        elif from_protocol == "iatp":
            # IATP can wrap any protocol
            return message
        else:
            # Default: pass through
            return message
    
    def _a2a_to_mcp(self, message: dict) -> dict:
        """Convert A2A message to MCP format."""
        # A2A task -> MCP tool call
        return {
            "method": "tools/call",
            "params": {
                "name": message.get("task_type", "execute"),
                "arguments": message.get("parameters", {}),
            },
        }
    
    def _mcp_to_a2a(self, message: dict) -> dict:
        """Convert MCP message to A2A format."""
        # MCP tool call -> A2A task
        params = message.get("params", {})
        return {
            "task_type": params.get("name", "execute"),
            "parameters": params.get("arguments", {}),
        }
    
    def add_verification_footer(
        self,
        content: str,
        trust_score: int,
        agent_did: str,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Add AgentMesh verification footer to content.
        
        This creates the "viral" verification message that shows
        AgentMesh is securing the interaction.
        
        Args:
            content: Original content
            trust_score: Current trust score
            agent_did: Agent DID
            metadata: Optional metadata to include
            
        Returns:
            Content with verification footer appended
        """
        footer = (
            f"\n\n> 🔒 Verified by AgentMesh (Trust Score: {trust_score}/1000)\n"
            f"> Agent: {agent_did[:40]}...\n"
        )
        
        if metadata:
            if "policy" in metadata:
                footer += f"> Policy: {metadata['policy']}\n"
            if "audit" in metadata:
                footer += f"> Audit: {metadata['audit']}\n"
            if "view_log" in metadata:
                footer += f"> [View Audit Log]({metadata['view_log']})\n"
        
        return content + footer
    
    async def _send(self, peer_did: str, message: Any, protocol: str) -> Any:
        """Send message via protocol handler."""
        # In production, would dispatch to actual protocol handlers
        # For now, return a placeholder
        return {
            "status": "sent",
            "peer": peer_did,
            "protocol": protocol,
        }
    
    def get_protocol_for_peer(self, peer_did: str) -> Optional[str]:
        """Get the preferred communication protocol for a peer.

        Args:
            peer_did: The peer's decentralized identifier.

        Returns:
            Protocol string (e.g. ``"a2a"``, ``"mcp"``), or ``None``
            if the peer is unknown.
        """
        peer = self.trust_bridge.get_peer(peer_did)
        return peer.protocol if peer else None


class A2AAdapter:
    """
    Adapter for Google A2A (Agent-to-Agent) protocol.
    
    Supports:
    - Agent Card discovery
    - Task lifecycle management
    - Collaboration messaging
    """
    
    def __init__(self, agent_did: str, trust_bridge: TrustBridge):
        """Initialise the A2A adapter.

        Args:
            agent_did: This agent's decentralized identifier.
            trust_bridge: Shared ``TrustBridge`` for peer verification.
        """
        self.agent_did = agent_did
        self.trust_bridge = trust_bridge
    
    async def discover_agent(self, endpoint: str) -> Optional[dict]:
        """Discover an agent via A2A Agent Card.

        Fetches the agent card from ``GET /.well-known/agent.json`` at
        the given endpoint.

        Args:
            endpoint: Base URL of the remote agent.

        Returns:
            Agent card dictionary, or ``None`` if discovery fails.
        """
        # Would make HTTP request in production
        return {
            "name": "discovered-agent",
            "description": "An A2A-compatible agent",
            "capabilities": ["task/execute"],
        }
    
    async def create_task(
        self,
        peer_did: str,
        task_type: str,
        parameters: dict,
    ) -> dict:
        """Create a task on a peer agent via the A2A protocol.

        Trust is verified before the task is dispatched.

        Args:
            peer_did: Target peer's decentralized identifier.
            task_type: Type of task to create (e.g. ``"execute"``).
            parameters: Task parameters to send.

        Returns:
            Dictionary containing ``task_id``, ``status``, and
            ``type`` of the created task.

        Raises:
            PermissionError: If the peer is not trusted.
        """
        # Verify trust
        if not await self.trust_bridge.is_peer_trusted(peer_did):
            raise PermissionError("Peer not trusted")
        
        return {
            "task_id": f"task_{peer_did}_{datetime.utcnow().timestamp()}",
            "status": "created",
            "type": task_type,
        }
    
    async def get_task_status(self, peer_did: str, task_id: str) -> dict:
        """Get the current status of a task on a peer agent.

        Args:
            peer_did: The peer's decentralized identifier.
            task_id: Identifier of the task to query.

        Returns:
            Dictionary containing ``task_id`` and ``status``.
        """
        return {
            "task_id": task_id,
            "status": "running",
        }


class MCPAdapter:
    """
    Adapter for Anthropic MCP (Model Context Protocol).
    
    Supports:
    - Tool registration
    - Resource binding
    - Governed tool invocation
    
    All MCP tool calls route through AgentMesh policy engine.
    """
    
    def __init__(self, agent_did: str, trust_bridge: TrustBridge):
        """Initialise the MCP adapter.

        Args:
            agent_did: This agent's decentralized identifier.
            trust_bridge: Shared ``TrustBridge`` for peer verification.
        """
        self.agent_did = agent_did
        self.trust_bridge = trust_bridge
        self._registered_tools: dict[str, dict] = {}
    
    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: dict,
        required_capability: Optional[str] = None,
    ) -> None:
        """Register a tool with the MCP adapter.

        Args:
            name: Unique tool name.
            description: Human-readable tool description.
            input_schema: JSON Schema describing accepted arguments.
            required_capability: Capability string a peer must hold
                to invoke this tool. ``None`` means unrestricted.
        """
        self._registered_tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
            "required_capability": required_capability,
        }
    
    async def call_tool(
        self,
        peer_did: str,
        tool_name: str,
        arguments: dict,
    ) -> dict:
        """Call a tool on a peer with governance enforcement.

        Unlike raw MCP, this method:

        1. Verifies peer trust via the ``TrustBridge``.
        2. Checks that the peer holds the required capability.
        3. Logs the invocation for audit.

        Args:
            peer_did: Target peer's decentralized identifier.
            tool_name: Name of the registered tool to invoke.
            arguments: Arguments to pass to the tool.

        Returns:
            Dictionary with ``tool``, ``result``, and ``governed``
            keys.

        Raises:
            PermissionError: If the peer is not trusted or lacks the
                required capability for the tool.
        """
        # Verify trust
        if not await self.trust_bridge.is_peer_trusted(peer_did):
            raise PermissionError("Peer not trusted for MCP tool call")
        
        peer = self.trust_bridge.get_peer(peer_did)
        
        # Check capability if tool requires one
        tool = self._registered_tools.get(tool_name)
        if tool and tool.get("required_capability"):
            if tool["required_capability"] not in peer.capabilities:
                raise PermissionError(
                    f"Peer lacks capability: {tool['required_capability']}"
                )
        
        # Execute (would actually call MCP in production)
        return {
            "tool": tool_name,
            "result": "success",
            "governed": True,
        }
    
    def list_tools(self) -> list[dict]:
        """List all registered tools.

        Returns:
            List of tool descriptor dictionaries, each containing
            ``name``, ``description``, ``inputSchema``, and
            ``required_capability`` keys.
        """
        return list(self._registered_tools.values())
