from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".venv", "venv", ".local", "__pycache__"}


def test_no_access_keys_or_private_keys_in_source():
    for path in ROOT.rglob("*"):
        if any(part in SKIP for part in path.parts) or not path.is_file():
            continue
        if path.suffix not in {".py", ".json", ".toml", ".md", ".cedar", ".example", ".yml", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert "BEGIN PRIVATE KEY" not in text, path
        assert "AKIA" not in text, path
