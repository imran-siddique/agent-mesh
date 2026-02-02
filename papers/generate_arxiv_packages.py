#!/usr/bin/env python3
"""
Generate arXiv submission packages for AgentMesh papers.
Following https://trevorcampbell.me/html/arxiv.html guidelines.
"""

import os
import re
import shutil
import tarfile
from pathlib import Path
from datetime import datetime

PAPERS_DIR = Path(__file__).parent

# Paper configurations
PAPERS = {
    "01-reward-engine": {
        "main_tex": "main.tex",
        "bbl_file": "main.bbl",
        "style_files": [],
        "figures_dir": "figures",
        "title": "Continuous Trust Scoring for Autonomous AI Agents: Multi-Dimensional Reward Learning with Automatic Revocation",
        "authors": "Imran Siddique",
        "abstract": "As AI agent deployments scale from single assistants to multi-agent ecosystems, traditional binary access control (allow/deny) becomes insufficient. Agents exhibit continuous behavioral variation—an agent trusted yesterday may behave anomalously today due to model drift, adversarial manipulation, or capability degradation. We present RewardEngine, a continuous trust scoring framework that evaluates agent behavior across five orthogonal dimensions: policy compliance, resource efficiency, output quality, security posture, and collaboration health. Unlike static rule-based systems, RewardEngine learns from runtime signals using exponential moving averages with recency weighting, updating scores every ≤30 seconds. Key innovations include: (1) Multi-dimensional trust representation replacing binary decisions, (2) Automatic credential revocation within <5 seconds when trust drops below configurable thresholds, (3) Adaptive weight learning that tunes dimension importance based on deployment context. Evaluated on simulated agent workloads with 1000 agents over 24 hours, RewardEngine achieves 94.2% precision in detecting degrading agents with 12.3% false positive rate, compared to 66.2% precision for single-dimension baselines. We integrate RewardEngine into AgentMesh for production deployment.",
        "categories": ["cs.AI", "cs.LG", "cs.CR"],
        "primary_category": "cs.AI"
    },
    "02-delegation-chains": {
        "main_tex": "main.tex",
        "bbl_file": "main.bbl",
        "style_files": [],
        "figures_dir": None,
        "title": "Capability-Narrowing Delegation Chains for AI Agent Security: Preventing Privilege Escalation in Multi-Agent Systems",
        "authors": "Imran Siddique",
        "abstract": "Multi-agent AI systems require agents to delegate tasks to sub-agents, creating complex chains of authority. Traditional access control lists (ACLs) and role-based access control (RBAC) fail to prevent privilege escalation when agents can create arbitrary sub-agents. We present Capability-Narrowing Delegation Chains, a cryptographic construction that guarantees capabilities can only decrease as delegation depth increases. Each delegation certificate contains: (1) the parent's signed capability set, (2) a strict subset of capabilities granted to the child, and (3) a hash chain linking to the root authority. We prove that our construction satisfies three security properties: Monotonic Narrowing (capabilities never expand), Revocation Propagation (revoking a parent instantly invalidates all descendants), and Tamper Detection (any modification breaks the hash chain). Implemented in AgentMesh with Ed25519 signatures, delegation certificate creation takes 2.1ms and chain verification scales linearly with depth. Security evaluation against 6 escalation attack classes shows 100% detection rate.",
        "categories": ["cs.CR", "cs.AI", "cs.SE"],
        "primary_category": "cs.CR"
    },
    "03-merkle-audit": {
        "main_tex": "main.tex",
        "bbl_file": "main.bbl",
        "style_files": [],
        "figures_dir": None,
        "title": "Tamper-Evident Governance for AI Agent Ecosystems: Merkle-Chained Audit Logs with Offline Verification",
        "authors": "Imran Siddique",
        "abstract": "As AI agents execute autonomous workflows in regulated industries, compliance teams face an unprecedented challenge: proving that governance was correctly enforced after the fact. Traditional audit logs are vulnerable to tampering—a compromised agent or malicious insider can modify records to hide policy violations. We present Merkle-Chained Audit Logs, a cryptographic data structure that provides tamper-evidence and offline verification for AI agent governance. Each audit entry is hash-chained to its predecessor, forming an append-only log. Periodically, we compute a Merkle tree over recent entries and publish the root hash to an immutable anchor (blockchain, Certificate Transparency log, or signed timestamp). Any modification—insertion, deletion, or alteration—is detectable by recomputing hashes. We prove that our scheme provides: (1) Tamper detection in O(log n) verification time, (2) Non-repudiation via agent signatures on entries, and (3) Selective disclosure enabling privacy-preserving audits. Experiments demonstrate 50,000 entries/second write throughput with verification latency under 5ms for 1 million entry logs. We integrate this into AgentMesh for automated SOC 2, HIPAA, and EU AI Act compliance reporting.",
        "categories": ["cs.CR", "cs.AI", "cs.DC"],
        "primary_category": "cs.CR"
    },
    "04-protocol-bridge": {
        "main_tex": "main.tex",
        "bbl_file": "main.bbl",
        "style_files": [],
        "figures_dir": None,
        "title": "Unified Trust Bridge for Heterogeneous Agent Protocols: Consistent Governance Across A2A, MCP, and IATP",
        "authors": "Imran Siddique",
        "abstract": "The AI agent ecosystem is fragmenting across incompatible protocols. Google's Agent-to-Agent (A2A) handles inter-agent coordination. Anthropic's Model Context Protocol (MCP) governs tool access. The Inter-Agent Trust Protocol (IATP) defines trust handshakes. Each protocol solves a slice of the problem—none provides trust across protocol boundaries. We present TrustBridge, a unified governance layer that speaks A2A, MCP, and IATP natively while enforcing a consistent trust model. When Agent A (on A2A) delegates to Agent B (on MCP), TrustBridge translates the request, performs capability verification, and ensures the audit trail spans both protocols seamlessly. Key innovations include: (1) Protocol-agnostic trust handshakes completing in <200ms cross-protocol, (2) Capability scope translation preserving security invariants across protocol boundaries, and (3) Unified audit trails enabling compliance reporting regardless of underlying protocol. Experiments on multi-protocol agent workflows demonstrate: 98.7% handshake success rate, 147ms median cross-protocol latency (vs. 892ms for naive gateway), and zero capability escalation across 10,000 cross-protocol delegations.",
        "categories": ["cs.NI", "cs.AI", "cs.DC"],
        "primary_category": "cs.NI"
    }
}


def remove_comments(tex_content: str) -> str:
    """Remove LaTeX comments while preserving % in URLs and escaped %."""
    lines = tex_content.split('\n')
    cleaned_lines = []
    for line in lines:
        # Find first unescaped % that's not in a URL
        result = []
        i = 0
        while i < len(line):
            if line[i] == '%':
                # Check if escaped
                if i > 0 and line[i-1] == '\\':
                    result.append('%')
                # Check if in URL (rough heuristic)
                elif 'http' in line[:i] or 'url{' in line[:i].lower():
                    result.append('%')
                else:
                    # Start of comment, stop here
                    break
            else:
                result.append(line[i])
            i += 1
        cleaned_lines.append(''.join(result).rstrip())
    return '\n'.join(cleaned_lines)


def flatten_figures(tex_content: str, figures_subdir: str) -> str:
    """Update figure paths to be in root directory."""
    if not figures_subdir:
        return tex_content
    # Handle various includegraphics patterns
    patterns = [
        (rf'\\includegraphics(\[[^\]]*\])?{{{figures_subdir}/([^}}]+)}}',
         r'\\includegraphics\1{\2}'),
        (rf'\\input{{{figures_subdir}/([^}}]+)}}',
         r'\\input{\1}'),
    ]
    for pattern, replacement in patterns:
        tex_content = re.sub(pattern, replacement, tex_content)
    return tex_content


def create_arxiv_package(paper_id: str, config: dict, output_dir: Path):
    """Create a clean arXiv submission package."""
    paper_dir = PAPERS_DIR / paper_id
    pkg_dir = output_dir / paper_id
    
    # Clean start
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    pkg_dir.mkdir(parents=True)
    
    print(f"\n{'='*60}")
    print(f"Processing {paper_id}: {config['title'][:50]}...")
    print(f"{'='*60}")
    
    # Determine source paths
    main_tex_path = paper_dir / config['main_tex']
    if not main_tex_path.exists():
        print(f"  ERROR: Main tex file not found: {main_tex_path}")
        return None
    
    # Read and process main.tex
    with open(main_tex_path, 'r', encoding='utf-8') as f:
        tex_content = f.read()
    
    # Remove comments
    tex_content = remove_comments(tex_content)
    
    # Flatten figure paths
    figures_subdir = config.get('figures_dir')
    if figures_subdir:
        tex_content = flatten_figures(tex_content, figures_subdir)
    
    # Add arXiv compilation hint at end
    if 'typeout{get arXiv' not in tex_content:
        tex_content = tex_content.rstrip()
        if tex_content.endswith('\\end{document}'):
            tex_content = tex_content[:-len('\\end{document}')]
            tex_content += '\n\\typeout{get arXiv to do 4 passes: Label(s) may have changed. Rerun}\n\\end{document}\n'
    
    # Write processed main.tex
    with open(pkg_dir / 'main.tex', 'w', encoding='utf-8') as f:
        f.write(tex_content)
    print(f"  - Wrote main.tex (comments removed, figures flattened)")
    
    # Copy style files
    for sty in config.get('style_files', []):
        sty_path = paper_dir / sty
        if sty_path.exists():
            shutil.copy(sty_path, pkg_dir / sty)
            print(f"  - Copied {sty}")
    
    # Copy .bbl file (pre-compiled bibliography) if exists
    bbl_file = config.get('bbl_file')
    if bbl_file:
        bbl_path = paper_dir / bbl_file
        if bbl_path.exists():
            shutil.copy(bbl_path, pkg_dir / 'main.bbl')
            print(f"  - Copied {bbl_file} -> main.bbl")
        else:
            print(f"  NOTE: BBL file not found: {bbl_path} (will need bibtex run)")
    
    # Copy figures (flattened to root)
    figures_dir = config.get('figures_dir')
    if figures_dir:
        fig_path = paper_dir / figures_dir
        if fig_path.exists():
            fig_count = 0
            for fig in fig_path.iterdir():
                if fig.suffix.lower() in ['.png', '.pdf', '.jpg', '.jpeg', '.eps', '.svg']:
                    shutil.copy(fig, pkg_dir / fig.name)
                    fig_count += 1
            print(f"  - Copied {fig_count} figures to root")
    
    # Create tarball
    tar_path = pkg_dir / 'submission.tar'
    with tarfile.open(tar_path, 'w') as tar:
        for item in pkg_dir.iterdir():
            if item.name != 'submission.tar':
                tar.add(item, arcname=item.name)
    print(f"  - Created submission.tar")
    
    # List contents
    print(f"  Package contents:")
    for item in sorted(pkg_dir.iterdir()):
        if item.name != 'submission.tar':
            size = item.stat().st_size
            print(f"    - {item.name} ({size:,} bytes)")
    
    return pkg_dir


def create_metadata_file(paper_id: str, config: dict, output_dir: Path):
    """Create arXiv metadata file."""
    metadata_path = output_dir / paper_id / 'ARXIV_METADATA.txt'
    
    metadata = f"""arXiv Submission Metadata
========================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Paper: {paper_id}

TITLE (use initial caps, no LaTeX):
{config['title']}

AUTHORS (comma-separated, no "and"):
{config['authors']}

ABSTRACT (plain text, no LaTeX, no line breaks):
{config['abstract']}

PRIMARY CATEGORY:
{config['primary_category']}

CROSS-LIST CATEGORIES:
{', '.join(config['categories'][1:]) if len(config['categories']) > 1 else 'None'}

COMMENTS:
Part of the AgentMesh project: https://github.com/imran-siddique/agent-mesh

LICENSE:
CC BY 4.0

---
Submission Checklist:
[ ] Upload submission.tar
[ ] Verify all files extracted correctly
[ ] Check compiled PDF for errors
[ ] Copy title exactly as above
[ ] Copy authors exactly as above  
[ ] Copy abstract (remove any remaining line breaks)
[ ] Select primary category: {config['primary_category']}
[ ] Add cross-list categories
[ ] Add comments field
"""
    
    with open(metadata_path, 'w', encoding='utf-8') as f:
        f.write(metadata)
    print(f"  - Created ARXIV_METADATA.txt")


def main():
    output_dir = PAPERS_DIR / 'arxiv_submissions'
    output_dir.mkdir(exist_ok=True)
    
    print("="*60)
    print("Generating arXiv Submission Packages for AgentMesh")
    print("="*60)
    print(f"Output directory: {output_dir}")
    
    for paper_id, config in PAPERS.items():
        try:
            pkg_dir = create_arxiv_package(paper_id, config, output_dir)
            if pkg_dir:
                create_metadata_file(paper_id, config, output_dir)
        except Exception as e:
            print(f"  ERROR processing {paper_id}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    for paper_id in PAPERS:
        pkg_dir = output_dir / paper_id
        if pkg_dir.exists():
            tar_path = pkg_dir / 'submission.tar'
            if tar_path.exists():
                print(f"  {paper_id}: submission.tar ({tar_path.stat().st_size:,} bytes)")
            else:
                print(f"  {paper_id}: FAILED (no tarball)")
        else:
            print(f"  {paper_id}: FAILED (no directory)")
    
    print(f"\nPackages ready in: {output_dir}")


if __name__ == '__main__':
    main()
