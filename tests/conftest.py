from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("TRACE_DIR", str(tmp_path / "traces"))
    monkeypatch.setenv("MEMORY_PATH", str(tmp_path / "memory.json"))
    monkeypatch.setenv("SUPPORT_DB", str(tmp_path / "support.db"))
    monkeypatch.setenv("FAILURE_MODE", "none")
    monkeypatch.setenv("MODEL_PROVIDER", "bedrock")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AGENTCORE_MEMORY_ID", raising=False)
    monkeypatch.delenv("AGENTCORE_POLICY_ENFORCE", raising=False)
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)

    import memory as memory_mod

    from gateway import observability, retries, store

    monkeypatch.setattr(retries.time, "sleep", lambda _seconds: None)
    store.reset_for_tests(tmp_path)
    memory_mod.LOCAL_MEMORY_PATH = tmp_path / "memory.json"
    observability._TRACE_DIR = tmp_path / "traces"
    yield
