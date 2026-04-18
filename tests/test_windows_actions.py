from pathlib import Path
from unittest.mock import patch

from local_assistant.actions.windows_actions import WindowsActionExecutor
from local_assistant.config import AssistantConfig
from local_assistant.models import IntentName, IntentResult


def _config() -> AssistantConfig:
    return AssistantConfig(
        dry_run=True,
        app_whitelist={"discord": "start discord"},
        folder_whitelist={"docs": "%USERPROFILE%\\Documents"},
    )


def test_open_app_allowed_dry_run() -> None:
    executor = WindowsActionExecutor(_config())
    intent = IntentResult(name=IntentName.OPEN_APP, confidence=0.95, params={"app": "discord"})

    reply = executor.execute(intent)

    assert reply.source == "actions"
    assert "[dry-run]" in reply.text


def test_open_app_rejected_if_not_whitelisted() -> None:
    executor = WindowsActionExecutor(_config())
    intent = IntentResult(name=IntentName.OPEN_APP, confidence=0.95, params={"app": "powershell"})

    reply = executor.execute(intent)

    assert "lista blanca" in reply.text


def test_open_folder_path_not_found() -> None:
    cfg = AssistantConfig(
        dry_run=True,
        app_whitelist={},
        folder_whitelist={"tmp": "%USERPROFILE%\\NoExiste"},
    )
    executor = WindowsActionExecutor(cfg)

    def _always_false(self: Path) -> bool:
        return False

    with patch.object(Path, "exists", _always_false):
        intent = IntentResult(
            name=IntentName.OPEN_FOLDER, confidence=0.95, params={"folder": "tmp"}
        )
        reply = executor.execute(intent)

    assert "no existe" in reply.text.lower()
