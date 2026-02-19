"""Policy evaluation benchmarks for AgentMesh.

Measures single and multi-rule evaluation latency, YAML loading,
and pattern matching throughput.
"""

import fnmatch
import statistics
import time

try:
    from agentmesh.governance.policy import Policy, PolicyEngine, PolicyRule

    _HAS_AGENTMESH = True
except ImportError:
    _HAS_AGENTMESH = False

ITERATIONS = 1_000
WARMUP = 50

SAMPLE_YAML_10 = """
name: bench-policy-10
version: "1.0"
rules:
""" + "\n".join(
    f"""  - name: rule-{i}
    condition: "agent_did == 'did:mesh:agent-{i}' and action == 'tool:invoke'"
    action: allow
    priority: {i}"""
    for i in range(10)
)

SAMPLE_YAML_100 = """
name: bench-policy-100
version: "1.0"
rules:
""" + "\n".join(
    f"""  - name: rule-{i}
    condition: "agent_did == 'did:mesh:agent-{i}' and action == 'tool:invoke'"
    action: allow
    priority: {i}"""
    for i in range(100)
)


def _percentile(data: list[float], pct: float) -> float:
    s = sorted(data)
    idx = int(len(s) * pct / 100)
    return s[min(idx, len(s) - 1)]


def _bench(fn, n: int = ITERATIONS, warmup: int = WARMUP) -> dict:
    for _ in range(warmup):
        fn()
    times: list[float] = []
    for _ in range(n):
        start = time.perf_counter()
        fn()
        elapsed = (time.perf_counter() - start) * 1_000
        times.append(elapsed)
    mean = statistics.mean(times)
    return {
        "iterations": n,
        "mean_ms": mean,
        "median_ms": statistics.median(times),
        "p50_ms": _percentile(times, 50),
        "p95_ms": _percentile(times, 95),
        "p99_ms": _percentile(times, 99),
        "min_ms": min(times),
        "max_ms": max(times),
        "stdev_ms": statistics.stdev(times) if n > 1 else 0.0,
        "ops_per_sec": 1_000 / mean if mean > 0 else float("inf"),
    }


# ---------------------------------------------------------------------------
# Simulated policy evaluation (always available)
# ---------------------------------------------------------------------------

def _simulate_rule_match(rule: dict, context: dict) -> bool:
    """Simulate matching a rule against a context."""
    for key, pattern in rule.get("condition", {}).items():
        value = context.get(key, "")
        if not fnmatch.fnmatch(value, pattern):
            return False
    return True


def _build_rules(n: int) -> list[dict]:
    return [
        {
            "name": f"rule-{i}",
            "condition": {
                "agent_did": f"did:mesh:agent-{i}",
                "action": "tool:invoke",
            },
            "action": "allow",
            "priority": i,
        }
        for i in range(n)
    ]


def bench_single_rule_evaluation() -> dict:
    """Single rule evaluation latency."""
    rule = _build_rules(1)[0]
    context = {"agent_did": "did:mesh:agent-0", "action": "tool:invoke"}

    def evaluate():
        _simulate_rule_match(rule, context)

    return _bench(evaluate, n=10_000)


def bench_10_rule_evaluation() -> dict:
    """10-rule policy evaluation latency."""
    rules = _build_rules(10)
    context = {"agent_did": "did:mesh:agent-5", "action": "tool:invoke"}

    def evaluate():
        for rule in rules:
            if _simulate_rule_match(rule, context):
                return rule["action"]
        return "deny"

    return _bench(evaluate, n=5_000)


def bench_100_rule_evaluation() -> dict:
    """100-rule policy evaluation latency."""
    rules = _build_rules(100)
    context = {"agent_did": "did:mesh:agent-50", "action": "tool:invoke"}

    def evaluate():
        for rule in rules:
            if _simulate_rule_match(rule, context):
                return rule["action"]
        return "deny"

    return _bench(evaluate)


def bench_yaml_loading() -> dict | None:
    """YAML policy loading time."""
    if not _HAS_AGENTMESH:
        # Fallback: use pyyaml directly
        try:
            import yaml

            def load():
                yaml.safe_load(SAMPLE_YAML_100)

            return _bench(load, n=500)
        except ImportError:
            return None

    engine = PolicyEngine()

    def load():
        engine.load_yaml(SAMPLE_YAML_100)

    return _bench(load, n=500)


def bench_pattern_matching() -> dict:
    """Pattern matching throughput (fnmatch)."""
    patterns = [f"did:mesh:agent-{i}*" for i in range(100)]
    value = "did:mesh:agent-42-instance-7"

    def match_all():
        for p in patterns:
            fnmatch.fnmatch(value, p)

    return _bench(match_all, n=5_000)


def bench_policy_engine_evaluate() -> dict | None:
    """PolicyEngine.evaluate with 10-rule policy."""
    if not _HAS_AGENTMESH:
        return None
    engine = PolicyEngine()
    engine.load_yaml(SAMPLE_YAML_10)
    context = {"agent_did": "did:mesh:agent-5", "action": "tool:invoke"}

    def evaluate():
        engine.evaluate("did:mesh:agent-5", context)

    return _bench(evaluate)


def run_all() -> dict:
    """Run all policy benchmarks."""
    results: dict = {}
    benchmarks = [
        ("single_rule_evaluation", bench_single_rule_evaluation),
        ("10_rule_evaluation", bench_10_rule_evaluation),
        ("100_rule_evaluation", bench_100_rule_evaluation),
        ("yaml_loading", bench_yaml_loading),
        ("pattern_matching", bench_pattern_matching),
        ("policy_engine_evaluate", bench_policy_engine_evaluate),
    ]
    for name, fn in benchmarks:
        print(f"  Running {name}...", end=" ", flush=True)
        result = fn()
        if result is not None:
            results[name] = result
            print(f"{result['ops_per_sec']:.0f} ops/sec")
        else:
            print("SKIPPED (import unavailable)")
    return results


if __name__ == "__main__":
    print("=== Policy Benchmarks ===")
    run_all()
