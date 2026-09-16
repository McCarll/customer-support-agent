from loop_guard import LoopGuard


def test_loop_guard_stops_identical_failures():
    guard = LoopGuard(max_identical_failures=2)
    assert guard.record_failure("get_order", "Timeout") is False
    assert guard.record_failure("get_order", "Timeout") is True
    assert guard.stopped is True
    assert "get_order" in guard.reason


def test_loop_guard_resets_on_success():
    guard = LoopGuard(max_identical_failures=2)
    guard.record_failure("get_order", "Timeout")
    guard.record_success()
    assert guard.record_failure("get_order", "Timeout") is False
