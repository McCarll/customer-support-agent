"""Identity: default credential chain only. No long-lived keys in source."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

LIVE_OPENAI_KEY = re.compile(r"sk-(?:proj-)?[A-Za-z0-9]{20,}")
LIVE_AWS_ACCESS_KEY = re.compile(r"AKIA[0-9A-Z]{16}")
PRIVATE_KEY_MARKER = "BEGIN PRIVATE " + "KEY"

SKIP_DIR_NAMES = {".git", ".venv", "venv", ".local", "__pycache__", ".pytest_cache"}
SCAN_SUFFIXES = {".py", ".json", ".toml", ".md", ".cedar", ".example", ".yml", ".txt"}


@dataclass(frozen=True)
class IdentityContext:
    region: str
    actor_id: str
    credential_source: str


def running_on_agentcore() -> bool:
    return bool(
        os.getenv("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI")
        or os.getenv("AWS_CONTAINER_CREDENTIALS_FULL_URI")
        or os.getenv("BEDROCK_AGENTCORE_RUNTIME")
    )


def identity_context(actor_id: str | None = None) -> IdentityContext:
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "eu-west-1"
    source = "agentcore-runtime-role" if running_on_agentcore() else "aws-credential-chain"
    if os.getenv("AWS_PROFILE"):
        source = f"aws-profile:{os.environ['AWS_PROFILE']}"
    elif os.getenv("AWS_WEB_IDENTITY_TOKEN_FILE"):
        source = "web-identity"
    elif os.getenv("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI") or os.getenv(
        "AWS_CONTAINER_CREDENTIALS_FULL_URI"
    ):
        source = "task-role"
    return IdentityContext(
        region=region,
        actor_id=actor_id or os.getenv("DEFAULT_ACTOR_ID", "customer-001"),
        credential_source=source,
    )


def assert_no_hardcoded_secrets(source_root: str | Path | None = None) -> None:
    """Fail if committed files contain live OpenAI or AWS keys."""
    root = Path(source_root) if source_root else Path(__file__).resolve().parents[2]
    for path in root.rglob("*"):
        if any(part in SKIP_DIR_NAMES for part in path.parts) or not path.is_file():
            continue
        if path.suffix not in SCAN_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if PRIVATE_KEY_MARKER in text:
            raise RuntimeError(f"private key material in {path}")
        if LIVE_AWS_ACCESS_KEY.search(text):
            raise RuntimeError(f"AWS access key id in {path}")
        if LIVE_OPENAI_KEY.search(text):
            raise RuntimeError(f"OpenAI API key in {path}")
