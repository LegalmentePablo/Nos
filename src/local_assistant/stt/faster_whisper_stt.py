from __future__ import annotations


class FasterWhisperSTT:
    def __init__(self, enabled: bool = False) -> None:
        self._enabled = enabled

    def transcribe(self) -> str:
        # MVP stub: integrate streaming microphone transcription in phase 2.
        _ = self._enabled
        return ""
