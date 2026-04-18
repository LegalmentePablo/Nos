from __future__ import annotations

from typing import Any

import requests


class OllamaClient:
    def __init__(self, host: str, model: str, timeout_seconds: int = 20) -> None:
        self._host = host.rstrip("/")
        self._model = model
        self._timeout_seconds = timeout_seconds

    def chat(self, prompt: str) -> str:
        url = f"{self._host}/api/generate"
        payload: dict[str, Any] = {
            "model": self._model,
            "prompt": prompt,
            "stream": False,
        }
        response = requests.post(url, json=payload, timeout=self._timeout_seconds)
        response.raise_for_status()
        data = response.json()
        return str(data.get("response", "")).strip()
