"""OCR engines behind one interface, with a graceful fallback chain.

Order (brief §3): PaddleOCR (primary) → EasyOCR (fallback) → Null (manual entry). Heavy
deps (paddleocr, easyocr, numpy, opencv) are imported lazily inside the engines, so the
backend boots and the deterministic tests run without any of them installed. The
:class:`ChainedOCR` engine tries each available engine until one returns usable text.
"""

from __future__ import annotations

import io
import logging
from typing import Optional

from app.providers.base import OCREngine, OCRLine, OCRResult

logger = logging.getLogger(__name__)


def _load_image_array(image_bytes: bytes):
    """Decode bytes to an RGB numpy array (lazy imports)."""
    import numpy as np
    from PIL import Image

    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return np.array(img)


class PaddleOCREngine(OCREngine):
    name = "paddle"

    def __init__(self, lang: str = "en") -> None:
        from paddleocr import PaddleOCR  # lazy

        self._ocr = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)

    def read(self, image_bytes: bytes) -> OCRResult:
        arr = _load_image_array(image_bytes)
        raw = self._ocr.ocr(arr, cls=True)
        lines: list[OCRLine] = []
        for page in raw or []:
            for box, (text, conf) in page or []:
                lines.append(OCRLine(text=text, confidence=float(conf), bbox=box))
        return OCRResult(lines=lines, engine=self.name)


class EasyOCREngine(OCREngine):
    name = "easyocr"

    def __init__(self, langs: Optional[list[str]] = None) -> None:
        import easyocr  # lazy

        self._reader = easyocr.Reader(langs or ["en"], gpu=False)

    def read(self, image_bytes: bytes) -> OCRResult:
        arr = _load_image_array(image_bytes)
        results = self._reader.readtext(arr)
        lines = [OCRLine(text=text, confidence=float(conf), bbox=box) for box, text, conf in results]
        return OCRResult(lines=lines, engine=self.name)


class NullOCREngine(OCREngine):
    """Terminal fallback: returns nothing so the caller routes to manual entry."""

    name = "null"

    def read(self, image_bytes: bytes) -> OCRResult:
        return OCRResult(lines=[], engine=self.name)


class ChainedOCR(OCREngine):
    """Try each engine in order until one yields text; degrade to manual entry."""

    name = "chained"

    def __init__(self, engines: list[OCREngine]) -> None:
        self._engines = engines or [NullOCREngine()]

    def read(self, image_bytes: bytes) -> OCRResult:
        for engine in self._engines:
            try:
                result = engine.read(image_bytes)
            except Exception as exc:  # noqa: BLE001
                logger.warning("OCR engine %s failed, trying next: %s", engine.name, exc)
                continue
            if result.lines:
                return result
        return OCRResult(lines=[], engine="null")
