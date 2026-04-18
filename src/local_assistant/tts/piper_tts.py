from __future__ import annotations


class PiperTTS:
    def __init__(self, enabled: bool = False) -> None:
        self._enabled = enabled

    def speak(self, text: str) -> None:
        # MVP stub: integrate Piper binary invocation in phase 2.
        _ = text
        _ = self._enabled
