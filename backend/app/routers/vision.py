"""/detect and /ocr — the probabilistic vision edges.

Both accept an uploaded image, run the configured provider (or its fallback), and apply the
graceful-degradation rules: low-confidence detections are flagged ``needs_confirmation`` so
the UI asks the user, and OCR output is immediately handed to the deterministic
:func:`parse_nutrition` so the client gets a structured object plus confidence flags.
"""

from __future__ import annotations

from fastapi import APIRouter, File, UploadFile

from app.config.providers import get_detector, get_ocr
from app.config.settings import get_settings
from app.schemas.models import DetectionOut, DetectResponse, OcrResponse
from app.services.nutrition import parse_nutrition

router = APIRouter(tags=["vision"])


@router.post("/detect", response_model=DetectResponse)
async def detect(image: UploadFile = File(...)) -> DetectResponse:
    data = await image.read()
    detector = get_detector()
    result = detector.detect(data)
    threshold = get_settings().low_confidence_threshold
    return DetectResponse(
        model=result.model,
        width=result.width,
        height=result.height,
        detections=[
            DetectionOut(
                label=d.label,
                confidence=round(d.confidence, 3),
                bbox_xyxy=list(d.bbox_xyxy),
                needs_confirmation=d.confidence < threshold,
            )
            for d in result.detections
        ],
    )


@router.post("/ocr", response_model=OcrResponse)
async def ocr(image: UploadFile = File(...)) -> OcrResponse:
    data = await image.read()
    engine = get_ocr()
    result = engine.read(data)
    facts = parse_nutrition(result.text)
    return OcrResponse(
        engine=result.engine,
        text=result.text,
        mean_confidence=round(result.mean_confidence, 3),
        nutrition=facts.as_dict(),
    )
