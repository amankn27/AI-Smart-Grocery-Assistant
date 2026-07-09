"""YOLO product detector behind the :class:`Detector` interface.

Phase 0 uses a **pretrained** Ultralytics checkpoint (no custom training — brief §4).
Stock weights don't know our 12 grocery categories, so detections are surfaced with their
raw label + confidence and the router applies the low-confidence → "ask the user to
confirm" path. Fine-tuning on a labeled grocery set is a measured Phase 1 follow-up.

``ultralytics`` is imported lazily; when it (or a weights file) is unavailable the factory
falls back to :class:`StubDetector` so the endpoint still responds.
"""

from __future__ import annotations

import io
import logging

from app.providers.base import Detection, DetectionResult, Detector

logger = logging.getLogger(__name__)


class YoloDetector(Detector):
    name = "yolo"

    def __init__(self, weights: str = "yolov8n.pt", conf_threshold: float = 0.25) -> None:
        from ultralytics import YOLO  # lazy

        self._model = YOLO(weights)
        self._conf = conf_threshold

    def detect(self, image_bytes: bytes) -> DetectionResult:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        results = self._model.predict(img, conf=self._conf, verbose=False)
        detections: list[Detection] = []
        for r in results:
            names = r.names
            for box in r.boxes:
                cls_id = int(box.cls[0])
                xyxy = tuple(float(v) for v in box.xyxy[0].tolist())
                detections.append(
                    Detection(label=names.get(cls_id, str(cls_id)), confidence=float(box.conf[0]), bbox_xyxy=xyxy)
                )
        return DetectionResult(detections=detections, model=self.name, width=img.width, height=img.height)


class StubDetector(Detector):
    """Zero-dependency fallback: returns a single centered low-confidence box so the UI can
    still prompt the user to confirm the product manually."""

    name = "stub"

    def detect(self, image_bytes: bytes) -> DetectionResult:
        from PIL import Image  # Pillow is a light dep; if even this is missing, size is 0.

        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            w, h = img.width, img.height
        except Exception:  # noqa: BLE001
            w, h = 0, 0
        box = (w * 0.2, h * 0.2, w * 0.8, h * 0.8) if w and h else (0.0, 0.0, 0.0, 0.0)
        return DetectionResult(
            detections=[Detection(label="unknown_product", confidence=0.0, bbox_xyxy=box)],
            model=self.name,
            width=w,
            height=h,
        )
