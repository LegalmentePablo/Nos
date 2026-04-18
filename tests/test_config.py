from pathlib import Path

import pytest
from pydantic import ValidationError

from local_assistant.config import load_config


def test_load_config_happy_path(tmp_path: Path) -> None:
    config_file = tmp_path / "settings.yaml"
    config_file.write_text(
        """
llm_enabled: true
llm_intent_threshold: 0.8
llm_chat_timeout_seconds: 180
llm_model: "qwen2.5:3b-instruct-q4_K_M"
ollama_host: "http://127.0.0.1:11434"
dry_run: true
app_whitelist:
  discord: "start discord"
folder_whitelist:
  documentos: "%USERPROFILE%\\\\Documents"
""".strip(),
        encoding="utf-8",
    )

    cfg = load_config(config_file)

    assert cfg.llm_enabled is True
    assert cfg.llm_intent_threshold == 0.8
    assert cfg.dry_run is True
    assert cfg.app_whitelist["discord"] == "start discord"


def test_load_config_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_config(Path("missing_config.yaml"))


def test_load_config_rejects_unknown_fields(tmp_path: Path) -> None:
    config_file = tmp_path / "settings.yaml"
    config_file.write_text(
        """
llm_enabled: true
unknown_field: 123
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_config(config_file)


def test_load_config_threshold_bounds(tmp_path: Path) -> None:
    config_file = tmp_path / "settings.yaml"
    config_file.write_text(
        """
llm_intent_threshold: 1.5
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValidationError):
        load_config(config_file)
