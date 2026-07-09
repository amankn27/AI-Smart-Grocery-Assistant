"""Barcode/QR decoding behind an interface, with a manual-entry fallback.

pyzbar (which needs the native zbar lib) is imported lazily; when it isn't available the
factory falls back to :class:`NullBarcode`, which decodes nothing so the caller routes to
manual entry — the endpoint still responds (graceful degradation, brief §3).
"""

from __future__ import annotations

import io
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Barcode:
    value: str
    type: str  # EAN13 | UPCA | QRCODE | ...


class BarcodeDecoder(ABC):
    name: str = "base"

    @abstractmethod
    def decode(self, image_bytes: bytes) -> list[Barcode]:
        raise NotImplementedError


class PyzbarDecoder(BarcodeDecoder):
    name = "pyzbar"

    def __init__(self) -> None:
        from pyzbar import pyzbar  # lazy; raises if zbar/pyzbar absent

        self._pyzbar = pyzbar

    def decode(self, image_bytes: bytes) -> list[Barcode]:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        results = self._pyzbar.decode(img)
        return [Barcode(value=r.data.decode("utf-8", "ignore"), type=r.type) for r in results]


class NullBarcode(BarcodeDecoder):
    """Terminal fallback: decodes nothing → caller falls back to manual entry."""

    name = "null"

    def decode(self, image_bytes: bytes) -> list[Barcode]:
        return []
