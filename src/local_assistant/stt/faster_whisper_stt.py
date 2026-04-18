from __future__ import annotations

from collections.abc import Iterator
from importlib import import_module
from queue import Empty, Queue
from time import monotonic
from typing import Any


class FasterWhisperSTT:
    def __init__(
        self,
        enabled: bool = False,
        model_size: str = "base",
        compute_type: str = "int8",
        device: str = "cpu",
        input_device: str = "default",
        language: str = "es",
        beam_size: int = 5,
        vad_filter: bool = True,
        sample_rate_hz: int = 16_000,
        record_seconds: float = 4.0,
    ) -> None:
        self._enabled = enabled
        self._model_size = model_size
        self._compute_type = compute_type
        self._device = device
        self._input_device = input_device
        self._language = language
        self._beam_size = beam_size
        self._vad_filter = vad_filter
        self._sample_rate_hz = sample_rate_hz
        self._record_seconds = record_seconds
        self._model: Any | None = None

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model

        try:
            faster_whisper = import_module("faster_whisper")
            model_cls = faster_whisper.WhisperModel
        except Exception as exc:
            raise RuntimeError(
                "STT requires faster-whisper. Install with: pip install -e .[voice]"
            ) from exc

        self._model = model_cls(
            self._model_size,
            device=self._device,
            compute_type=self._compute_type,
        )
        return self._model

    def _load_sounddevice(self) -> Any:
        try:
            return import_module("sounddevice")
        except Exception as exc:
            raise RuntimeError(
                "Microphone capture requires sounddevice. Install with: pip install -e .[voice]"
            ) from exc

    def _resolve_input_device(self, sounddevice: Any) -> Any:
        chosen_input: Any
        if self._input_device.lower() == "default":
            default_devices = getattr(sounddevice.default, "device", None)
            if isinstance(default_devices, (tuple, list)) and len(default_devices) >= 1:
                chosen_input = default_devices[0]
            else:
                chosen_input = None
        else:
            chosen_input = self._input_device

        if chosen_input in {-1, "-1"}:
            return None
        return chosen_input

    def _transcribe_audio(self, audio: Any, beam_size: int | None = None) -> str:
        model = self._load_model()
        segments, _info = model.transcribe(
            audio,
            language=self._language,
            vad_filter=self._vad_filter,
            beam_size=beam_size if beam_size is not None else self._beam_size,
        )

        parts: list[str] = []
        for segment in segments:
            text = str(getattr(segment, "text", "")).strip()
            if text:
                parts.append(text)

        return " ".join(parts).strip()

    def _record_audio(self) -> Any:
        sounddevice = self._load_sounddevice()

        chosen_input = self._resolve_input_device(sounddevice)

        try:
            dev_info = sounddevice.query_devices(chosen_input, kind="input")
        except Exception as exc:
            raise RuntimeError(
                "No se pudo abrir el microfono por defecto del sistema. "
                "Revisa permisos de microfono en Windows y dispositivo predeterminado."
            ) from exc

        device_name = str(dev_info.get("name", "unknown"))
        print(f"[stt] Dispositivo de entrada: {device_name}")

        total_samples = int(self._sample_rate_hz * self._record_seconds)
        try:
            audio = sounddevice.rec(
                total_samples,
                samplerate=self._sample_rate_hz,
                channels=1,
                dtype="float32",
                device=chosen_input,
            )
            sounddevice.wait()
        except Exception as exc:
            raise RuntimeError(
                "Fallo la captura de audio. Prueba stt_sample_rate_hz: 48000 "
                "o verifica que el microfono predeterminado este activo."
            ) from exc
        return audio.reshape(-1)

    def stream_transcriptions(
        self,
        chunk_seconds: float = 0.2,
        partial_interval_seconds: float = 0.5,
        silence_seconds: float = 0.8,
        energy_threshold: float = 0.01,
        emit_partials: bool = False,
    ) -> Iterator[tuple[str, bool]]:
        if not self._enabled:
            return

        sounddevice = self._load_sounddevice()
        numpy = import_module("numpy")

        chosen_input = self._resolve_input_device(sounddevice)
        try:
            dev_info = sounddevice.query_devices(chosen_input, kind="input")
        except Exception as exc:
            raise RuntimeError(
                "No se pudo abrir el microfono por defecto del sistema. "
                "Revisa permisos de microfono en Windows y dispositivo predeterminado."
            ) from exc

        device_name = str(dev_info.get("name", "unknown"))
        print(f"[stt] Dispositivo de entrada: {device_name}")

        chunk_samples = max(1, int(self._sample_rate_hz * chunk_seconds))
        chunks: Queue[Any] = Queue()

        def _callback(indata: Any, frames: int, time_info: Any, status: Any) -> None:
            _ = frames
            _ = time_info
            if status:
                return
            chunks.put(indata.copy().reshape(-1))

        speech_chunks: list[Any] = []
        speech_started_at: float | None = None
        last_speech_at: float | None = None
        last_partial_at = monotonic()
        last_partial_text = ""

        try:
            with sounddevice.InputStream(
                samplerate=self._sample_rate_hz,
                channels=1,
                dtype="float32",
                device=chosen_input,
                blocksize=chunk_samples,
                callback=_callback,
            ):
                while True:
                    try:
                        chunk = chunks.get(timeout=1.0)
                    except Empty:
                        continue

                    now = monotonic()
                    rms = float(numpy.sqrt(numpy.mean(numpy.square(chunk))))
                    is_speech = rms >= energy_threshold

                    if is_speech:
                        if speech_started_at is None:
                            speech_started_at = now
                        last_speech_at = now
                        speech_chunks.append(chunk)
                    elif speech_started_at is not None:
                        # Keep short silence tail to avoid clipping word endings.
                        speech_chunks.append(chunk)

                    if (
                        emit_partials
                        and partial_interval_seconds > 0
                        and
                        speech_started_at is not None
                        and speech_chunks
                        and now - last_partial_at >= partial_interval_seconds
                    ):
                        partial_audio = numpy.concatenate(speech_chunks)
                        partial_text = self._transcribe_audio(partial_audio, beam_size=1)
                        if partial_text and partial_text != last_partial_text:
                            last_partial_text = partial_text
                            yield partial_text, False
                        last_partial_at = now

                    if (
                        speech_started_at is not None
                        and last_speech_at is not None
                        and now - last_speech_at >= silence_seconds
                    ):
                        final_audio = numpy.concatenate(speech_chunks)
                        final_text = self._transcribe_audio(final_audio)
                        if final_text:
                            yield final_text, True

                        speech_chunks = []
                        speech_started_at = None
                        last_speech_at = None
                        last_partial_text = ""
        except Exception as exc:
            raise RuntimeError(
                "Fallo la captura de audio en modo streaming. "
                "Revisa microfono y configuracion de audio del sistema."
            ) from exc

    def transcribe(self) -> str:
        if not self._enabled:
            return ""

        self._load_model()
        audio = self._record_audio()
        return self._transcribe_audio(audio)
