from memory import get_session_manager, remember, use_agentcore_memory


def test_agentcore_memory_skips_local_file(monkeypatch):
    monkeypatch.setenv("AGENTCORE_MEMORY_ID", "mem-123")
    assert use_agentcore_memory() is True
    assert remember("customer-001", "s1", "My preferred AWS region is eu-west-1.") == []


def test_session_manager_is_absent_without_memory_id():
    assert get_session_manager("session-1", "customer-001") is None
