"""AgentCore Runtime entrypoint: Strands agent + Gateway MCP + Memory + IAM."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_HERE = Path(__file__).resolve().parent
for _env in (_HERE / ".env", _HERE.parent.parent / ".env"):
    if _env.exists():
        load_dotenv(_env)
        break

from agent import create_agent  # noqa: E402
from bedrock_agentcore.runtime import BedrockAgentCoreApp  # noqa: E402
from identity import identity_context  # noqa: E402
from mcp_gateway import gateway_tools  # noqa: E402
from memory import remember  # noqa: E402

app = BedrockAgentCoreApp()
log = app.logger


def _payload_text(payload: dict, key: str, default: str) -> str:
    value = payload.get(key, default)
    return value if isinstance(value, str) and value.strip() else default


@app.entrypoint
def invoke(payload, context):
    prompt = payload.get("prompt") if isinstance(payload, dict) else None
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("payload.prompt must be a non-empty string")

    session_id = _payload_text(
        payload,
        "session_id",
        getattr(context, "session_id", None) or "local-session",
    )
    actor_id = _payload_text(
        payload,
        "actor_id",
        os.getenv("DEFAULT_ACTOR_ID", "customer-001"),
    )
    identity = identity_context(actor_id)
    log.info(
        "invoke actor=%s session=%s credentials=%s",
        identity.actor_id,
        session_id,
        identity.credential_source,
    )

    stored = remember(actor_id, session_id, prompt)
    if stored:
        log.info("stored preferences %s", stored)

    try:
        with gateway_tools() as (_client, tools):
            agent = create_agent(tools, session_id=session_id, actor_id=actor_id)
            result = agent(prompt)
            return {
                "ok": True,
                "result": str(result),
                "actor_id": actor_id,
                "session_id": session_id,
            }
    except Exception as exc:
        log.exception("invoke failed")
        return {
            "ok": False,
            "error": type(exc).__name__,
            "message": str(exc),
            "actor_id": actor_id,
            "session_id": session_id,
        }


if __name__ == "__main__":
    app.run()
