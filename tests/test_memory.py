from memory import recall, remember


def test_preference_survives_a_new_session():
    stored = remember(
        "customer-001",
        "session-one",
        "My preferred AWS region is eu-west-1.",
    )
    assert stored
    recalled = recall("customer-001", "session-two")
    assert any("eu-west-1" in item for item in recalled)


def test_preferences_are_scoped_to_actor():
    remember("customer-001", "s1", "My preferred AWS region is eu-west-1.")
    assert recall("customer-002", "s2") == []
