from pathlib import Path

from identity import assert_no_hardcoded_secrets

ROOT = Path(__file__).resolve().parents[1]


def test_no_access_keys_or_private_keys_in_source():
    assert_no_hardcoded_secrets(ROOT)
