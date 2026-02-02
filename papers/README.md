# AgentMesh Research Papers

> Academic research supporting the AgentMesh governance platform.

## Paper Portfolio

AgentMesh introduces four novel contributions to AI agent governance:

| # | Paper | Component | Target Venue | Status |
|---|-------|-----------|--------------|--------|
| 1 | **Continuous Trust Scoring** | Reward Engine | NeurIPS/ICML 2026 | Draft |
| 2 | **Capability-Narrowing Delegation** | Identity Layer | IEEE S&P/USENIX 2026 | Draft |
| 3 | **Tamper-Evident Governance** | Merkle Audit | NDSS/CCS 2026 | Draft |
| 4 | **Unified Trust Bridge** | Protocol Bridge | WWW/SIGCOMM 2026 | Draft |

## Innovation Analysis

### What's Novel (Paper-Worthy)

| Innovation | Traditional Approach | AgentMesh Contribution |
|------------|---------------------|------------------------|
| **Multi-dimensional reward scoring** | Binary allow/deny | 5-dimension continuous trust with EMA learning |
| **Automatic credential revocation** | Manual review | <5s revocation on trust breach |
| **Cryptographic delegation narrowing** | ACL lists | Provably narrowing capability chains |
| **Merkle-chained audit logs** | Database logs | Offline-verifiable tamper evidence |
| **Cross-protocol trust preservation** | Per-protocol auth | Trust context propagates across A2A/MCP/IATP |

### Standard Implementations (No Paper)

- Basic identity/credential management (standard SPIFFE patterns)
- Rate limiting (well-established algorithms)
- Shadow mode A/B testing (standard practice)
- Policy YAML/JSON parsing (conventional)

## Dependency Graph

```
┌─────────────────────────┐
│  01-Reward Engine       │  ← Runtime learning, novel contribution
└───────────┬─────────────┘
            │
┌───────────┴─────────────┐
│  02-Delegation Chains   │  ← Security foundation
└───────────┬─────────────┘
            │
┌───────────┴─────────────┐
│  03-Merkle Audit        │  ← Compliance layer
└───────────┬─────────────┘
            │
┌───────────┴─────────────┐
│  04-Protocol Bridge     │  ← Interoperability
└─────────────────────────┘
```

## Building Papers

Each paper uses standard LaTeX:

```bash
# Build a single paper
cd papers/01-reward-engine
pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex

# Build all papers
for dir in papers/*/; do
    if [ -f "$dir/main.tex" ]; then
        (cd "$dir" && pdflatex main.tex && bibtex main 2>/dev/null; pdflatex main.tex && pdflatex main.tex)
    fi
done
```

## Running Experiments

### Paper 1: Reward Engine Benchmark

```bash
cd papers/01-reward-engine/experiments

# Full benchmark (1000 agents, 24 hours simulated)
python run_benchmark.py --agents 1000 --duration 86400 --output results/

# Quick test (100 agents, 1 hour)
python run_benchmark.py --agents 100 --duration 3600 --output results/

# Ablation study
python run_benchmark.py --agents 500 --duration 43200 --ablation --output results/
```

Expected results:
- RewardEngine: 94.2% precision, 12.3% FPR, 3.1s latency
- Single-dimension baseline: 66.2% precision, 34.2% FPR
- Binary rules: 100% precision, 0% recall on unknown threats

### Paper 2: Delegation Chain Tests

```bash
cd papers/02-delegation-chains/experiments
python test_narrowing.py  # Verify capability narrowing
python test_revocation.py  # Measure revocation propagation
```

### Paper 3: Merkle Audit Benchmarks

```bash
cd papers/03-merkle-audit/experiments
python bench_throughput.py  # Write throughput
python bench_verification.py  # Verification latency
```

### Paper 4: Protocol Bridge Latency

```bash
cd papers/04-protocol-bridge/experiments
python bench_crossprotocol.py  # Cross-protocol latency
python test_escalation.py  # Escalation attack detection
```

## arXiv Submission

All papers are prepared for arXiv submission:

1. ✅ Non-anonymous author information
2. ✅ Correct citations to real, published work
3. ✅ Reproducible experiments with code links
4. ✅ Self-contained (no external style files)
5. ✅ pdflatex compatible

To prepare submission package:

```bash
cd papers/01-reward-engine
mkdir -p arxiv_submission
cp main.tex arxiv_submission/
cp -r figures/ arxiv_submission/ 2>/dev/null || true
cp main.bbl arxiv_submission/ 2>/dev/null || true
cd arxiv_submission && tar -czvf ../arxiv_package.tar.gz *
```

## Author Information

**Imran Siddique**  
Principal Software Engineer  
Microsoft  
Email: imran.siddique@microsoft.com

## Related Work

These papers build on the Agent OS research:
- [CMVK: Cross-Model Verification Kernel](https://github.com/imran-siddique/agent-os/papers/02-cmvk)
- [CaaS: Context-as-a-Service](https://github.com/imran-siddique/agent-os/papers/03-caas)
- [IATP: Inter-Agent Trust Protocol](https://github.com/imran-siddique/agent-os/papers/04-iatp)
- [Control Plane: Deterministic Governance](https://github.com/imran-siddique/agent-os/papers/05-control-plane)
- [SCAK: Self-Correcting Agent Kernel](https://github.com/imran-siddique/agent-os/papers/06-scak)

## License

All papers are released under CC-BY-4.0 for academic use.
