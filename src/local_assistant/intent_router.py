from __future__ import annotations

import re
from dataclasses import dataclass

from .models import IntentName, IntentResult


@dataclass(slots=True)
class PatternRule:
    intent: IntentName
    pattern: re.Pattern[str]
    confidence: float


class IntentRouter:
    def __init__(self) -> None:
        self._rules = [
            PatternRule(
                IntentName.OPEN_APP,
                re.compile(
                    r"\b(?:abre|abrir|inicia|iniciar|ejecuta|ahora)\s+(?P<app>[\w\s.-]+)$",
                    re.I,
                ),
                0.95,
            ),
            PatternRule(
                IntentName.SEARCH_GOOGLE,
                re.compile(r"\b(?:busca|buscar)\s+en\s+google\s+(?P<query>.+)$", re.I),
                0.95,
            ),
            PatternRule(
                IntentName.SEARCH_YOUTUBE,
                re.compile(r"\b(?:busca|buscar)\s+en\s+youtube\s+(?P<query>.+)$", re.I),
                0.95,
            ),
            PatternRule(
                IntentName.PLAY_SPOTIFY,
                re.compile(r"\b(?:pon|reproduce|poner)\s+(?P<query>.+)\s+en\s+spotify$", re.I),
                0.92,
            ),
            PatternRule(
                IntentName.MEDIA_PAUSE, re.compile(r"\b(?:pausa|pausar|deten)\b", re.I), 0.9
            ),
            PatternRule(
                IntentName.MEDIA_NEXT,
                re.compile(r"\b(?:siguiente|next|salta\s+cancion)\b", re.I),
                0.9,
            ),
            PatternRule(
                IntentName.OPEN_FOLDER,
                re.compile(r"\b(?:abre|abrir)\s+carpeta\s+(?P<folder>[\w\s.-]+)$", re.I),
                0.93,
            ),
            PatternRule(
                IntentName.CHAT_MODE_ON,
                re.compile(r"\b(?:hablemos|modo\s+charla|quiero\s+charlar)\b", re.I),
                0.91,
            ),
        ]

    def route(self, text: str) -> IntentResult:
        normalized = text.strip()
        for rule in self._rules:
            match = rule.pattern.search(normalized)
            if not match:
                continue
            params = {k: v.strip() for k, v in match.groupdict().items() if v}
            return IntentResult(
                name=rule.intent,
                confidence=rule.confidence,
                params=params,
                raw_text=normalized,
            )

        return IntentResult(
            name=IntentName.UNKNOWN,
            confidence=0.0,
            params={},
            raw_text=normalized,
        )
