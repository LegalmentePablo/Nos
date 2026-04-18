from pathlib import Path
from unittest.mock import patch

from local_assistant.actions.windows_actions import WindowsActionExecutor
from local_assistant.config import AssistantConfig
from local_assistant.models import IntentName, IntentResult


def _config() -> AssistantConfig:
    return AssistantConfig(
        dry_run=True,
        app_whitelist={"discord": "start discord", "chrome": "start chrome"},
        app_aliases={"google chorme": "chrome"},
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


def test_open_app_alias_google_chorme_maps_to_chrome() -> None:
    executor = WindowsActionExecutor(_config())
    intent = IntentResult(
        name=IntentName.OPEN_APP,
        confidence=0.95,
        params={"app": "google chorme"},
    )

    reply = executor.execute(intent)

    assert "[dry-run]" in reply.text
    assert "start chrome" in reply.text.lower()


def test_open_app_fuzzy_typo_chorme_maps_to_chrome() -> None:
    executor = WindowsActionExecutor(_config())
    intent = IntentResult(name=IntentName.OPEN_APP, confidence=0.95, params={"app": "chorme"})

    reply = executor.execute(intent)

    assert "[dry-run]" in reply.text
    assert "start chrome" in reply.text.lower()


def test_open_app_infers_subset_phrase_google_chrome_to_chrome() -> None:
    executor = WindowsActionExecutor(_config())
    intent = IntentResult(
        name=IntentName.OPEN_APP,
        confidence=0.95,
        params={"app": "ahora google chrome"},
    )

    reply = executor.execute(intent)

    assert "[dry-run]" in reply.text
    assert "start chrome" in reply.text.lower()


def test_open_app_with_trailing_punctuation_maps_to_chrome() -> None:
    executor = WindowsActionExecutor(_config())
    intent = IntentResult(
        name=IntentName.OPEN_APP,
        confidence=0.95,
        params={"app": "Google Chrome."},
    )

    reply = executor.execute(intent)

    assert "[dry-run]" in reply.text
    assert "start chrome" in reply.text.lower()
