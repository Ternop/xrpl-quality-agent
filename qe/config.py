from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str | None
    base_url: str
    model: str


def openai_config() -> OpenAIConfig:
    return OpenAIConfig(
        api_key=os.getenv("QE_OPENAI_API_KEY"),
        base_url=os.getenv("QE_OPENAI_BASE_URL", "https://api.openai.com/v1"),
        model=os.getenv("QE_OPENAI_MODEL", "gpt-4.1-mini"),
    )
