from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import patch

from local_assistant.main import build_assistant


def test_build_assistant_wires_components_from_yaml(tmp_path: Path) -> None:
    config_file = tmp_path / "settings.yaml"
    config_file.write_text(
        """
llm_enabled: false
llm_intent_threshold: 0.8
llm_chat_timeout_seconds: 180
llm_model: "qwen2.5:3b-instruct-q4_K_M"
ollama_host: "http://127.0.0.1:11434"
dry_run: true
app_whitelist:
  discord: "start discord"
folder_whitelist:
  descargas: "%USERPROFILE%\\\\Downloads"
""".strip(),
        encoding="utf-8",
    )

    logger = logging.getLogger("test.build")

    with patch("local_assistant.main.setup_logging", return_value=logger):
        assistant = build_assistant(config_file)

    local_reply = assistant.handle_text("abre discord")
    unknown_reply = assistant.handle_text("organiza mi tarde")

    assert local_reply.source == "actions"
    assert "[dry-run]" in local_reply.text
    assert unknown_reply.source == "router"
    assert "llm esta desactivado" in unknown_reply.text.lower()


def test_build_assistant_wires_llm_enabled_with_mocked_client(tmp_path: Path) -> None:
    config_file = tmp_path / "settings_llm.yaml"
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
  descargas: "%USERPROFILE%\\\\Downloads"
""".strip(),
        encoding="utf-8",
    )

    class FakeOllamaClient:
        def __init__(self, host: str, model: str) -> None:
            self.host = host
            self.model = model

        def chat(self, prompt: str) -> str:
            _ = prompt
            return "respuesta llm mock"

    logger = logging.getLogger("test.build.llm")

    with (
        patch("local_assistant.main.setup_logging", return_value=logger),
        patch("local_assistant.main.OllamaClient", FakeOllamaClient),
    ):
        assistant = build_assistant(config_file)

    reply = assistant.handle_text("organiza mi tarde")

    assert reply.source == "llm"
    assert reply.text == "respuesta llm mock"
