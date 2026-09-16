"""MCP server that exposes business tools behind Gateway policy."""

from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP

from invoke import call_tool_json
from store import init_db

HOST = os.getenv("MCP_HOST", "127.0.0.1")
PORT = int(os.getenv("MCP_PORT", "8080"))

mcp = FastMCP(
    "customer-support-gateway",
    host=HOST,
    port=PORT,
    stateless_http=True,
)


@mcp.tool()
def get_order(order_id: str) -> str:
    """Look up an order by id, including status and delay reason.

    Args:
        order_id: Order identifier, for example "123".
    """
    return call_tool_json("get_order", order_id=order_id)


@mcp.tool()
def get_customer(customer_id: str) -> str:
    """Retrieve customer profile information.

    Args:
        customer_id: Customer identifier, for example "CUST-001".
    """
    return call_tool_json("get_customer", customer_id=customer_id)


@mcp.tool()
def refund_customer(
    customer_id: str,
    amount: float,
    order_id: str,
    idempotency_key: str = "operation-123",
    reason: str = "",
) -> str:
    """Process a customer refund. Amounts above $1000 are denied by Gateway Policy.

    Authorization is enforced by Cedar policy at the Gateway, not by the model prompt.
    Repeating the same idempotency_key returns the original refund instead of creating another.

    Args:
        customer_id: Customer identifier, for example CUST-001.
        amount: Refund amount in USD.
        order_id: Order to refund.
        idempotency_key: Caller-supplied key. Use "operation-123" for the required scenario.
        reason: Optional reason for the refund.
    """
    return call_tool_json(
        "refund_customer",
        customer_id=customer_id,
        amount=amount,
        order_id=order_id,
        idempotency_key=idempotency_key,
        reason=reason,
    )


if __name__ == "__main__":
    init_db()
    mcp.run(transport="streamable-http")
