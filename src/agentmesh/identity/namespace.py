"""
Agent Namespaces

Scoped trust boundaries for agent groups. Agents within the same namespace
communicate freely; cross-namespace interaction requires explicit rules.
Supports nested namespaces (e.g. "finance.trading" is a child of "finance").
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from agentmesh.governance.trust_policy import TrustPolicy


class AgentNamespace(BaseModel):
    """A logical grouping of agents with shared trust boundaries."""

    name: str = Field(..., description="Namespace name (e.g. 'finance.trading')")
    description: str = Field(..., description="Human-readable description")
    parent: Optional[str] = Field(
        None, description="Parent namespace name for nesting (e.g. 'finance')"
    )
    trust_policy: Optional[TrustPolicy] = Field(
        None, description="Optional trust policy governing this namespace"
    )
    members: set[str] = Field(default_factory=set, description="Agent DIDs in this namespace")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NamespaceRule(BaseModel):
    """Rule governing cross-namespace communication or delegation."""

    source_namespace: str = Field(..., description="Originating namespace")
    target_namespace: str = Field(..., description="Destination namespace")
    allowed: bool = Field(..., description="Whether communication is allowed")
    min_trust_score: Optional[int] = Field(
        None, description="Minimum trust score required (0-1000)"
    )
    require_approval: bool = Field(
        default=False, description="Whether human approval is required"
    )
