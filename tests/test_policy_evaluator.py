from policy import evaluate, load_policies


def test_cedar_files_are_the_source_of_policy():
    rules = load_policies()
    sources = {rule.source for rule in rules}
    assert "refund.cedar" in sources
    assert "read_tools.cedar" in sources
    assert any(rule.effect == "forbid" for rule in rules)


def test_read_tools_are_permitted():
    assert evaluate("get_order", {"order_id": "123"}).decision == "ALLOW"
    assert evaluate("get_customer", {"customer_id": "CUST-001"}).decision == "ALLOW"


def test_unknown_tool_default_deny():
    assert evaluate("wire_money", {"amount": 1}).decision == "DENY"
