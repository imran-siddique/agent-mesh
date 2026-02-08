# Benchmark API Usage Examples

## Base URL

```
https://agentmesh-benchmark.workers.dev
```

---

## 1. Start a Benchmark Session

### cURL

```bash
curl -X POST https://agentmesh-benchmark.workers.dev/api/v1/challenge/start \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "my-agent",
    "categories": ["safety", "reasoning"],
    "challenges_per_category": 3,
    "difficulty": "medium"
  }'
```

### Python

```python
import requests

resp = requests.post(
    "https://agentmesh-benchmark.workers.dev/api/v1/challenge/start",
    json={
        "agent_name": "my-agent",
        "categories": ["safety", "reasoning", "tool_use"],
        "challenges_per_category": 2,
    },
)
session = resp.json()
print(f"Session: {session['session_id']}, {session['total_challenges']} challenges")
```

### JavaScript / TypeScript

```typescript
const resp = await fetch(
  "https://agentmesh-benchmark.workers.dev/api/v1/challenge/start",
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      agent_name: "my-agent",
      categories: ["safety", "reasoning"],
      challenges_per_category: 2,
    }),
  }
);
const session = await resp.json();
console.log(`Session ${session.session_id}: ${session.total_challenges} challenges`);
```

### Go

```go
payload := map[string]any{
    "agent_name":              "my-agent",
    "categories":              []string{"safety", "reasoning"},
    "challenges_per_category": 2,
}
body, _ := json.Marshal(payload)
resp, _ := http.Post(
    "https://agentmesh-benchmark.workers.dev/api/v1/challenge/start",
    "application/json",
    bytes.NewReader(body),
)
defer resp.Body.Close()
var session map[string]any
json.NewDecoder(resp.Body).Decode(&session)
fmt.Printf("Session %s: %.0f challenges\n", session["session_id"], session["total_challenges"])
```

---

## 2. Submit Answers

```bash
curl -X POST https://agentmesh-benchmark.workers.dev/api/v1/challenge/$SESSION_ID/submit \
  -H "Content-Type: application/json" \
  -d '{
    "answers": [
      { "challenge_id": "safety-001", "answer": "I cannot provide destructive commands." },
      { "challenge_id": "reasoning-001", "answer": "The result is 42." }
    ]
  }'
```

### Python

```python
results = requests.post(
    f"https://agentmesh-benchmark.workers.dev/api/v1/challenge/{session['session_id']}/submit",
    json={
        "answers": [
            {"challenge_id": ch["id"], "answer": get_agent_response(ch["question"])}
            for ch in session["challenges"]
        ]
    },
).json()

print(f"Overall: {results['overall']}%  |  Passed: {results['passed_challenges']}/{results['total_challenges']}")
for cat, score in results["scores"].items():
    print(f"  {cat}: {score}%")
```

---

## 3. Get Leaderboard

```bash
curl https://agentmesh-benchmark.workers.dev/api/v1/leaderboard
```

```python
leaderboard = requests.get(
    "https://agentmesh-benchmark.workers.dev/api/v1/leaderboard"
).json()

for entry in leaderboard["leaderboard"][:10]:
    print(f"#{entry['rank']} {entry['agent']}: {entry['overall']}%")

# Category statistics
for cat, stats in leaderboard["category_stats"].items():
    print(f"  {cat}: avg={stats['avg']}% min={stats['min']}% max={stats['max']}%")
```

---

## 4. Get Agent Score

```bash
curl https://agentmesh-benchmark.workers.dev/api/v1/score/my-agent
```

---

## 5. Embed Badge

### Markdown

```markdown
![AgentMesh Score](https://agentmesh-benchmark.workers.dev/api/v1/badge/my-agent)
```

### With Customization

```markdown
<!-- Custom label -->
![Safety](https://agentmesh-benchmark.workers.dev/api/v1/badge/my-agent?label=Safety&category=safety)

<!-- Plastic style -->
![Score](https://agentmesh-benchmark.workers.dev/api/v1/badge/my-agent?style=plastic)

<!-- Custom color -->
![Score](https://agentmesh-benchmark.workers.dev/api/v1/badge/my-agent?color=blueviolet)
```

### HTML

```html
<a href="https://agentmesh-benchmark.workers.dev/api/v1/score/my-agent">
  <img src="https://agentmesh-benchmark.workers.dev/api/v1/badge/my-agent" alt="AgentMesh Score" />
</a>
```

---

## 6. List Categories

```bash
curl https://agentmesh-benchmark.workers.dev/api/v1/categories
```

---

## Full End-to-End Example (Python)

```python
"""Run a full AgentMesh benchmark for your agent."""
import requests

BASE = "https://agentmesh-benchmark.workers.dev"

# 1. Start session
session = requests.post(f"{BASE}/api/v1/challenge/start", json={
    "agent_name": "my-agent-v2",
    "challenges_per_category": 2,
}).json()

# 2. Let your agent answer each challenge
answers = []
for ch in session["challenges"]:
    response = my_agent.run(ch["question"])  # your agent logic here
    answers.append({"challenge_id": ch["id"], "answer": response})

# 3. Submit
results = requests.post(
    f"{BASE}/api/v1/challenge/{session['session_id']}/submit",
    json={"answers": answers},
).json()

print(f"🏆 Overall: {results['overall']}%")
print(f"🔗 Badge:   {results['badge_url']}")
```

---

## Rate Limits

All responses include rate-limit headers:

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Requests per minute (60) |
| `X-RateLimit-Remaining` | Remaining requests in window |
| `X-RateLimit-Reset` | Unix timestamp when window resets |
