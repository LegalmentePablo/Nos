from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field


class AssistantConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    llm_enabled: bool = True
    llm_intent_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    llm_chat_timeout_seconds: int = Field(default=180, ge=30, le=3600)
    llm_model: str = "qwen2.5:3b-instruct-q4_K_M"
    ollama_host: str = "http://127.0.0.1:11434"

    dry_run: bool = True

    app_whitelist: dict[str, str] = Field(default_factory=dict)
    folder_whitelist: dict[str, str] = Field(default_factory=dict)


def load_config(config_path: Path) -> AssistantConfig:
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}

    return AssistantConfig.model_validate(data)
