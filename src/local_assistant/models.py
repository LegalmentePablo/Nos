from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class IntentName(StrEnum):
    OPEN_APP = "open_app"
    SEARCH_GOOGLE = "search_google"
    SEARCH_YOUTUBE = "search_youtube"
    PLAY_SPOTIFY = "play_spotify"
    MEDIA_PAUSE = "media_pause"
    MEDIA_NEXT = "media_next"
    OPEN_FOLDER = "open_folder"
    CHAT_MODE_ON = "chat_mode_on"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class IntentResult:
    name: IntentName
    confidence: float
    params: dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""


@dataclass(slots=True)
class AssistantReply:
    text: str
    source: str
