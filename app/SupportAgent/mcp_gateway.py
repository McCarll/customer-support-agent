"""MCP client for local FastMCP or IAM-authenticated AgentCore Gateway."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from identity import identity_context
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient

DEFAULT_MCP_URL = "http://127.0.0.1:8080/mcp"


def gateway_url(url: str | None = None) -> str:
    return url or os.getenv("MCP_URL") or os.getenv("AGENTCORE_GATEWAY_URL") or DEFAULT_MCP_URL


def uses_sigv4(url: str) -> bool:
    return "gateway.bedrock-agentcore" in url


def create_mcp_client(url: str | None = None) -> MCPClient:
    target = gateway_url(url)
    if uses_sigv4(target):
        from mcp_proxy_for_aws.client import aws_iam_streamablehttp_client

        region = identity_context().region
        return MCPClient(
            lambda: aws_iam_streamablehttp_client(
                endpoint=target,
                aws_region=region,
                aws_service="bedrock-agentcore",
            )
        )
    return MCPClient(lambda: streamablehttp_client(target))


@contextmanager
def gateway_tools(url: str | None = None) -> Iterator[tuple[MCPClient, list]]:
    client = create_mcp_client(url)
    with client:
        yield client, client.list_tools_sync()
