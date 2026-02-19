package agentmesh

import (
	"testing"
)

func TestNewClient(t *testing.T) {
	client, err := NewClient("test-agent",
		WithCapabilities([]string{"read", "write"}),
	)
	if err != nil {
		t.Fatalf("NewClient: %v", err)
	}
	if client.Identity == nil {
		t.Fatal("Identity is nil")
	}
	if client.Trust == nil {
		t.Fatal("Trust is nil")
	}
	if client.Policy == nil {
		t.Fatal("Policy is nil")
	}
	if client.Audit == nil {
		t.Fatal("Audit is nil")
	}
}

func TestExecuteWithGovernanceAllow(t *testing.T) {
	client, _ := NewClient("gov-agent",
		WithPolicyRules([]PolicyRule{
			{Action: "data.read", Effect: Allow},
		}),
	)

	result, err := client.ExecuteWithGovernance("data.read", nil)
	if err != nil {
		t.Fatalf("ExecuteWithGovernance: %v", err)
	}
	if !result.Allowed {
		t.Error("expected Allowed = true")
	}
	if result.Decision != Allow {
		t.Errorf("decision = %q, want allow", result.Decision)
	}
	if result.AuditEntry == nil {
		t.Error("expected AuditEntry to be non-nil")
	}
}

func TestExecuteWithGovernanceDeny(t *testing.T) {
	client, _ := NewClient("gov-agent",
		WithPolicyRules([]PolicyRule{
			{Action: "data.delete", Effect: Deny},
		}),
	)

	result, err := client.ExecuteWithGovernance("data.delete", nil)
	if err != nil {
		t.Fatal(err)
	}
	if result.Allowed {
		t.Error("expected Allowed = false for denied action")
	}
}

func TestEndToEndGovernance(t *testing.T) {
	client, _ := NewClient("e2e-agent",
		WithCapabilities([]string{"data.read"}),
		WithPolicyRules([]PolicyRule{
			{Action: "data.read", Effect: Allow},
			{Action: "*", Effect: Deny},
		}),
	)

	// Allowed action
	r1, _ := client.ExecuteWithGovernance("data.read", nil)
	if !r1.Allowed {
		t.Error("data.read should be allowed")
	}

	// Denied action
	r2, _ := client.ExecuteWithGovernance("system.shutdown", nil)
	if r2.Allowed {
		t.Error("system.shutdown should be denied")
	}

	// Audit chain intact
	if !client.Audit.Verify() {
		t.Error("audit chain should verify")
	}

	// Trust score updated
	score := client.Trust.GetTrustScore(client.Identity.DID)
	if score.Overall == 0 {
		t.Error("trust score should be non-zero after interactions")
	}
}
