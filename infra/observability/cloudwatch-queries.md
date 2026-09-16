# CloudWatch / OpenTelemetry

AgentCore Runtime ships with `aws-opentelemetry-distro`. Local runs also write
JSONL spans to `.local/traces/spans.jsonl` (or `TRACE_DIR`).

## Failure → span mapping

| Failure | Span | Root cause |
| --- | --- | --- |
| Tool timeout | `tool.get_order` or `tool.refund_customer` status=ERROR, error contains Timeout | Downstream tool exceeded Gateway timeout (`FAILURE_MODE=timeout`) |
| Invalid parameters | `tool.get_order` with `error=invalid_parameters` | Empty or mismatched ids |
| Wrong tool selection | `gateway.policy.evaluate` DENY or `unknown_tool` | Model called a tool that is not permitted |
| HTTP 500 | `tool.refund_customer` RetryableBackendError | Refund backend returned 500; retries use exponential backoff |
| LLM loop | repeated `tool.*` spans in one `agent.invoke` trace | Model retried the same tool; stop after two identical failures |

## Insights queries

```sql
fields @timestamp, name, status, error, attributes.tool
| filter status = "ERROR"
| sort @timestamp desc
```

```sql
fields @timestamp, name, attributes.decision, attributes.tool
| filter name = "gateway.policy.evaluate"
| filter attributes.decision = "DENY"
```

```bash
agentcore traces list --limit 20
agentcore logs
```
