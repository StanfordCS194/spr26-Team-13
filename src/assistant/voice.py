"""Push-to-talk microphone capture and transcription helpers."""

from __future__ import annotations

import os
import tempfile
import threading
import wave
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    load_dotenv = None

try:
    from openai import OpenAI
except ModuleNotFoundError:
    OpenAI = None

try:
    import sounddevice as sd
except ModuleNotFoundError:
    sd = None

if load_dotenv is not None:
    load_dotenv()

DEFAULT_TRANSCRIBE_MODEL = "gpt-4o-mini-transcribe"
DEFAULT_SAMPLE_RATE = 16000


class VoiceInputUnavailableError(RuntimeError):
    """Raised when local microphone capture or transcription is unavailable."""


class ToggleVoiceRecorder:
    """Record microphone audio between explicit start and stop calls."""

    def __init__(self, *, sample_rate: int = DEFAULT_SAMPLE_RATE) -> None:
        if sd is None:
            raise VoiceInputUnavailableError(
                "Microphone recording requires the sounddevice package. "
                "Install project dependencies, then try again."
            )
        self.sample_rate = sample_rate
        self._chunks: list[bytes] = []
        self._lock = threading.Lock()
        self._stream = None

    @property
    def is_recording(self) -> bool:
        return self._stream is not None

    def start(self) -> None:
        if self._stream is not None:
            return
        with self._lock:
            self._chunks.clear()

        def callback(indata, frames, time, status):
            if status:
                return
            with self._lock:
                self._chunks.append(indata.copy().tobytes())

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            callback=callback,
        )
        self._stream.start()

    def stop_to_wav(self, path: Path) -> None:
        if self._stream is None:
            raise VoiceInputUnavailableError("Voice recording has not started.")

        self._stream.stop()
        self._stream.close()
        self._stream = None

        with self._lock:
            frames = b"".join(self._chunks)
            self._chunks.clear()

        if not frames:
            raise VoiceInputUnavailableError("No microphone audio was captured.")
        _write_wav(path, frames, sample_rate=self.sample_rate)

    def stop_and_transcribe(self, *, model: str | None = None) -> str:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
            audio_path = Path(handle.name)

        try:
            self.stop_to_wav(audio_path)
            return transcribe_audio_file(audio_path, model=model)
        finally:
            audio_path.unlink(missing_ok=True)


def record_and_transcribe(
    *,
    duration_seconds: float = 4.0,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    model: str | None = None,
) -> str:
    """Record a short microphone clip and return its transcript."""

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
        audio_path = Path(handle.name)

    try:
        record_wav(audio_path, duration_seconds=duration_seconds, sample_rate=sample_rate)
        return transcribe_audio_file(audio_path, model=model)
    finally:
        audio_path.unlink(missing_ok=True)


def record_wav(
    path: Path,
    *,
    duration_seconds: float,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
) -> None:
    """Record mono microphone input to a WAV file."""

    if sd is None:
        raise VoiceInputUnavailableError(
            "Microphone recording requires the sounddevice package. "
            "Install project dependencies, then try again."
        )
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be greater than 0")

    frame_count = int(round(duration_seconds * sample_rate))
    audio = sd.rec(frame_count, samplerate=sample_rate, channels=1, dtype="int16")
    sd.wait()

    _write_wav(path, audio.tobytes(), sample_rate=sample_rate)


def _write_wav(path: Path, frames: bytes, *, sample_rate: int) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frames)


def transcribe_audio_file(path: Path, *, model: str | None = None) -> str:
    """Transcribe a WAV file with OpenAI speech-to-text."""

    if OpenAI is None:
        raise VoiceInputUnavailableError("OpenAI package is not installed.")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise VoiceInputUnavailableError("OPENAI_API_KEY is required for voice transcription.")

    client = OpenAI(api_key=api_key)
    with path.open("rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model=model or os.getenv("OPENAI_TRANSCRIBE_MODEL", DEFAULT_TRANSCRIBE_MODEL),
            file=audio_file,
        )

    text = getattr(transcript, "text", "")
    return str(text).strip()
