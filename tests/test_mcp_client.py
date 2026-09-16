from mcp_gateway import create_mcp_client, uses_sigv4


def test_localhost_does_not_use_sigv4():
    assert uses_sigv4("http://127.0.0.1:8080/mcp") is False


def test_agentcore_gateway_url_uses_sigv4():
    url = "https://abc.gateway.bedrock-agentcore.eu-west-1.amazonaws.com/mcp"
    assert uses_sigv4(url) is True


def test_local_client_is_unsigned(monkeypatch):
    monkeypatch.setenv("MCP_URL", "http://127.0.0.1:8080/mcp")
    client = create_mcp_client()
    assert client is not None
