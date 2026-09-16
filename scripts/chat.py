"""Interactive local chat. Starts the Gateway in-process."""

from __future__ import annotations

import sys
import threading
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app" / "SupportAgent"))

from agent import create_agent  # noqa: E402
from mcp_gateway import gateway_tools  # noqa: E402
from memory import remember  # noqa: E402
from model.load import provider_name  # noqa: E402

from gateway.mcp_server import mcp  # noqa: E402
from gateway.store import init_db  # noqa: E402


def start_gateway() -> None:
    init_db()
    mcp.run(transport="streamable-http")


def main() -> None:
    actor_id = "customer-001"
    session_id = f"session-{uuid.uuid4().hex[:8]}"
    print(f"actor_id={actor_id} session_id={session_id} model={provider_name()}")
    print("Type 'new-session' to start a fresh session (memory is kept). Ctrl-C to exit.\n")

    thread = threading.Thread(target=start_gateway, daemon=True)
    thread.start()
    time.sleep(1.0)

    while True:
        try:
            prompt = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not prompt:
            continue
        if prompt == "new-session":
            session_id = f"session-{uuid.uuid4().hex[:8]}"
            print(f"started {session_id} (same actor, long-term memory kept)")
            continue
        remember(actor_id, session_id, prompt)
        with gateway_tools() as (_client, tools):
            agent = create_agent(tools, session_id=session_id, actor_id=actor_id)
            print("agent>", agent(prompt))


if __name__ == "__main__":
    main()
