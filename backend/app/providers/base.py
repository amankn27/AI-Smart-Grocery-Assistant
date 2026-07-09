"""Abstract interfaces every model provider implements.

Business logic depends only on these ABCs, never on a concrete SDK. The factory in
``app/config/providers.py`` selects an implementation from environment settings, so the
LLM, OCR engine, and detector are all swappable without touching routers or services
(brief §3, "every model call behind an interface").

Each interface is deliberately narrow and returns plain dataclasses so a fallback/stub
implementation is a few lines — that is what keeps "graceful degradation" cheap.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


# --------------------------------------------------------------------------- LLM
class LLMProvider(ABC):
    """Text-in / text-out chat completion. Vision Q&A is a Phase 1 extension."""

    name: str = "base"

    @abstractmethod
    def complete(self, prompt: str, *, system: Optional[str] = None, max_tokens: int = 512) -> str:
        """Return a completion string. Implementations must not raise on transient
        failures — wrap timeouts/retries internally and degrade to a useful message."""
        raise NotImplementedError


# --------------------------------------------------------------------------- OCR
@dataclass
class OCRLine:
    text: str
    confidence: float
    bbox: Optional[list[list[float]]] = None  # 4-point polygon, image pixel coords


@dataclass
class OCRResult:
    lines: list[OCRLine] = field(default_factory=list)
    engine: str = "unknown"

    @property
    def text(self) -> str:
        return "\n".join(line.text for line in self.lines)

    @property
    def mean_confidence(self) -> float:
        if not self.lines:
            return 0.0
        return sum(line.confidence for line in self.lines) / len(self.lines)


class OCREngine(ABC):
    name: str = "base"

    @abstractmethod
    def read(self, image_bytes: bytes) -> OCRResult:
        """Extract text from raw image bytes (PNG/JPEG)."""
        raise NotImplementedError


# ---------------------------------------------------------------------- Detector
@dataclass
class Detection:
    label: str
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]  # pixel coords


@dataclass
class DetectionResult:
    detections: list[Detection] = field(default_factory=list)
    model: str = "unknown"
    width: int = 0
    height: int = 0

    @property
    def top(self) -> Optional[Detection]:
        return max(self.detections, key=lambda d: d.confidence, default=None)


class Detector(ABC):
    name: str = "base"

    @abstractmethod
    def detect(self, image_bytes: bytes) -> DetectionResult:
        """Detect products in raw image bytes and return boxes + confidence + label."""
        raise NotImplementedError
