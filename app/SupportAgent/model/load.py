import os
from typing import Any

from identity import running_on_agentcore

DEFAULT_BEDROCK_MODEL_ID = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"
DEFAULT_OPENAI_MODEL_ID = "gpt-4o"


def provider_name() -> str:
    if running_on_agentcore():
        return "bedrock"
    explicit = os.getenv("MODEL_PROVIDER", "bedrock").strip().lower()
    return explicit or "bedrock"


def load_model() -> Any:
    """Bedrock is the default. OpenAI is local-only when MODEL_PROVIDER=openai."""
    if provider_name() == "openai":
        if running_on_agentcore():
            raise RuntimeError("OpenAI is not allowed on AgentCore Runtime; use Bedrock and IAM")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("MODEL_PROVIDER=openai requires OPENAI_API_KEY")
        from strands.models.openai import OpenAIModel

        return OpenAIModel(
            client_args={"api_key": api_key},
            model_id=os.getenv("OPENAI_MODEL_ID", DEFAULT_OPENAI_MODEL_ID),
            params={"max_tokens": 4096, "temperature": 0.2},
        )

    from strands.models.bedrock import BedrockModel

    return BedrockModel(
        model_id=os.getenv("BEDROCK_MODEL_ID", DEFAULT_BEDROCK_MODEL_ID),
        max_tokens=4096,
    )
