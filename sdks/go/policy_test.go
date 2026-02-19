package agentmesh

import (
	"os"
	"path/filepath"
	"testing"
)

func TestEvaluateExactMatch(t *testing.T) {
	pe := NewPolicyEngine([]PolicyRule{
		{Action: "data.read", Effect: Allow},
	})
	if d := pe.Evaluate("data.read", nil); d != Allow {
		t.Errorf("decision = %q, want allow", d)
	}
}

func TestEvaluateWildcard(t *testing.T) {
	pe := NewPolicyEngine([]PolicyRule{
		{Action: "data.*", Effect: Allow},
	})
	if d := pe.Evaluate("data.write", nil); d != Allow {
		t.Errorf("decision = %q, want allow", d)
	}
}

func TestEvaluateGlobalWildcard(t *testing.T) {
	pe := NewPolicyEngine([]PolicyRule{
		{Action: "*", Effect: Review},
	})
	if d := pe.Evaluate("anything", nil); d != Review {
		t.Errorf("decision = %q, want review", d)
	}
}

func TestEvaluateDefaultDeny(t *testing.T) {
	pe := NewPolicyEngine(nil)
	if d := pe.Evaluate("data.read", nil); d != Deny {
		t.Errorf("decision = %q, want deny (default)", d)
	}
}

func TestEvaluateConditions(t *testing.T) {
	pe := NewPolicyEngine([]PolicyRule{
		{Action: "data.read", Effect: Allow, Conditions: map[string]interface{}{"role": "admin"}},
	})

	if d := pe.Evaluate("data.read", map[string]interface{}{"role": "admin"}); d != Allow {
		t.Errorf("decision with matching condition = %q, want allow", d)
	}
	if d := pe.Evaluate("data.read", map[string]interface{}{"role": "guest"}); d != Deny {
		t.Errorf("decision with non-matching condition = %q, want deny", d)
	}
}

func TestEvaluateFirstMatchWins(t *testing.T) {
	pe := NewPolicyEngine([]PolicyRule{
		{Action: "data.read", Effect: Deny},
		{Action: "data.read", Effect: Allow},
	})
	if d := pe.Evaluate("data.read", nil); d != Deny {
		t.Errorf("first-match should win, got %q", d)
	}
}

func TestLoadFromYAML(t *testing.T) {
	dir := t.TempDir()
	yamlContent := `rules:
  - action: "file.read"
    effect: "allow"
  - action: "file.delete"
    effect: "deny"
`
	path := filepath.Join(dir, "policy.yaml")
	if err := os.WriteFile(path, []byte(yamlContent), 0644); err != nil {
		t.Fatal(err)
	}

	pe := NewPolicyEngine(nil)
	if err := pe.LoadFromYAML(path); err != nil {
		t.Fatalf("LoadFromYAML: %v", err)
	}

	if d := pe.Evaluate("file.read", nil); d != Allow {
		t.Errorf("YAML rule: decision = %q, want allow", d)
	}
	if d := pe.Evaluate("file.delete", nil); d != Deny {
		t.Errorf("YAML rule: decision = %q, want deny", d)
	}
}
