# Architecture

Production-like customer support agent on Amazon Bedrock AgentCore.

```mermaid
flowchart TB
  User[Customer] --> Runtime[AgentCore Runtime<br/>Strands agent]
  Runtime --> Memory[AgentCore Memory<br/>USER_PREFERENCE]
  Runtime --> IAM[IAM / AgentCore Identity<br/>no long-lived keys]
  Runtime --> Gateway[AgentCore Gateway MCP]
  Gateway --> Policy[Cedar Policy Engine<br/>ENFORCE]
  Policy -->|ALLOW amount &lt;= 1000| Tools[Business tools]
  Policy -->|DENY amount &gt; 1000| Deny[DENY + audit span]
  Tools --> Order[get_order]
  Tools --> Customer[get_customer]
  Tools --> Refund[refund_customer<br/>idempotency_key]
  Runtime --> OTEL[CloudWatch / OpenTelemetry]
  Gateway --> OTEL
  Policy --> OTEL
```

## Prompt injection path

```text
LLM requests refund(5000)
        ↓
Gateway
        ↓
Policy
        ↓
DENY
```

The model prompt is not the authorization layer. Cedar at the Gateway is.

## Components

| Piece | Local | AWS |
| --- | --- | --- |
| Agent | `app/SupportAgent/main.py` | AgentCore Runtime |
| Tools | `gateway/mcp_server.py` | AgentCore Gateway MCP target |
| Policy | `gateway/policy.py` reads `policy/*.cedar` | AgentCore Policy ENFORCE |
| Memory | `.local/memory.json` by actor_id | AgentCore Memory USER_PREFERENCE |
| Identity | AWS CLI/SSO profile | Runtime execution role |
| Refunds | SQLite + unique idempotency_key | same contract against the backend |
| Traces | `.local/traces/spans.jsonl` | CloudWatch / X-Ray |

## Reliability

`refund_customer` stores `idempotency_key`. The required key `operation-123` always
returns the original refund on retry. Retryable backend errors use exponential backoff.
