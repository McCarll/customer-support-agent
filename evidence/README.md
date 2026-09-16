# Evidence

Do not commit secrets. After a local or AWS run, store screenshots and logs in
`evidence/captured/` (gitignored except the instructions).

## Checklist

1. Order 123 delayed — tool result or agent transcript
2. Customer CUST-001 profile
3. Refund ALLOW ≤ $1000 with `operation-123`
4. Refund replay with the same key (one refund)
5. Refund DENY $5000 / prompt injection
6. Memory: preference `eu-west-1` recalled in a new session
7. Traces for timeout, invalid parameters, HTTP 500
8. CloudWatch or `agentcore traces` screenshot after deploy
