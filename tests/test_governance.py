"""Tests for AgentMesh Governance module."""

import pytest
from datetime import datetime, timedelta
import tempfile
import json

from agentmesh.governance import (
    PolicyEngine,
    Policy,
    PolicyRule,
    ComplianceEngine,
    ComplianceFramework,
    AuditLog,
    MerkleAuditChain,
    ShadowMode,
)


class TestPolicyEngine:
    """Tests for PolicyEngine."""
    
    def test_create_engine(self):
        """Test creating policy engine."""
        engine = PolicyEngine()
        
        assert engine is not None
        assert len(engine.policies) == 0
    
    def test_load_policy(self):
        """Test loading a policy."""
        engine = PolicyEngine()
        
        policy_data = {
            "id": "test-policy",
            "name": "Test Policy",
            "enabled": True,
            "rules": [
                {
                    "id": "rule-1",
                    "action": "allow",
                    "conditions": [],
                },
            ],
        }
        
        engine.load_policy(policy_data)
        
        assert len(engine.policies) == 1
    
    def test_policy_evaluation(self):
        """Test policy evaluation."""
        engine = PolicyEngine()
        
        engine.load_policy({
            "id": "test-policy",
            "name": "Test Policy",
            "enabled": True,
            "rules": [
                {
                    "id": "block-secrets",
                    "action": "block",
                    "conditions": ["output contains 'password'"],
                },
            ],
        })
        
        # Should be blocked
        result = engine.evaluate({
            "agent_did": "did:agentmesh:test",
            "output": "The password is secret123",
        })
        
        assert result.action == "block"
    
    def test_policy_deterministic(self):
        """Test that policy evaluation is deterministic."""
        engine = PolicyEngine()
        
        engine.load_policy({
            "id": "test-policy",
            "name": "Test Policy",
            "enabled": True,
            "rules": [
                {
                    "id": "rule-1",
                    "action": "allow",
                    "conditions": ["value > 10"],
                },
            ],
        })
        
        context = {"agent_did": "did:agentmesh:test", "value": 15}
        
        # Multiple evaluations should give same result
        results = [engine.evaluate(context) for _ in range(10)]
        
        assert all(r.action == results[0].action for r in results)


class TestCompliance:
    """Tests for ComplianceEngine."""
    
    def test_create_engine(self):
        """Test creating compliance engine."""
        engine = ComplianceEngine()
        
        assert len(engine.frameworks) > 0
    
    def test_eu_ai_act_mapping(self):
        """Test EU AI Act compliance mapping."""
        engine = ComplianceEngine()
        
        controls = engine.get_controls(ComplianceFramework.EU_AI_ACT)
        
        assert len(controls) > 0
    
    def test_soc2_mapping(self):
        """Test SOC 2 compliance mapping."""
        engine = ComplianceEngine()
        
        controls = engine.get_controls(ComplianceFramework.SOC2)
        
        assert len(controls) > 0
    
    def test_compliance_report(self):
        """Test generating compliance report."""
        engine = ComplianceEngine()
        
        report = engine.generate_report(
            agent_did="did:agentmesh:test",
            framework=ComplianceFramework.SOC2,
        )
        
        assert "controls" in report
        assert "generated_at" in report


class TestAudit:
    """Tests for AuditLog and MerkleAuditChain."""
    
    def test_audit_entry(self):
        """Test creating audit entry."""
        log = AuditLog()
        
        entry_id = log.record(
            agent_did="did:agentmesh:test",
            action="policy_check",
            result="allowed",
        )
        
        assert entry_id is not None
    
    def test_audit_retrieval(self):
        """Test retrieving audit entries."""
        log = AuditLog()
        
        log.record(agent_did="did:agentmesh:test", action="action-1")
        log.record(agent_did="did:agentmesh:test", action="action-2")
        
        entries = log.get_entries(agent_did="did:agentmesh:test")
        
        assert len(entries) == 2
    
    def test_merkle_chain(self):
        """Test Merkle chain for tamper evidence."""
        chain = MerkleAuditChain()
        
        chain.append({"action": "test-1", "timestamp": datetime.utcnow().isoformat()})
        chain.append({"action": "test-2", "timestamp": datetime.utcnow().isoformat()})
        
        # Chain should be valid
        assert chain.verify()
    
    def test_merkle_tamper_detection(self):
        """Test that tampering is detected."""
        chain = MerkleAuditChain()
        
        chain.append({"action": "test-1"})
        chain.append({"action": "test-2"})
        
        # Tamper with the chain
        if chain.entries:
            chain.entries[0]["action"] = "tampered!"
        
        # Should detect tampering
        assert not chain.verify()


class TestShadowMode:
    """Tests for ShadowMode."""
    
    def test_create_shadow(self):
        """Test creating shadow mode."""
        shadow = ShadowMode()
        
        assert shadow is not None
    
    def test_shadow_simulation(self):
        """Test simulating actions in shadow mode."""
        shadow = ShadowMode()
        
        engine = PolicyEngine()
        engine.load_policy({
            "id": "test-policy",
            "name": "Test Policy",
            "enabled": True,
            "rules": [],
        })
        
        result = shadow.simulate(
            policy_engine=engine,
            context={"agent_did": "did:agentmesh:test"},
        )
        
        assert result is not None
        assert "simulated" in result or result.get("executed", False) == False
