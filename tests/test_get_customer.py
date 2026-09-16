from invoke import call_tool


def test_retrieve_customer_information():
    result = call_tool("get_customer", customer_id="CUST-001")
    assert result["ok"] is True
    assert result["decision"] == "ALLOW"
    assert result["customer"]["name"] == "Alice Johnson"
    assert result["customer"]["email"] == "alice@example.com"


def test_unknown_customer():
    result = call_tool("get_customer", customer_id="CUST-404")
    assert result["ok"] is True
    assert result["found"] is False
