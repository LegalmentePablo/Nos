from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from local_assistant.stt.faster_whisper_stt import FasterWhisperSTT


def test_transcribe_returns_empty_when_disabled() -> None:
    stt = FasterWhisperSTT(enabled=False)
    assert stt.transcribe() == ""


def test_transcribe_uses_mocked_whisper_and_audio_capture() -> None:
    fake_segment = Mock()
    fake_segment.text = " hola mundo "

    fake_model = Mock()
    fake_model.transcribe.return_value = ([fake_segment], {})

    fake_whisper_module = Mock()
    fake_whisper_module.WhisperModel.return_value = fake_model

    fake_audio = Mock()
    fake_audio.reshape.return_value = [0.1, 0.2, 0.3]

    fake_sounddevice = Mock()
    fake_sounddevice.rec.return_value = fake_audio

    def fake_import(name: str) -> object:
        if name == "faster_whisper":
            return fake_whisper_module
        if name == "sounddevice":
            return fake_sounddevice
        raise ModuleNotFoundError(name)

    stt = FasterWhisperSTT(enabled=True)
    with patch("local_assistant.stt.faster_whisper_stt.import_module", side_effect=fake_import):
        text = stt.transcribe()

    assert text == "hola mundo"
    fake_sounddevice.rec.assert_called_once()
    fake_sounddevice.wait.assert_called_once()
    fake_model.transcribe.assert_called_once()


def test_transcribe_raises_clear_error_if_dependencies_missing() -> None:
    stt = FasterWhisperSTT(enabled=True)

    with patch(
        "local_assistant.stt.faster_whisper_stt.import_module",
        side_effect=ModuleNotFoundError("missing"),
    ):
        with pytest.raises(RuntimeError, match="faster-whisper"):
            stt.transcribe()
