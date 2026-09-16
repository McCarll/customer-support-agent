# Observability evidence

After you run the scenarios, copy traces and screenshots here:

- `evidence/captured/traces/spans.jsonl` — local JSONL spans
- CloudWatch / `agentcore traces` screenshots for Runtime
- Policy DENY audit for the $5,000 injection

Expected local span names are listed in `infra/observability/cloudwatch-queries.md`.
Sample shape:

```json
{
  "name": "gateway.policy.evaluate",
  "status": "ERROR",
  "attributes": {"tool": "refund_customer", "decision": "DENY"},
  "error": "Cedar forbid matched (forbid-wins)."
}
```
