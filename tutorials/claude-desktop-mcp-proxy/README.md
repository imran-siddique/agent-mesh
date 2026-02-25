# Secure Claude Desktop with AgentMesh MCP Proxy

> **Turn Claude Desktop from a black box into a governed, auditable AI assistant.**

Claude Desktop's Model Context Protocol (MCP) gives AI direct access to your
filesystem, databases, APIs, and shell. That's powerful — and dangerous without
guardrails. AgentMesh sits between Claude and your MCP servers, enforcing
trust policies, rate limits, and tamper-evident audit logging on every tool call.

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────┐
│  Claude Desktop │────▶│  AgentMesh MCP Proxy  │────▶│  MCP Server │
│                 │     │  ┌────────────────┐   │     │  (filesystem│
│  tool_call ──────────▶│  │ Policy Engine  │   │     │   shell, db)│
│                 │     │  │ Audit Logger   │   │     │             │
│  ◀──────────────────  │  │ Trust Scoring  │   │     │             │
│  governed result│     │  └────────────────┘   │     └─────────────┘
└─────────────────┘     └──────────────────────┘
```

## Why You Need This

| Without AgentMesh | With AgentMesh |
|---|---|
| Claude can `rm -rf /` via shell tool | Shell commands require approval or are blocked |
| No record of what tools were called | Every call hash-chained in tamper-evident audit log |
| All tools equally trusted | Granular allow / require-approval / block policies |
| Unlimited tool call rate | Rate limiting prevents runaway agents |
| No identity verification | Cryptographic DID identity for every MCP session |

## Prerequisites

- Python 3.10+
- Claude Desktop (optional — the demo works standalone)
- 5 minutes

## Step 1: Install AgentMesh

```bash
pip install agentmesh-platform
```

Verify:

```bash
python -c "from agentmesh import AgentIdentity, PolicyEngine, AuditLog; print('AgentMesh ready')"
```

## Step 2: Define Governance Policies

Create a policy file that controls which MCP tools Claude can access. See
[`policies/mcp-governance.yaml`](policies/mcp-governance.yaml) for the full
example. The key sections:

```yaml
policies:
  - id: mcp-claude-desktop
    name: Claude Desktop MCP Governance
    rules:
      # Safe read operations — always allowed
      - id: allow-reads
        action: allow
        conditions:
          - "tool in ['read_file', 'search_files', 'list_directory', 'browse_web']"

      # Write operations — require human approval
      - id: approve-writes
        action: require_approval
        conditions:
          - "tool in ['write_file', 'execute_command']"

      # Dangerous operations — always blocked
      - id: block-destructive
        action: deny
        conditions:
          - "tool in ['delete_file', 'modify_system', 'shell_exec']"
```

## Step 3: Configure Claude Desktop

Claude Desktop uses a JSON config file to define MCP servers. Instead of
pointing Claude directly at your MCP server, point it at the AgentMesh proxy.

**Config file location:**

| OS | Path |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

Copy [`claude_desktop_config.example.json`](claude_desktop_config.example.json)
to the appropriate location and adjust paths:

```json
{
  "mcpServers": {
    "filesystem-governed": {
      "command": "python",
      "args": [
        "-m", "agentmesh.integrations.mcp.proxy",
        "--upstream", "npx @modelcontextprotocol/server-filesystem /home/user/projects",
        "--policy", "./policies/mcp-governance.yaml",
        "--audit-dir", "./audit-logs"
      ],
      "env": {
        "AGENTMESH_AGENT_NAME": "claude-desktop",
        "AGENTMESH_SPONSOR": "security@company.com",
        "AGENTMESH_TRUST_MIN_SCORE": "600",
        "AGENTMESH_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

After saving, restart Claude Desktop. The proxy intercepts all tool calls
transparently — Claude doesn't know or care that governance is in place.

## Step 4: Run the Demo (No Claude Desktop Required)

The included demo simulates the full proxy flow:

```bash
cd tutorials/claude-desktop-mcp-proxy
python demo.py
```

**Expected output:**

```
══════════════════════════════════════════════════════
  AgentMesh MCP Proxy Demo — Claude Desktop Security
══════════════════════════════════════════════════════

[1] Agent identity created
    DID: did:mesh:a3f8...c912
    Name: claude-desktop-proxy

[2] Governance policies loaded
    Rules: 5 active
    Mode: enforce (not shadow)

[3] Simulating MCP tool calls...

    ✅ read_file(/home/user/notes.txt)
       Policy: ALLOW (rule: allow-reads)
       Audit:  logged #0001

    ✅ search_files("TODO")
       Policy: ALLOW (rule: allow-reads)
       Audit:  logged #0002

    ⏳ write_file(/home/user/output.txt, ...)
       Policy: REQUIRE_APPROVAL (rule: approve-writes)
       Audit:  logged #0003 (pending approval)

    🚫 delete_file(/etc/passwd)
       Policy: DENY (rule: block-destructive)
       Audit:  logged #0004 (blocked)

    🚫 shell_exec("rm -rf /")
       Policy: DENY (rule: block-destructive)
       Audit:  logged #0005 (blocked)

    ✅ browse_web("https://example.com")
       Policy: ALLOW (rule: allow-reads)
       Audit:  logged #0006

[4] Audit trail (tamper-evident, hash-chained)
    ┌─────┬──────────────┬──────────┬──────────────────┐
    │  #  │ Tool         │ Decision │ Hash             │
    ├─────┼──────────────┼──────────┼──────────────────┤
    │ 001 │ read_file    │ allow    │ a3f8c1...        │
    │ 002 │ search_files │ allow    │ b7d2e4...        │
    │ 003 │ write_file   │ approval │ c9a1f6...        │
    │ 004 │ delete_file  │ deny     │ d4b3c8...        │
    │ 005 │ shell_exec   │ deny     │ e1f5a2...        │
    │ 006 │ browse_web   │ allow    │ f6c9d3...        │
    └─────┴──────────────┴──────────┴──────────────────┘

    Chain integrity: ✅ verified (6/6 entries)

[5] Trust score impact
    Initial:  800 (trusted)
    After:    780 (2 blocked calls reduced score)
    Status:   ⚠ within warning threshold
```

## Step 5: Inspect Audit Logs

Every tool call produces a CloudEvents-format audit entry:

```json
{
  "specversion": "1.0",
  "type": "agentmesh.mcp.tool_call",
  "source": "did:mesh:a3f8c912",
  "id": "evt-0004",
  "time": "2025-01-15T10:32:01Z",
  "data": {
    "tool": "delete_file",
    "params": {"path": "/etc/passwd"},
    "decision": "deny",
    "matched_rule": "block-destructive",
    "reason": "Tool 'delete_file' is blocked by governance policy",
    "trust_score": 780,
    "chain_hash": "d4b3c8..."
  }
}
```

Entries are hash-chained: each entry's hash includes the previous entry's hash,
making tampering detectable. Use `agentmesh audit verify` to validate the chain.

## Step 6: Customize Policies

### Block specific file paths

```yaml
- id: block-sensitive-paths
  action: deny
  conditions:
    - "tool == 'read_file'"
    - "params.path starts_with '/etc/'"
  message: "Access to system configuration files is blocked"
  severity: critical
```

### Rate limit API calls

```yaml
- id: rate-limit-api
  action: deny
  conditions:
    - "count(tool='browse_web', window='1h') > 100"
  message: "Hourly rate limit exceeded for web browsing"
  limit: "100/hour"
```

### Shadow mode (log-only, don't block)

Set `shadow_mode: true` in the governance config to test policies without
enforcement. All decisions are logged but never block tool calls.

## How It Works

1. **Claude Desktop** sends a tool call via MCP (e.g., `read_file`)
2. **AgentMesh Proxy** intercepts the call before it reaches the MCP server
3. **Policy Engine** evaluates the call against governance rules (<5ms)
4. **Decision:**
   - `allow` → forward to upstream MCP server, return result
   - `require_approval` → hold until human approves (or auto-deny after timeout)
   - `deny` → return error to Claude, log the attempt
5. **Audit Logger** records the call, decision, and result in a hash-chained log
6. **Trust Scoring** adjusts the session's trust score based on behavior

## Troubleshooting

| Issue | Solution |
|---|---|
| Claude can't see MCP tools | Check `claude_desktop_config.json` syntax, restart Claude |
| All calls blocked | Verify policy file path, check for `shadow_mode: true` |
| Audit logs empty | Ensure `--audit-dir` path is writable |
| Proxy won't start | Check Python 3.10+, run `pip install agentmesh-platform` |

## Next Steps

- [MCP Tool Server Example](../../examples/01-mcp-tool-server/) — Full MCP
  server with governance
- [Healthcare HIPAA Example](../../examples/03-healthcare-hipaa/) — Compliance
  automation
- [Architecture Guide](../../ARCHITECTURE.md) — Deep dive into the trust stack
- [Security Policy](../../SECURITY.md) — Report vulnerabilities

---

*Part of the [AgentMesh](https://github.com/imran-siddique/agent-mesh) project —
SSL for AI Agents.*
