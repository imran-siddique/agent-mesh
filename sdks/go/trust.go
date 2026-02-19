package agentmesh

import (
	"math"
	"sync"
)

// TrustScore represents an agent's current trust standing.
type TrustScore struct {
	Overall    float64            `json:"overall"`
	Dimensions map[string]float64 `json:"dimensions"`
	Tier       string             `json:"tier"`
}

type scoreState struct {
	score       float64
	interactions int
}

// TrustManager tracks and updates per-agent trust scores.
type TrustManager struct {
	mu     sync.RWMutex
	config TrustConfig
	scores map[string]*scoreState
}

// NewTrustManager creates a TrustManager with the given config.
func NewTrustManager(config TrustConfig) *TrustManager {
	return &TrustManager{
		config: config,
		scores: make(map[string]*scoreState),
	}
}

// VerifyPeer verifies a peer's identity and returns the current trust score.
func (tm *TrustManager) VerifyPeer(peerID string, peerIdentity *AgentIdentity) (*TrustVerificationResult, error) {
	verified := peerIdentity != nil && peerIdentity.PublicKey != nil && len(peerIdentity.PublicKey) == 32
	score := tm.GetTrustScore(peerID)
	return &TrustVerificationResult{
		PeerID:   peerID,
		Verified: verified,
		Score:    score,
	}, nil
}

// GetTrustScore returns the current trust score for an agent.
func (tm *TrustManager) GetTrustScore(agentID string) TrustScore {
	tm.mu.RLock()
	defer tm.mu.RUnlock()

	s, ok := tm.scores[agentID]
	if !ok {
		return TrustScore{
			Overall:    tm.config.InitialScore,
			Dimensions: map[string]float64{"reliability": tm.config.InitialScore},
			Tier:       tm.tierFor(tm.config.InitialScore),
		}
	}

	return TrustScore{
		Overall:    s.score,
		Dimensions: map[string]float64{"reliability": s.score},
		Tier:       tm.tierFor(s.score),
	}
}

// RecordSuccess increases an agent's trust score with decay.
func (tm *TrustManager) RecordSuccess(agentID string, reward float64) {
	tm.mu.Lock()
	defer tm.mu.Unlock()

	s := tm.getOrCreate(agentID)
	s.interactions++
	decayed := tm.applyDecay(s.score)
	s.score = math.Min(1.0, decayed+reward*tm.config.RewardFactor)
}

// RecordFailure decreases an agent's trust score with asymmetric penalty.
func (tm *TrustManager) RecordFailure(agentID string, penalty float64) {
	tm.mu.Lock()
	defer tm.mu.Unlock()

	s := tm.getOrCreate(agentID)
	s.interactions++
	decayed := tm.applyDecay(s.score)
	s.score = math.Max(0.0, decayed-penalty*tm.config.PenaltyFactor)
}

func (tm *TrustManager) getOrCreate(agentID string) *scoreState {
	s, ok := tm.scores[agentID]
	if !ok {
		s = &scoreState{score: tm.config.InitialScore}
		tm.scores[agentID] = s
	}
	return s
}

func (tm *TrustManager) applyDecay(score float64) float64 {
	return score * (1.0 - tm.config.DecayRate)
}

func (tm *TrustManager) tierFor(score float64) string {
	switch {
	case score >= tm.config.TierThresholds.High:
		return "high"
	case score >= tm.config.TierThresholds.Medium:
		return "medium"
	default:
		return "low"
	}
}
