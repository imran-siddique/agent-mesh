#!/usr/bin/env python3
"""AgentMesh benchmark runner.

Runs all benchmark suites and outputs results as JSON and markdown.
Results are saved to benchmarks/results/latest.json.

Usage:
    python -m benchmarks.run_all
    python benchmarks/run_all.py
"""

import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure the repo root is on sys.path so imports work
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from benchmarks import bench_identity, bench_trust, bench_policy, bench_audit, bench_e2e


def _system_info() -> dict:
    return {
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _format_number(n: float) -> str:
    """Format number with commas."""
    if n >= 1_000:
        return f"{n:,.0f}"
    if n >= 1:
        return f"{n:.2f}"
    return f"{n:.4f}"


def _generate_markdown(results: dict) -> str:
    """Generate a markdown summary table from results."""
    lines = [
        "# Benchmark Results",
        "",
        f"> Generated: {results['system']['timestamp']}",
        f"> Platform: {results['system']['platform']}",
        f"> Python: {results['system']['python_version']}",
        f"> CPUs: {results['system']['cpu_count']}",
        "",
        "## Summary",
        "",
        "| Suite | Benchmark | Ops/sec | p50 (ms) | p95 (ms) | p99 (ms) |",
        "|-------|-----------|---------|----------|----------|----------|",
    ]

    suite_names = {
        "identity": "Identity",
        "trust": "Trust",
        "policy": "Policy",
        "audit": "Audit",
        "e2e": "End-to-End",
    }

    for suite_key, suite_label in suite_names.items():
        suite_data = results.get(suite_key, {})
        for bench_name, bench_data in suite_data.items():
            if isinstance(bench_data, dict) and "ops_per_sec" in bench_data:
                ops = _format_number(bench_data["ops_per_sec"])
                p50 = f"{bench_data.get('p50_ms', bench_data.get('mean_ms', 0)):.3f}"
                p95 = f"{bench_data.get('p95_ms', 0):.3f}"
                p99 = f"{bench_data.get('p99_ms', 0):.3f}"
                lines.append(
                    f"| {suite_label} | {bench_name} | {ops} | {p50} | {p95} | {p99} |"
                )
            elif isinstance(bench_data, dict):
                # Nested results (e.g., merkle verification by chain length)
                for sub_name, sub_data in bench_data.items():
                    if isinstance(sub_data, dict) and "mean_ms" in sub_data:
                        ops = _format_number(sub_data.get("ops_per_sec", 0))
                        p50 = f"{sub_data.get('p50_ms', sub_data.get('mean_ms', 0)):.3f}"
                        p95 = f"{sub_data.get('p95_ms', 0):.3f}"
                        p99 = f"{sub_data.get('p99_ms', 0):.3f}"
                        lines.append(
                            f"| {suite_label} | {sub_name} | {ops} | {p50} | {p95} | {p99} |"
                        )

    lines.extend([
        "",
        f"Total runtime: {results.get('total_seconds', 0):.1f}s",
    ])
    return "\n".join(lines)


def main():
    print("=" * 60)
    print("  AgentMesh Performance Benchmark Suite")
    print("=" * 60)
    print()

    results: dict = {"system": _system_info()}
    total_start = time.perf_counter()

    suites = [
        ("identity", "Identity Operations", bench_identity),
        ("trust", "Trust Engine", bench_trust),
        ("policy", "Policy Evaluation", bench_policy),
        ("audit", "Audit Logging", bench_audit),
        ("e2e", "End-to-End Governance", bench_e2e),
    ]

    for key, label, module in suites:
        print(f"\n--- {label} ---")
        results[key] = module.run_all()

    total_seconds = time.perf_counter() - total_start
    results["total_seconds"] = total_seconds

    # Save JSON results
    results_dir = Path(__file__).resolve().parent / "results"
    results_dir.mkdir(exist_ok=True)

    json_path = results_dir / "latest.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n✓ JSON results saved to {json_path}")

    # Generate and print markdown
    md = _generate_markdown(results)
    print(f"\n{md}")

    print(f"\n{'=' * 60}")
    print(f"  Completed in {total_seconds:.1f}s")
    print(f"{'=' * 60}")

    return results


if __name__ == "__main__":
    main()
