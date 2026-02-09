"""
Governance & Compliance Plane (Layer 3)

Declarative policy engine with automated compliance mapping.
Tamper-evident audit logs with Merkle-chain hashing.
"""

from .policy import PolicyEngine, Policy, PolicyRule, PolicyDecision
from .compliance import ComplianceEngine, ComplianceFramework, ComplianceReport
from .audit import AuditLog, AuditEntry, MerkleAuditChain
from .persistent_audit import PersistentAuditLog
from .shadow import ShadowMode, ShadowResult
from .opa import OPAEvaluator, OPADecision, load_rego_into_engine

__all__ = [
    "PolicyEngine",
    "Policy",
    "PolicyRule",
    "PolicyDecision",
    "ComplianceEngine",
    "ComplianceFramework",
    "ComplianceReport",
    "AuditLog",
    "AuditEntry",
    "MerkleAuditChain",
    "PersistentAuditLog",
    "ShadowMode",
    "ShadowResult",
    "OPAEvaluator",
    "OPADecision",
    "load_rego_into_engine",
]
