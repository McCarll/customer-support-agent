from invoke import call_tool
from store import configure_failures, refund_count


def test_retryable_failure_then_success_creates_one_refund():
    configure_failures(2)
    result = call_tool(
        "refund_customer",
        customer_id="CUST-001",
        amount=79.99,
        order_id="789",
        idempotency_key="operation-123",
    )
    assert result["ok"] is True
    assert result["decision"] == "ALLOW"
    assert refund_count() == 1
