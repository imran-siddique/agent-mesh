"""
AgentMesh Integrations
======================

Protocol and framework integrations for A2A, MCP, LangGraph, Swarm,
Langflow, Flowise, and Haystack.
"""

from .a2a import A2AAgentCard, A2ATrustProvider
from .mcp import TrustGatedMCPServer, TrustGatedMCPClient
from .langgraph import TrustedGraphNode, TrustCheckpoint
from .swarm import TrustedSwarm, TrustPolicy, TrustedAgent, HandoffVerifier
from .langflow import TrustGatedFlow, TrustVerificationComponent, IdentityComponent
from .flowise import TrustGatedFlowiseClient, FlowiseNodeIdentity, FlowiseTrustPolicy
from .haystack import TrustedPipeline, TrustGateComponent, TrustAgentComponent
from .http_middleware import TrustMiddleware, TrustConfig

__all__ = [
    # A2A
    "A2AAgentCard",
    "A2ATrustProvider",
    # MCP
    "TrustGatedMCPServer",
    "TrustGatedMCPClient",
    # LangGraph
    "TrustedGraphNode",
    "TrustCheckpoint",
    # Swarm
    "TrustedSwarm",
    "TrustPolicy",
    "TrustedAgent",
    "HandoffVerifier",
    # Langflow
    "TrustGatedFlow",
    "TrustVerificationComponent",
    "IdentityComponent",
    # Flowise
    "TrustGatedFlowiseClient",
    "FlowiseNodeIdentity",
    "FlowiseTrustPolicy",
    # Haystack
    "TrustedPipeline",
    "TrustGateComponent",
    "TrustAgentComponent",
    # HTTP Middleware
    "TrustMiddleware",
    "TrustConfig",
]
