"""Text-to-speech behind an interface.

Default is :class:`BrowserTTS`, which returns **no** server audio and signals the client to
speak the text with the Web Speech API — zero dependency, works everywhere. gTTS is an
optional server-side engine that returns MP3 bytes. XTTS/custom voices stay deferred.
"""

from __future__ import annotations

import io
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class Speech:
    audio: Optional[bytes]      # None → client should synthesize (browser TTS)
    mime: str
    engine: str


class TTSEngine(ABC):
    name: str = "base"

    @abstractmethod
    def synthesize(self, text: str) -> Speech:
        raise NotImplementedError


class BrowserTTS(TTSEngine):
    """No server audio; the frontend speaks the answer via the Web Speech API."""

    name = "browser"

    def synthesize(self, text: str) -> Speech:
        return Speech(audio=None, mime="text/plain", engine=self.name)


class GttsTTS(TTSEngine):
    name = "gtts"

    def __init__(self, lang: str = "en") -> None:
        from gtts import gTTS  # lazy

        self._gTTS = gTTS
        self._lang = lang

    def synthesize(self, text: str) -> Speech:
        buf = io.BytesIO()
        self._gTTS(text=text, lang=self._lang).write_to_fp(buf)
        return Speech(audio=buf.getvalue(), mime="audio/mpeg", engine=self.name)
