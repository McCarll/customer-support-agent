// Read tools are permitted without an amount condition.
// Refund remains governed by refund.cedar.

permit(
  principal,
  action == AgentCore::Action::"SupportTarget___get_order",
  resource == AgentCore::Gateway::"GATEWAY_ARN"
);

permit(
  principal,
  action == AgentCore::Action::"SupportTarget___get_customer",
  resource == AgentCore::Gateway::"GATEWAY_ARN"
);
