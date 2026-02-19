package agentmesh

import (
	"os"
	"strings"
	"sync"

	"gopkg.in/yaml.v3"
)

// PolicyRule defines a single governance rule.
type PolicyRule struct {
	Action     string                 `json:"action" yaml:"action"`
	Effect     PolicyDecision         `json:"effect" yaml:"effect"`
	Conditions map[string]interface{} `json:"conditions,omitempty" yaml:"conditions,omitempty"`
}

// PolicyEngine evaluates actions against a set of rules.
type PolicyEngine struct {
	mu    sync.RWMutex
	rules []PolicyRule
}

// NewPolicyEngine creates a PolicyEngine with the supplied rules.
func NewPolicyEngine(rules []PolicyRule) *PolicyEngine {
	return &PolicyEngine{rules: rules}
}

// Evaluate returns the decision for the given action and context.
// Rules are evaluated in order; first match wins. Default is Deny.
func (pe *PolicyEngine) Evaluate(action string, context map[string]interface{}) PolicyDecision {
	pe.mu.RLock()
	defer pe.mu.RUnlock()

	for _, rule := range pe.rules {
		if matchAction(rule.Action, action) && matchConditions(rule.Conditions, context) {
			return rule.Effect
		}
	}
	return Deny
}

// LoadFromYAML loads rules from a YAML file, appending to existing rules.
func (pe *PolicyEngine) LoadFromYAML(path string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}

	var loaded struct {
		Rules []PolicyRule `yaml:"rules"`
	}
	if err := yaml.Unmarshal(data, &loaded); err != nil {
		return err
	}

	pe.mu.Lock()
	defer pe.mu.Unlock()
	pe.rules = append(pe.rules, loaded.Rules...)
	return nil
}

func matchAction(pattern, action string) bool {
	if pattern == "*" {
		return true
	}
	if strings.HasSuffix(pattern, ".*") {
		prefix := strings.TrimSuffix(pattern, ".*")
		return strings.HasPrefix(action, prefix+".")
	}
	return pattern == action
}

func matchConditions(conditions map[string]interface{}, context map[string]interface{}) bool {
	for key, expected := range conditions {
		actual, ok := context[key]
		if !ok {
			return false
		}
		if !valuesEqual(expected, actual) {
			return false
		}
	}
	return true
}

func valuesEqual(a, b interface{}) bool {
	switch av := a.(type) {
	case string:
		bv, ok := b.(string)
		return ok && av == bv
	case float64:
		bv, ok := b.(float64)
		return ok && av == bv
	case bool:
		bv, ok := b.(bool)
		return ok && av == bv
	default:
		return false
	}
}
