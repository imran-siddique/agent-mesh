package agentmesh

import (
	"testing"
)

func TestGenerateIdentity(t *testing.T) {
	id, err := GenerateIdentity("agent-1", []string{"read", "write"})
	if err != nil {
		t.Fatalf("GenerateIdentity: %v", err)
	}
	if id.DID != "did:agentmesh:agent-1" {
		t.Errorf("DID = %q, want did:agentmesh:agent-1", id.DID)
	}
	if len(id.PublicKey) != 32 {
		t.Errorf("PublicKey length = %d, want 32", len(id.PublicKey))
	}
	if len(id.Capabilities) != 2 {
		t.Errorf("Capabilities length = %d, want 2", len(id.Capabilities))
	}
}

func TestSignAndVerify(t *testing.T) {
	id, err := GenerateIdentity("signer", nil)
	if err != nil {
		t.Fatal(err)
	}

	data := []byte("hello agent mesh")
	sig, err := id.Sign(data)
	if err != nil {
		t.Fatalf("Sign: %v", err)
	}
	if !id.Verify(data, sig) {
		t.Error("Verify returned false for valid signature")
	}
	if id.Verify([]byte("tampered"), sig) {
		t.Error("Verify returned true for tampered data")
	}
}

func TestSignWithoutPrivateKey(t *testing.T) {
	id := &AgentIdentity{DID: "did:agentmesh:nopk"}
	_, err := id.Sign([]byte("data"))
	if err == nil {
		t.Error("expected error when signing without private key")
	}
}

func TestJSONRoundTrip(t *testing.T) {
	id, _ := GenerateIdentity("json-agent", []string{"cap1"})
	data, err := id.ToJSON()
	if err != nil {
		t.Fatalf("ToJSON: %v", err)
	}

	restored, err := FromJSON(data)
	if err != nil {
		t.Fatalf("FromJSON: %v", err)
	}
	if restored.DID != id.DID {
		t.Errorf("DID mismatch: %q vs %q", restored.DID, id.DID)
	}
	if len(restored.PublicKey) != len(id.PublicKey) {
		t.Error("PublicKey length mismatch after round-trip")
	}
}
