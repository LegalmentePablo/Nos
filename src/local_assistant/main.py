from __future__ import annotations

import os
from pathlib import Path

from .actions.windows_actions import WindowsActionExecutor
from .assistant import LocalAssistant
from .config import load_config
from .intent_router import IntentRouter
from .llm.ollama_client import OllamaClient
from .logging_setup import setup_logging
from .stt.faster_whisper_stt import FasterWhisperSTT


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


def run_voice_console() -> None:
    config_path = Path(os.getenv("LOCAL_ASSISTANT_CONFIG", "config/settings.yaml"))
    config = load_config(config_path)
    assistant = build_assistant(config_path)
    stt = FasterWhisperSTT(
        enabled=config.stt_enabled,
        model_size=config.stt_model_size,
        compute_type=config.stt_compute_type,
        device=config.stt_device,
        input_device=config.stt_input_device,
        language=config.stt_language,
        beam_size=config.stt_beam_size,
        vad_filter=config.stt_vad_filter,
        sample_rate_hz=config.stt_sample_rate_hz,
        record_seconds=config.stt_record_seconds,
    )

    print("Asistente de voz listo. Habla despues de cada captura.")
    print("Di 'salir' para cerrar.")

    if config.stt_streaming_enabled:
        try:
            for user_text, is_final in stt.stream_transcriptions(
                chunk_seconds=config.stt_chunk_seconds,
                partial_interval_seconds=config.stt_partial_interval_seconds,
                silence_seconds=config.stt_silence_seconds,
                energy_threshold=config.stt_energy_threshold,
                emit_partials=config.stt_emit_partials,
            ):
                if is_final or config.stt_emit_partials:
                    prefix = "[user]" if is_final else "[user~]"
                    print(f"{prefix} {user_text}")

                if not is_final:
                    continue

                if user_text.lower() in {"exit", "quit", "salir"}:
                    print("Cerrando asistente.")
                    return

                reply = assistant.handle_text(user_text)
                print(f"[{reply.source}] {reply.text}")
        except RuntimeError as exc:
            print(f"[stt] Error: {exc}")
            print("Cambiando a modo texto.")
            run_text_console()
        return

    while True:
        print("[stt] Escuchando...")
        try:
            user_text = stt.transcribe()
        except RuntimeError as exc:
            print(f"[stt] Error: {exc}")
            print("Cambiando a modo texto.")
            run_text_console()
            return

        if not user_text:
            continue

        print(f"[user] {user_text}")
        if user_text.lower() in {"exit", "quit", "salir"}:
            print("Cerrando asistente.")
            break

        reply = assistant.handle_text(user_text)
        print(f"[{reply.source}] {reply.text}")


def run_console() -> None:
    config_path = Path(os.getenv("LOCAL_ASSISTANT_CONFIG", "config/settings.yaml"))
    config = load_config(config_path)
    if config.stt_enabled:
        run_voice_console()
        return
    run_text_console()


if __name__ == "__main__":
    run_console()
