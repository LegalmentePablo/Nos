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

    stt_enabled: bool = False
    stt_model_size: str = "base"
    stt_compute_type: str = "int8"
    stt_device: str = "cpu"
    stt_input_device: str = "default"
    stt_language: str = "es"
    stt_beam_size: int = Field(default=5, ge=1, le=10)
    stt_vad_filter: bool = True
    stt_sample_rate_hz: int = Field(default=16_000, ge=8_000, le=48_000)
    stt_record_seconds: float = Field(default=4.0, gt=0.2, le=15.0)
    stt_streaming_enabled: bool = True
    stt_emit_partials: bool = False
    stt_chunk_seconds: float = Field(default=0.2, ge=0.05, le=1.0)
    stt_partial_interval_seconds: float = Field(default=0.5, ge=0.1, le=3.0)
    stt_silence_seconds: float = Field(default=0.8, ge=0.2, le=3.0)
    stt_energy_threshold: float = Field(default=0.01, ge=0.001, le=0.2)

    app_whitelist: dict[str, str] = Field(default_factory=dict)
    app_aliases: dict[str, str] = Field(default_factory=dict)
    folder_whitelist: dict[str, str] = Field(default_factory=dict)


def load_config(config_path: Path) -> AssistantConfig:
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}

    return AssistantConfig.model_validate(data)
