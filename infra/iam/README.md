# Least-privilege IAM

The agent does not embed access keys. AgentCore Runtime assumes `runtime-role.json`.
The Gateway assumes `gateway-role.json`. Replace `*` account ids with the
deployed account after `agentcore deploy`.

Outbound MCP calls to AgentCore Gateway are SigV4-signed (`mcp-proxy-for-aws`)
when `MCP_URL` is a `gateway.bedrock-agentcore` endpoint. Localhost stays unsigned HTTP.
