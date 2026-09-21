# Five-minute technical walkthrough

## 0:00–0:40 — What the system does

This is a customer-support agent for order status, customer lookup, and
refunds. It uses a Strands agent hosted on Amazon Bedrock AgentCore Runtime.
The agent can reason about a request, but it cannot access business data or
issue a refund directly.

## 0:40–1:30 — Request path and tool integration

A customer request enters the AgentCore Runtime, where the Strands agent
selects one of three MCP tools: `get_order`, `get_customer`, or
`refund_customer`. The tools are exposed through AgentCore Gateway. Gateway is
the integration boundary: all business operations use the same MCP contract,
regardless of whether the target is the local demo server or a deployed
service.

## 1:30–2:25 — Trust boundary and authorization

The model is outside the authorization boundary. It may propose a tool call,
including one influenced by prompt injection, but Gateway Policy evaluates the
call before the refund backend runs. Cedar permits refunds at or below $1,000,
forbids refunds above $1,000, and defaults to deny when no permit exists.
The `refund_customer` implementation is therefore never reached for a $5,000
request. Runtime and Gateway use IAM identities and SigV4 for the deployed MCP
endpoint; the repository contains no access keys.

## 2:25–3:10 — Memory and identity

Preferences are stored by `actor_id`, rather than by `session_id`, so a
preference saved in one session is available in another. Locally this is a JSON
backend that makes the demo testable without AWS. In deployment,
`AGENTCORE_MEMORY_ID` switches the session manager to AgentCore Memory using
the USER_PREFERENCE strategy. The execution role limits the runtime to its
Bedrock model, named memory, and named Gateway.

## 3:10–4:05 — Reliability and observability

Refunds require an idempotency key. A replay returns the original refund and a
different payload using the same key is rejected. Transient HTTP 500 errors
receive bounded exponential backoff; invalid input and timeouts are returned
without retrying. Every policy decision and tool call produces a span. Local
runs write JSONL evidence, while the deployment path exports telemetry to
CloudWatch and X-Ray.

## 4:05–5:00 — Demonstration, trade-offs, and next steps

Demonstrate the delayed order, customer lookup, a $249.99 refund, a replay,
cross-session region recall, and the denied $5,000 prompt-injection request.
Then show the timeout, invalid-parameter, and HTTP 500 spans.

The local SQLite and JSON memory stores prioritize repeatable, low-cost tests;
they are adapters, not production durable stores. The policy evaluator is a
local approximation that exercises the Cedar source files, while the deployed
Gateway policy engine is the authorization authority. The remaining production
work is to replace deployment placeholders such as `GATEWAY_ARN` and account
wildcards with real resource ARNs, then validate the same scenarios in AWS.
