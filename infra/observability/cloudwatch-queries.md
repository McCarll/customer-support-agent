# CloudWatch / OpenTelemetry

AgentCore Runtime ships with `aws-opentelemetry-distro`. Local runs write JSONL
spans to `TRACE_DIR` (scenario evidence: `evidence/runs/spans.jsonl`).

Handled tool failures set span `status=ERROR`.

## Failure → span mapping

| Failure | Span | Root cause |
| --- | --- | --- |
| Tool timeout | `tool.get_order` status=ERROR | `FAILURE_MODE=timeout`; not retried |
| Invalid parameters | `tool.get_order` `invalid_parameters` | Empty or mismatched ids |
| Wrong tool | `gateway.policy.evaluate` DENY | Default deny / no Cedar permit |
| HTTP 500 | `tool.refund_customer` RetryableBackendError | Refund backend 500; exponential backoff |
| LLM loop | identical tool failure twice | `LoopGuard` stops a third identical call |

```sql
fields @timestamp, name, status, error, attributes.tool
| filter status = "ERROR"
| sort @timestamp desc
```

```bash
agentcore traces list --limit 20
agentcore logs
```
