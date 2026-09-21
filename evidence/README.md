# Evidence

Tracked captures live in `evidence/runs/` (committed). Do not commit `.env`.

Regenerate:

```bash
python scripts/run_scenarios.py
```

| File | Scenario |
| --- | --- |
| `runs/scenarios.json` | Order, customer, ALLOW refund, replay, DENY $5000, memory, and timeout/parameters/HTTP 500/LLM-loop failures |
| `runs/policy-deny-refund-5000.json` | Prompt injection / refund over limit |
| `runs/idempotent-refund.json` | `operation-123` replay, one refund |
| `runs/spans.jsonl` | Policy and tool spans including ERROR status |
| `../docs/architecture.svg` | Architecture diagram |

After AWS deploy, add a CloudWatch / `agentcore traces` screenshot next to these files.
