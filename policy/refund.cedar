// Replace GATEWAY_ARN after the first `agentcore deploy` with the real Gateway ARN.
// AgentCore Policy is deny-by-default and forbid-wins.
// Required rules: refund <= 1000 ALLOW, refund > 1000 DENY.

permit(
  principal,
  action == AgentCore::Action::"SupportTarget___refund_customer",
  resource == AgentCore::Gateway::"GATEWAY_ARN"
)
when {
  context.input has amount &&
  context.input.amount <= 1000
};

forbid(
  principal,
  action == AgentCore::Action::"SupportTarget___refund_customer",
  resource == AgentCore::Gateway::"GATEWAY_ARN"
)
when {
  context.input.amount > 1000
};
