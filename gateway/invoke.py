"""Single Gateway invocation path used by the MCP server and by tests."""

from __future__ import annotations

from typing import Any

from .observability import new_trace_id, span
from .policy import PolicyDecision, evaluate
from .retries import retry_with_backoff
from .store import InvalidToolParameters, dump_json, get_customer, get_order, refund_customer

_IMPLEMENTATIONS = {
    "get_order": lambda **kw: get_order(order_id=kw["order_id"]),
    "get_customer": lambda **kw: get_customer(customer_id=kw["customer_id"]),
    "refund_customer": lambda **kw: refund_customer(
        customer_id=kw["customer_id"],
        amount=kw["amount"],
        order_id=kw["order_id"],
        idempotency_key=kw.get("idempotency_key") or "",
        reason=kw.get("reason", ""),
    ),
}


def call_tool(tool_name: str, **kwargs: Any) -> dict[str, Any]:
    trace_id = new_trace_id()
    with span(
        "gateway.policy.evaluate",
        trace_id=trace_id,
        attributes={"tool": tool_name, "arguments": kwargs},
    ) as policy_span:
        decision: PolicyDecision = evaluate(tool_name, kwargs)
        policy_span["attributes"]["decision"] = decision.decision
        if decision.decision == "DENY":
            policy_span["status"] = "ERROR"
            policy_span["error"] = decision.reason
            return {
                "ok": False,
                "authorized": False,
                "decision": "DENY",
                "reason": decision.reason,
                "policy": decision.matched_rule,
                "tool": decision.tool_name,
                "trace_id": trace_id,
            }

    implementation = _IMPLEMENTATIONS.get(tool_name)
    if implementation is None:
        return {
            "ok": False,
            "error": "unknown_tool",
            "decision": "DENY",
            "authorized": False,
            "tool": tool_name,
            "trace_id": trace_id,
        }

    with span(
        f"tool.{tool_name}",
        trace_id=trace_id,
        attributes={
            "tool": tool_name,
            "idempotency_key": kwargs.get("idempotency_key"),
        },
    ) as tool_span:
        try:
            result = retry_with_backoff(lambda: implementation(**kwargs))
        except InvalidToolParameters as exc:
            tool_span["status"] = "ERROR"
            tool_span["error"] = str(exc)
            return {
                "ok": False,
                "error": "invalid_parameters",
                "message": str(exc),
                "tool": tool_name,
                "trace_id": trace_id,
            }
        except Exception as exc:
            tool_span["status"] = "ERROR"
            tool_span["error"] = f"{type(exc).__name__}: {exc}"
            return {
                "ok": False,
                "error": type(exc).__name__,
                "message": str(exc),
                "tool": tool_name,
                "trace_id": trace_id,
            }
        tool_span["attributes"]["replayed"] = result.get("replayed")
        tool_span["attributes"]["idempotency_key"] = kwargs.get("idempotency_key")
    return {
        "ok": True,
        "authorized": True,
        "decision": "ALLOW",
        "trace_id": trace_id,
        **result,
    }


def call_tool_json(tool_name: str, **kwargs: Any) -> str:
    return dump_json(call_tool(tool_name, **kwargs))
