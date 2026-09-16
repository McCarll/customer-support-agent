# Least-privilege IAM

The agent does not embed access keys. AgentCore Runtime assumes `runtime-role.json`.
The Gateway assumes `gateway-role.json`. Tighten the `*` region/account placeholders
to the deployed account after `agentcore deploy`.

Outbound calls from the agent to the Gateway use IAM (`authorizerType: AWS_IAM`)
or AgentCore Identity. Local development uses `aws sso login` / an AWS CLI profile.
