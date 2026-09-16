"""Memory that persists user preferences across sessions.

Locally this is a JSON file keyed by actor_id (not session_id).
In AWS, AgentCore Memory with USER_PREFERENCE is used when MEMORY_ID is set.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

PREF_RE = re.compile(
    r"preferred\s+(?:aws\s+)?region\s+is\s+([a-z0-9-]+)",
    re.IGNORECASE,
)

LOCAL_MEMORY_PATH = Path(os.getenv("MEMORY_PATH", ".local/memory.json"))


def _load() -> dict[str, Any]:
    if not LOCAL_MEMORY_PATH.exists():
        return {"actors": {}}
    return json.loads(LOCAL_MEMORY_PATH.read_text(encoding="utf-8"))


def _save(payload: dict[str, Any]) -> None:
    LOCAL_MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOCAL_MEMORY_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def extract_preferences(text: str) -> list[str]:
    found = [f"My preferred AWS region is {match.group(1).lower()}." for match in PREF_RE.finditer(text)]
    if "preferred" in text.lower() and not found:
        found.append(text.strip())
    return found


def remember(actor_id: str, session_id: str, text: str) -> list[str]:
    prefs = extract_preferences(text)
    if not prefs:
        return []
    data = _load()
    actor = data["actors"].setdefault(actor_id, {"preferences": [], "sessions": []})
    for pref in prefs:
        if pref not in actor["preferences"]:
            actor["preferences"].append(pref)
    if session_id not in actor["sessions"]:
        actor["sessions"].append(session_id)
    _save(data)
    return prefs


def recall(actor_id: str, session_id: str | None = None) -> list[str]:
    """Return preferences for the actor. Session id is ignored for long-term memory."""
    del session_id
    actor = _load().get("actors", {}).get(actor_id) or {}
    return list(actor.get("preferences", []))


def memory_prompt_block(actor_id: str) -> str:
    prefs = recall(actor_id)
    if not prefs:
        return "No stored user preferences."
    return "Known user preferences from previous sessions:\n- " + "\n- ".join(prefs)


def get_session_manager(session_id: str, actor_id: str):
    """Use AgentCore Memory in AWS; return None locally so the file backend is used."""
    memory_id = os.getenv("AGENTCORE_MEMORY_ID")
    if not memory_id:
        return None
    try:
        from bedrock_agentcore.memory.integrations.strands.config import (
            AgentCoreMemoryConfig,
            RetrievalConfig,
        )
        from bedrock_agentcore.memory.integrations.strands.session_manager import (
            AgentCoreMemorySessionManager,
        )
    except ImportError:
        return None

    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "eu-west-1"
    config = AgentCoreMemoryConfig(
        memory_id=memory_id,
        session_id=session_id,
        actor_id=actor_id,
        retrieval_config={
            "/preferences/{actorId}/": RetrievalConfig(top_k=5, relevance_score=0.3),
            "/facts/{actorId}/": RetrievalConfig(top_k=5, relevance_score=0.3),
        },
    )
    return AgentCoreMemorySessionManager(config, region)
