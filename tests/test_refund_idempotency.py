from gateway.invoke import call_tool
from gateway.store import refund_count


def test_retry_with_same_idempotency_key_does_not_duplicate():
    first = call_tool(
        "refund_customer",
        customer_id="CUST-001",
        amount=249.99,
        order_id="123",
        idempotency_key="operation-123",
    )
    second = call_tool(
        "refund_customer",
        customer_id="CUST-001",
        amount=249.99,
        order_id="123",
        idempotency_key="operation-123",
        reason="client retry",
    )
    assert first["ok"] is True
    assert first["replayed"] is False
    assert second["replayed"] is True
    assert first["refund"]["id"] == second["refund"]["id"]
    assert refund_count() == 1


def test_reused_key_with_different_payload_is_rejected():
    call_tool(
        "refund_customer",
        customer_id="CUST-001",
        amount=249.99,
        order_id="123",
        idempotency_key="operation-123",
    )
    conflict = call_tool(
        "refund_customer",
        customer_id="CUST-001",
        amount=10,
        order_id="123",
        idempotency_key="operation-123",
    )
    assert conflict["error"] == "invalid_parameters"
    assert refund_count() == 1
