import os

from strands.models.bedrock import BedrockModel

DEFAULT_MODEL_ID = "global.anthropic.claude-sonnet-4-5-20250929-v1:0"


def load_model() -> BedrockModel:
    """Create the Bedrock model client from the runtime IAM role or local credential chain."""
    return BedrockModel(
        model_id=os.getenv("BEDROCK_MODEL_ID", DEFAULT_MODEL_ID),
        max_tokens=4096,
    )
