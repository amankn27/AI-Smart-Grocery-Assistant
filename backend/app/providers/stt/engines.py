"""Speech-to-text behind an interface.

Whisper (via faster-whisper) is the real engine, imported lazily. When it (or its model) is
unavailable the factory falls back to :class:`NullSTT`, which transcribes nothing so the
client is expected to send typed text instead — the endpoint still responds. XTTS/heavy
models stay deferred (brief §4)."""

from __future__ import annotations

import logging
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Transcript:
    text: str
    language: str = ""
    engine: str = "unknown"


class STTEngine(ABC):
    name: str = "base"

    @abstractmethod
    def transcribe(self, audio_bytes: bytes) -> Transcript:
        raise NotImplementedError


class WhisperSTT(STTEngine):
    name = "whisper"

    def __init__(self, model_size: str = "base") -> None:
        from faster_whisper import WhisperModel  # lazy

        self._model = WhisperModel(model_size, device="cpu", compute_type="int8")

    def transcribe(self, audio_bytes: bytes) -> Transcript:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()
            segments, info = self._model.transcribe(tmp.name)
            text = " ".join(seg.text.strip() for seg in segments).strip()
        return Transcript(text=text, language=getattr(info, "language", ""), engine=self.name)


class NullSTT(STTEngine):
    """Terminal fallback: no transcription → client sends typed text instead."""

    name = "null"

    def transcribe(self, audio_bytes: bytes) -> Transcript:
        return Transcript(text="", engine=self.name)
