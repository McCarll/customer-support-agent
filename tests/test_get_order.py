from invoke import call_tool


def test_agent_checks_delayed_order_123():
    result = call_tool("get_order", order_id="123")
    assert result["ok"] is True
    assert result["decision"] == "ALLOW"
    assert result["order"]["status"] == "delayed"
    assert "Dublin" in result["order"]["delay_reason"]


def test_unknown_order_is_not_invented():
    result = call_tool("get_order", order_id="999")
    assert result["ok"] is True
    assert result["found"] is False
