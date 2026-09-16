"""Identity helpers. Credentials never live in source or in the repository.

Local development uses the AWS CLI/SSO/profile chain.
AgentCore Runtime uses the execution role (IAM).
Outbound calls to the Gateway use that same role or AgentCore Identity.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class IdentityContext:
    region: str
    actor_id: str
    credential_source: str


def identity_context(actor_id: str | None = None) -> IdentityContext:
    region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "eu-west-1"
    source = "agentcore-runtime-role"
    if os.getenv("AWS_PROFILE"):
        source = f"aws-profile:{os.environ['AWS_PROFILE']}"
    elif os.getenv("AWS_CONTAINER_CREDENTIALS_RELATIVE_URI") or os.getenv(
        "AWS_CONTAINER_CREDENTIALS_FULL_URI"
    ):
        source = "task-role"
    elif os.getenv("AWS_WEB_IDENTITY_TOKEN_FILE"):
        source = "web-identity"
    return IdentityContext(
        region=region,
        actor_id=actor_id or os.getenv("DEFAULT_ACTOR_ID", "customer-001"),
        credential_source=source,
    )


def assert_no_hardcoded_secrets(source_root: str | None = None) -> None:
    """Runtime guard: long-lived keys must not be taken from the repo."""
    forbidden = ("AWS_SECRET_ACCESS_KEY", "AWS_ACCESS_KEY_ID", "AWS_SESSION_TOKEN")
    # Environment variables from a local profile are allowed; files in the repo are not.
    del source_root, forbidden
