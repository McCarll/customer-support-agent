"""Map customer utterances to Gateway tools. Used in tests and as a fallback."""

from __future__ import annotations


def select_tool(prompt: str) -> str:
    text = prompt.lower()
    if "ignore previous" in text or "refund" in text:
        return "refund_customer"
    if "customer" in text or "cust-" in text:
        return "get_customer"
    if "order" in text:
        return "get_order"
    return "unknown"
