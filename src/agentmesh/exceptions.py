# Copyright (c) Agent-Mesh Contributors. All rights reserved.
# Licensed under the MIT License.
"""Centralized exception hierarchy for AgentMesh.

All AgentMesh exceptions inherit from AgentMeshError, enabling
consistent error handling across integrations and core modules.
"""


class AgentMeshError(Exception):
    """Base exception for all AgentMesh errors."""


class IdentityError(AgentMeshError):
    """Errors related to agent identity (DID, keys, credentials)."""


class TrustError(AgentMeshError):
    """Errors related to trust scoring and verification."""


class TrustVerificationError(TrustError):
    """Trust verification failed during handshake or delegation."""


class TrustViolationError(TrustError):
    """Trust policy was violated during agent interaction."""


class DelegationError(AgentMeshError):
    """Errors related to delegation chains."""


class DelegationDepthError(DelegationError):
    """Raised when delegation chain exceeds the configured max depth."""


class GovernanceError(AgentMeshError):
    """Errors related to governance policy enforcement."""


class HandshakeError(TrustError):
    """Errors during trust handshake protocol."""


class HandshakeTimeoutError(HandshakeError):
    """Raised when a trust handshake exceeds the configured timeout."""


class StorageError(AgentMeshError):
    """Errors related to storage backend operations."""


__all__ = [
    "AgentMeshError",
    "IdentityError",
    "TrustError",
    "TrustVerificationError",
    "TrustViolationError",
    "DelegationError",
    "DelegationDepthError",
    "GovernanceError",
    "HandshakeError",
    "HandshakeTimeoutError",
    "StorageError",
]
