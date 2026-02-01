"""
Compliance Engine

Automated compliance mapping for:
- EU AI Act
- SOC 2
- HIPAA
- GDPR

Every action is mapped to relevant controls automatically.
"""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum


class ComplianceFramework(str, Enum):
    """Supported compliance frameworks."""
    EU_AI_ACT = "eu_ai_act"
    SOC2 = "soc2"
    HIPAA = "hipaa"
    GDPR = "gdpr"


class ComplianceControl(BaseModel):
    """A specific compliance control."""
    
    control_id: str
    framework: ComplianceFramework
    name: str
    description: str
    
    # Categorization
    category: str
    subcategory: Optional[str] = None
    
    # Requirements
    requirements: list[str] = Field(default_factory=list)
    
    # Evidence required
    evidence_types: list[str] = Field(default_factory=list)


class ComplianceMapping(BaseModel):
    """Mapping of an action to compliance controls."""
    
    action_type: str
    controls: list[str] = Field(default_factory=list)  # Control IDs
    
    # Auto-generated evidence
    evidence_generated: list[str] = Field(default_factory=list)
    
    # Manual evidence required
    evidence_required: list[str] = Field(default_factory=list)


class ComplianceViolation(BaseModel):
    """A compliance violation."""
    
    violation_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # What happened
    agent_did: str
    action_type: str
    
    # Which control was violated
    control_id: str
    framework: ComplianceFramework
    
    # Severity
    severity: Literal["critical", "high", "medium", "low"] = "medium"
    
    # Details
    description: str
    evidence: dict = Field(default_factory=dict)
    
    # Remediation
    remediated: bool = False
    remediated_at: Optional[datetime] = None
    remediation_notes: Optional[str] = None


class ComplianceReport(BaseModel):
    """Compliance audit report."""
    
    report_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Scope
    framework: ComplianceFramework
    period_start: datetime
    period_end: datetime
    
    # Organization
    organization_id: Optional[str] = None
    agents_covered: list[str] = Field(default_factory=list)
    
    # Summary
    total_controls: int = 0
    controls_met: int = 0
    controls_partial: int = 0
    controls_failed: int = 0
    compliance_score: float = 0.0  # 0-100
    
    # Violations
    violations: list[ComplianceViolation] = Field(default_factory=list)
    
    # Evidence
    evidence_items: int = 0
    
    # Recommendations
    recommendations: list[str] = Field(default_factory=list)


class ComplianceEngine:
    """
    Automated compliance mapping and reporting.
    
    Maps every agent action to relevant compliance controls
    and generates audit-ready reports.
    """
    
    def __init__(self, frameworks: Optional[list[ComplianceFramework]] = None):
        self.frameworks = frameworks or [ComplianceFramework.SOC2]
        self._controls: dict[str, ComplianceControl] = {}
        self._mappings: dict[str, ComplianceMapping] = {}
        self._violations: list[ComplianceViolation] = []
        
        # Load default controls
        self._load_default_controls()
    
    def _load_default_controls(self) -> None:
        """Load default compliance controls for enabled frameworks."""
        
        # SOC 2 Controls
        if ComplianceFramework.SOC2 in self.frameworks:
            self._add_control(ComplianceControl(
                control_id="SOC2-CC6.1",
                framework=ComplianceFramework.SOC2,
                name="Logical Access Security",
                description="Logical access security software, infrastructure, and architectures have been implemented",
                category="Common Criteria",
                requirements=[
                    "Identity verification",
                    "Access logging",
                    "Credential management",
                ],
                evidence_types=["access_logs", "identity_records"],
            ))
            self._add_control(ComplianceControl(
                control_id="SOC2-CC7.2",
                framework=ComplianceFramework.SOC2,
                name="System Monitoring",
                description="System components are monitored for anomalies",
                category="Common Criteria",
                requirements=[
                    "Activity monitoring",
                    "Anomaly detection",
                    "Alerting",
                ],
                evidence_types=["monitoring_logs", "alerts"],
            ))
        
        # HIPAA Controls
        if ComplianceFramework.HIPAA in self.frameworks:
            self._add_control(ComplianceControl(
                control_id="HIPAA-164.312(a)(1)",
                framework=ComplianceFramework.HIPAA,
                name="Access Control",
                description="Implement technical policies and procedures for electronic PHI access",
                category="Technical Safeguards",
                requirements=[
                    "Unique user identification",
                    "Automatic logoff",
                    "Encryption",
                ],
                evidence_types=["access_logs", "encryption_records"],
            ))
            self._add_control(ComplianceControl(
                control_id="HIPAA-164.312(b)",
                framework=ComplianceFramework.HIPAA,
                name="Audit Controls",
                description="Implement hardware, software, and procedural mechanisms for audit trails",
                category="Technical Safeguards",
                requirements=[
                    "Audit logging",
                    "Log retention",
                    "Log review",
                ],
                evidence_types=["audit_logs"],
            ))
        
        # EU AI Act Controls
        if ComplianceFramework.EU_AI_ACT in self.frameworks:
            self._add_control(ComplianceControl(
                control_id="EUAI-ART9",
                framework=ComplianceFramework.EU_AI_ACT,
                name="Risk Management System",
                description="High-risk AI systems shall have a risk management system",
                category="High-Risk AI",
                requirements=[
                    "Risk identification",
                    "Risk mitigation",
                    "Continuous monitoring",
                ],
                evidence_types=["risk_assessments", "mitigation_logs"],
            ))
            self._add_control(ComplianceControl(
                control_id="EUAI-ART13",
                framework=ComplianceFramework.EU_AI_ACT,
                name="Transparency",
                description="High-risk AI systems shall be designed to allow appropriate transparency",
                category="High-Risk AI",
                requirements=[
                    "Explainability",
                    "Documentation",
                    "User notification",
                ],
                evidence_types=["decision_logs", "explanations"],
            ))
        
        # GDPR Controls
        if ComplianceFramework.GDPR in self.frameworks:
            self._add_control(ComplianceControl(
                control_id="GDPR-ART5",
                framework=ComplianceFramework.GDPR,
                name="Data Processing Principles",
                description="Personal data shall be processed lawfully, fairly and transparently",
                category="Principles",
                requirements=[
                    "Lawful basis",
                    "Purpose limitation",
                    "Data minimization",
                ],
                evidence_types=["processing_records", "consent_logs"],
            ))
            self._add_control(ComplianceControl(
                control_id="GDPR-ART22",
                framework=ComplianceFramework.GDPR,
                name="Automated Decision-Making",
                description="Right not to be subject to solely automated decision-making",
                category="Individual Rights",
                requirements=[
                    "Human oversight",
                    "Explanation of logic",
                    "Right to contest",
                ],
                evidence_types=["decision_logs", "human_review_records"],
            ))
        
        # Set up default mappings
        self._setup_default_mappings()
    
    def _setup_default_mappings(self) -> None:
        """Set up default action-to-control mappings."""
        
        # Agent registration
        self._mappings["agent_registration"] = ComplianceMapping(
            action_type="agent_registration",
            controls=["SOC2-CC6.1", "HIPAA-164.312(a)(1)"],
            evidence_generated=["identity_record", "registration_log"],
        )
        
        # Data access
        self._mappings["data_access"] = ComplianceMapping(
            action_type="data_access",
            controls=["SOC2-CC6.1", "HIPAA-164.312(b)", "GDPR-ART5"],
            evidence_generated=["access_log", "data_classification"],
        )
        
        # Automated decision
        self._mappings["automated_decision"] = ComplianceMapping(
            action_type="automated_decision",
            controls=["EUAI-ART13", "GDPR-ART22"],
            evidence_generated=["decision_log", "explanation"],
            evidence_required=["human_review"] if ComplianceFramework.GDPR in self.frameworks else [],
        )
    
    def _add_control(self, control: ComplianceControl) -> None:
        """Add a control to the registry."""
        self._controls[control.control_id] = control
    
    def map_action(self, action_type: str) -> Optional[ComplianceMapping]:
        """Get compliance mapping for an action type."""
        return self._mappings.get(action_type)
    
    def check_compliance(
        self,
        agent_did: str,
        action_type: str,
        context: dict,
    ) -> list[ComplianceViolation]:
        """
        Check an action for compliance violations.
        
        Returns list of any violations found.
        """
        violations = []
        mapping = self.map_action(action_type)
        
        if not mapping:
            return violations
        
        for control_id in mapping.controls:
            control = self._controls.get(control_id)
            if not control:
                continue
            
            # Check requirements
            violation = self._check_control(agent_did, action_type, control, context)
            if violation:
                violations.append(violation)
                self._violations.append(violation)
        
        return violations
    
    def _check_control(
        self,
        agent_did: str,
        action_type: str,
        control: ComplianceControl,
        context: dict,
    ) -> Optional[ComplianceViolation]:
        """Check if an action violates a specific control."""
        import uuid
        
        # Framework-specific checks
        if control.framework == ComplianceFramework.HIPAA:
            # Check for PHI handling
            if context.get("data_type") == "phi" and not context.get("encrypted"):
                return ComplianceViolation(
                    violation_id=f"viol_{uuid.uuid4().hex[:12]}",
                    agent_did=agent_did,
                    action_type=action_type,
                    control_id=control.control_id,
                    framework=control.framework,
                    severity="high",
                    description="PHI data accessed without encryption",
                    evidence={"data_type": "phi", "encrypted": False},
                )
        
        if control.framework == ComplianceFramework.GDPR:
            # Check for consent
            if context.get("personal_data") and not context.get("consent_verified"):
                return ComplianceViolation(
                    violation_id=f"viol_{uuid.uuid4().hex[:12]}",
                    agent_did=agent_did,
                    action_type=action_type,
                    control_id=control.control_id,
                    framework=control.framework,
                    severity="high",
                    description="Personal data processed without verified consent",
                    evidence={"personal_data": True, "consent": False},
                )
        
        return None
    
    def generate_report(
        self,
        framework: ComplianceFramework,
        period_start: datetime,
        period_end: datetime,
        agent_ids: Optional[list[str]] = None,
    ) -> ComplianceReport:
        """Generate a compliance report."""
        import uuid
        
        # Filter violations
        violations = [
            v for v in self._violations
            if v.framework == framework
            and period_start <= v.timestamp <= period_end
            and (not agent_ids or v.agent_did in agent_ids)
        ]
        
        # Get controls for framework
        framework_controls = [
            c for c in self._controls.values()
            if c.framework == framework
        ]
        
        # Calculate compliance score
        violated_controls = set(v.control_id for v in violations)
        total = len(framework_controls)
        failed = len(violated_controls)
        met = total - failed
        
        score = (met / total * 100) if total > 0 else 100.0
        
        # Generate recommendations
        recommendations = []
        for v in violations:
            if not v.remediated:
                recommendations.append(
                    f"Remediate {v.control_id}: {v.description}"
                )
        
        return ComplianceReport(
            report_id=f"report_{uuid.uuid4().hex[:12]}",
            framework=framework,
            period_start=period_start,
            period_end=period_end,
            agents_covered=agent_ids or [],
            total_controls=total,
            controls_met=met,
            controls_failed=failed,
            compliance_score=score,
            violations=violations,
            recommendations=recommendations[:10],  # Top 10
        )
    
    def remediate_violation(
        self,
        violation_id: str,
        notes: str,
    ) -> bool:
        """Mark a violation as remediated."""
        for v in self._violations:
            if v.violation_id == violation_id:
                v.remediated = True
                v.remediated_at = datetime.utcnow()
                v.remediation_notes = notes
                return True
        return False
    
    def get_violations(
        self,
        framework: Optional[ComplianceFramework] = None,
        agent_did: Optional[str] = None,
        remediated: Optional[bool] = None,
    ) -> list[ComplianceViolation]:
        """Get violations with optional filters."""
        violations = self._violations
        
        if framework:
            violations = [v for v in violations if v.framework == framework]
        
        if agent_did:
            violations = [v for v in violations if v.agent_did == agent_did]
        
        if remediated is not None:
            violations = [v for v in violations if v.remediated == remediated]
        
        return violations
