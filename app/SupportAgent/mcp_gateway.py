"""MCP client that talks to AgentCore Gateway (AWS) or the local Gateway process."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient

MCP_URL = os.getenv("MCP_URL", "http://127.0.0.1:8080/mcp")


def create_mcp_client(url: str | None = None) -> MCPClient:
    target = url or MCP_URL
    return MCPClient(lambda: streamablehttp_client(target))


@contextmanager
def gateway_tools(url: str | None = None) -> Iterator[tuple[MCPClient, list]]:
    client = create_mcp_client(url)
    with client:
        yield client, client.list_tools_sync()
