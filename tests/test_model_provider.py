from model.load import provider_name


def test_default_provider_is_bedrock(monkeypatch):
    monkeypatch.delenv("MODEL_PROVIDER", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "present-but-ignored")
    assert provider_name() == "bedrock"


def test_openai_requires_explicit_provider(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "openai")
    assert provider_name() == "openai"


def test_agentcore_runtime_forces_bedrock(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "openai")
    monkeypatch.setenv("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI", "/v2/credentials")
    assert provider_name() == "bedrock"
