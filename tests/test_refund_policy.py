from invoke import call_tool
from store import refund_count


def test_refund_at_limit_is_allowed():
    result = call_tool(
        "refund_customer",
        customer_id="CUST-001",
        amount=1000,
        order_id="123",
        idempotency_key="at-limit",
    )
    assert result["decision"] == "ALLOW"
    assert result["ok"] is True
    assert result["refund"]["amount"] == 1000


def test_refund_below_limit_is_allowed():
    result = call_tool(
        "refund_customer",
        customer_id="CUST-001",
        amount=249.99,
        order_id="123",
        idempotency_key="operation-123",
    )
    assert result["decision"] == "ALLOW"
    assert result["refund"]["idempotency_key"] == "operation-123"


def test_refund_above_limit_is_denied():
    result = call_tool(
        "refund_customer",
        customer_id="CUST-001",
        amount=1000.01,
        order_id="123",
        idempotency_key="over-limit",
    )
    assert result["decision"] == "DENY"
    assert result["authorized"] is False
    assert refund_count() == 0


def test_refund_5000_is_denied():
    result = call_tool(
        "refund_customer",
        customer_id="CUST-001",
        amount=5000,
        order_id="123",
        idempotency_key="five-thousand",
    )
    assert result["decision"] == "DENY"
    assert refund_count() == 0
