import logging

from local_assistant.actions.windows_actions import WindowsActionExecutor
from local_assistant.assistant import LocalAssistant
from local_assistant.config import AssistantConfig
from local_assistant.intent_router import IntentRouter


class FakeLlm:
    def __init__(self, response: str = "ok") -> None:
        self.response = response
        self.calls = 0

    def chat(self, prompt: str) -> str:
        _ = prompt
        self.calls += 1
        return self.response


def _base_config() -> AssistantConfig:
    return AssistantConfig(
        llm_enabled=False,
        llm_intent_threshold=0.8,
        llm_chat_timeout_seconds=180,
        dry_run=True,
        app_whitelist={"discord": "start discord"},
        folder_whitelist={"descargas": "%USERPROFILE%\\Downloads"},
    )


def test_integration_local_command_uses_actions_path() -> None:
    cfg = _base_config()
    assistant = LocalAssistant(
        config=cfg,
        router=IntentRouter(),
        actions=WindowsActionExecutor(cfg),
        llm=None,
        logger=logging.getLogger("test.integration"),
    )

    reply = assistant.handle_text("abre discord")

    assert reply.source == "actions"
    assert "[dry-run]" in reply.text


def test_integration_unknown_command_uses_llm_when_enabled() -> None:
    cfg = _base_config().model_copy(update={"llm_enabled": True})
    llm = FakeLlm(response="respuesta integrada")
    assistant = LocalAssistant(
        config=cfg,
        router=IntentRouter(),
        actions=WindowsActionExecutor(cfg),
        llm=llm,
        logger=logging.getLogger("test.integration"),
    )

    reply = assistant.handle_text("organiza mi tarde")

    assert reply.source == "llm"
    assert reply.text == "respuesta integrada"
    assert llm.calls == 1


def test_integration_chat_mode_keeps_llm_available_temporarily() -> None:
    cfg = _base_config().model_copy(update={"llm_enabled": False})
    llm = FakeLlm(response="seguimos hablando")
    assistant = LocalAssistant(
        config=cfg,
        router=IntentRouter(),
        actions=WindowsActionExecutor(cfg),
        llm=llm,
        logger=logging.getLogger("test.integration"),
    )

    chat_on = assistant.handle_text("hablemos un rato")
    follow_up = assistant.handle_text("que opinas del plan")

    assert chat_on.source == "router"
    assert follow_up.source == "llm"
    assert follow_up.text == "seguimos hablando"
    assert llm.calls == 1


def test_integration_low_confidence_goes_to_llm() -> None:
    cfg = _base_config().model_copy(update={"llm_enabled": True, "llm_intent_threshold": 0.99})
    llm = FakeLlm(response="fallback por confianza")
    assistant = LocalAssistant(
        config=cfg,
        router=IntentRouter(),
        actions=WindowsActionExecutor(cfg),
        llm=llm,
        logger=logging.getLogger("test.integration"),
    )

    reply = assistant.handle_text("abre discord")

    assert reply.source == "llm"
    assert reply.text == "fallback por confianza"
    assert llm.calls == 1
