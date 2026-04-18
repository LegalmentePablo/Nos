import logging

from local_assistant.assistant import LocalAssistant
from local_assistant.config import AssistantConfig
from local_assistant.models import AssistantReply, IntentName, IntentResult


class FakeRouter:
    def __init__(self, result: IntentResult) -> None:
        self._result = result

    def route(self, text: str) -> IntentResult:
        _ = text
        return self._result


class FakeActions:
    def __init__(self, reply: AssistantReply) -> None:
        self.reply = reply
        self.called = 0

    def execute(self, intent: IntentResult) -> AssistantReply:
        _ = intent
        self.called += 1
        return self.reply

    def try_open_app_from_free_text(self, text: str) -> AssistantReply | None:
        _ = text
        return None


class FakeLlm:
    def __init__(self, response: str = "ok", explode: bool = False) -> None:
        self.response = response
        self.explode = explode
        self.called = 0

    def chat(self, prompt: str) -> str:
        _ = prompt
        self.called += 1
        if self.explode:
            raise RuntimeError("network down")
        return self.response


def _config(llm_enabled: bool = True) -> AssistantConfig:
    return AssistantConfig(
        llm_enabled=llm_enabled,
        llm_intent_threshold=0.8,
        llm_chat_timeout_seconds=180,
        dry_run=True,
        app_whitelist={},
        folder_whitelist={},
    )


def test_local_intent_prefers_actions_over_llm() -> None:
    router = FakeRouter(
        IntentResult(name=IntentName.OPEN_APP, confidence=0.95, params={"app": "discord"})
    )
    actions = FakeActions(AssistantReply(text="abriendo", source="actions"))
    llm = FakeLlm(response="llm")

    assistant = LocalAssistant(_config(), router, actions, llm, logging.getLogger("test"))
    reply = assistant.handle_text("abre discord")

    assert reply.source == "actions"
    assert actions.called == 1
    assert llm.called == 0


def test_unknown_intent_uses_llm_when_enabled() -> None:
    router = FakeRouter(IntentResult(name=IntentName.UNKNOWN, confidence=0.0, params={}))
    actions = FakeActions(AssistantReply(text="unused", source="actions"))
    llm = FakeLlm(response="respuesta llm")

    assistant = LocalAssistant(
        _config(llm_enabled=True), router, actions, llm, logging.getLogger("test")
    )
    reply = assistant.handle_text("haz algo complejo")

    assert reply.source == "llm"
    assert "respuesta" in reply.text
    assert actions.called == 0
    assert llm.called == 1


def test_chat_mode_activation_returns_router_message() -> None:
    router = FakeRouter(IntentResult(name=IntentName.CHAT_MODE_ON, confidence=0.91, params={}))
    actions = FakeActions(AssistantReply(text="unused", source="actions"))

    assistant = LocalAssistant(_config(), router, actions, FakeLlm(), logging.getLogger("test"))
    reply = assistant.handle_text("hablemos un rato")

    assert reply.source == "router"
    assert "modo charla" in reply.text.lower()


def test_llm_failure_returns_safe_message() -> None:
    router = FakeRouter(IntentResult(name=IntentName.UNKNOWN, confidence=0.0, params={}))
    actions = FakeActions(AssistantReply(text="unused", source="actions"))
    llm = FakeLlm(explode=True)

    assistant = LocalAssistant(_config(), router, actions, llm, logging.getLogger("test"))
    reply = assistant.handle_text("dime algo")

    assert reply.source == "llm"
    assert "no pude contactar" in reply.text.lower()


def test_low_information_unknown_text_does_not_call_llm() -> None:
    router = FakeRouter(IntentResult(name=IntentName.UNKNOWN, confidence=0.0, params={}))
    actions = FakeActions(AssistantReply(text="unused", source="actions"))
    llm = FakeLlm(response="no deberia llamarse")

    assistant = LocalAssistant(_config(), router, actions, llm, logging.getLogger("test"))
    reply = assistant.handle_text("pero?")

    assert reply.source == "router"
    assert "no te entendi" in reply.text.lower()
    assert llm.called == 0


def test_filler_only_unknown_text_does_not_call_llm() -> None:
    router = FakeRouter(IntentResult(name=IntentName.UNKNOWN, confidence=0.0, params={}))
    actions = FakeActions(AssistantReply(text="unused", source="actions"))
    llm = FakeLlm(response="no deberia llamarse")

    assistant = LocalAssistant(_config(), router, actions, llm, logging.getLogger("test"))
    reply = assistant.handle_text("por favor")

    assert reply.source == "router"
    assert "no te entendi" in reply.text.lower()
    assert llm.called == 0
