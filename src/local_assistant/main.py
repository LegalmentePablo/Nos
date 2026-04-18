from __future__ import annotations

import os
from pathlib import Path

from .actions.windows_actions import WindowsActionExecutor
from .assistant import LocalAssistant
from .config import load_config
from .intent_router import IntentRouter
from .llm.ollama_client import OllamaClient
from .logging_setup import setup_logging


def build_assistant(config_path: Path) -> LocalAssistant:
    config = load_config(config_path)
    logger = setup_logging(Path("logs"))

    llm = None
    if config.llm_enabled:
        llm = OllamaClient(host=config.ollama_host, model=config.llm_model)

    return LocalAssistant(
        config=config,
        router=IntentRouter(),
        actions=WindowsActionExecutor(config),
        llm=llm,
        logger=logger,
    )


def run_text_console() -> None:
    config_path = Path(os.getenv("LOCAL_ASSISTANT_CONFIG", "config/settings.yaml"))
    assistant = build_assistant(config_path)

    print("Asistente local listo. Escribe un comando (exit para salir).")
    while True:
        user_text = input("> ").strip()
        if user_text.lower() in {"exit", "quit", "salir"}:
            print("Cerrando asistente.")
            break
        if not user_text:
            continue

        reply = assistant.handle_text(user_text)
        print(f"[{reply.source}] {reply.text}")


if __name__ == "__main__":
    run_text_console()
