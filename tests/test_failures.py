import json
from pathlib import Path

from invoke import call_tool


def _spans(tmp_path: Path) -> list[dict]:
    path = tmp_path / "traces" / "spans.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_invalid_parameters_are_traced(tmp_path):
    result = call_tool("get_order", order_id="")
    assert result["error"] == "invalid_parameters"
    names = {span["name"] for span in _spans(tmp_path)}
    assert "gateway.policy.evaluate" in names
    assert "tool.get_order" in names


def test_timeout_failure_is_traced(tmp_path, monkeypatch):
    monkeypatch.setenv("FAILURE_MODE", "timeout")
    result = call_tool("get_order", order_id="123")
    assert result["ok"] is False
    assert "Timeout" in result["error"]
    tool_spans = [span for span in _spans(tmp_path) if span["name"] == "tool.get_order"]
    assert tool_spans


def test_http_500_failure_is_traced(tmp_path, monkeypatch):
    monkeypatch.setenv("FAILURE_MODE", "http_500")
    result = call_tool(
        "refund_customer",
        customer_id="CUST-001",
        amount=10,
        order_id="123",
        idempotency_key="http-500",
    )
    assert result["ok"] is False
    assert "RetryableBackendError" in result["error"] or "HTTP 500" in result.get("message", "")


def test_wrong_tool_selection_is_denied_and_traced(tmp_path):
    result = call_tool("delete_account", customer_id="CUST-001")
    assert result["decision"] == "DENY"
    assert result["authorized"] is False
    policy_spans = [span for span in _spans(tmp_path) if span["name"] == "gateway.policy.evaluate"]
    assert policy_spans
    assert policy_spans[0]["attributes"]["decision"] == "DENY"
