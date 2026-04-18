from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from .actions.windows_actions import WindowsActionExecutor
from .config import AssistantConfig
from .intent_router import IntentRouter
from .llm.ollama_client import OllamaClient
from .models import AssistantReply, IntentName


@dataclass(slots=True)
class AssistantState:
    chat_mode_until: datetime | None = None


class LocalAssistant:
    def __init__(
        self,
        config: AssistantConfig,
        router: IntentRouter,
        actions: WindowsActionExecutor,
        llm: OllamaClient | None,
        logger: logging.Logger,
    ) -> None:
        self._config = config
        self._router = router
        self._actions = actions
        self._llm = llm
        self._logger = logger
        self._state = AssistantState()

    def handle_text(self, text: str) -> AssistantReply:
        intent = self._router.route(text)
        self._log_event(
            "intent_detected",
            {"intent": intent.name.value, "confidence": intent.confidence, "params": intent.params},
        )

        if intent.name == IntentName.CHAT_MODE_ON:
            self._enable_chat_mode()
            reply = AssistantReply(text="Modo charla activado por unos minutos.", source="router")
            self._log_event("reply", {"source": reply.source, "text": reply.text})
            return reply

        if (
            intent.name != IntentName.UNKNOWN
            and intent.confidence >= self._config.llm_intent_threshold
        ):
            reply = self._actions.execute(intent)
            self._log_event("reply", {"source": reply.source, "text": reply.text})
            return reply

        if self._is_chat_mode_active() or self._config.llm_enabled:
            llm_reply = self._ask_llm(text)
            self._log_event("reply", {"source": llm_reply.source, "text": llm_reply.text})
            return llm_reply

        reply = AssistantReply(
            text="No entendi el comando y el LLM esta desactivado.", source="router"
        )
        self._log_event("reply", {"source": reply.source, "text": reply.text})
        return reply

    def _ask_llm(self, text: str) -> AssistantReply:
        if self._llm is None:
            return AssistantReply(text="LLM no configurado.", source="llm")

        system_prompt = (
            "Eres un asistente local de Windows. Responde breve en espanol, "
            "maximo 3 frases, y prioriza utilidad practica."
        )
        prompt = f"{system_prompt}\n\nUsuario: {text}\nAsistente:"

        try:
            answer = self._llm.chat(prompt)
        except Exception as exc:  # broad on purpose: network/runtime issues
            self._log_event("llm_error", {"error": str(exc)})
            return AssistantReply(text="No pude contactar al LLM local.", source="llm")

        return AssistantReply(text=answer or "Sin respuesta del modelo.", source="llm")

    def _enable_chat_mode(self) -> None:
        self._state.chat_mode_until = datetime.now(UTC) + timedelta(
            seconds=self._config.llm_chat_timeout_seconds
        )

    def _is_chat_mode_active(self) -> bool:
        expires = self._state.chat_mode_until
        return expires is not None and datetime.now(UTC) <= expires

    def _log_event(self, event: str, data: dict[str, object]) -> None:
        self._logger.info("assistant_event", extra={"event": event, "data": data})
