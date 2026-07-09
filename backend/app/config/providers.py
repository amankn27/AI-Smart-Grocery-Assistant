"""Provider factory — the one place that maps config → concrete model implementations.

Routers/services ask for `get_llm()` / `get_ocr()` / `get_detector()` and receive an object
satisfying the ABC in ``providers/base.py``. Every factory degrades gracefully: if the
selected implementation can't be constructed (missing key, missing heavy dependency,
missing weights) it logs and returns the safe fallback so the app always boots (brief §3).
"""

from __future__ import annotations

import logging
from functools import lru_cache

from app.config.settings import get_settings
from app.providers.base import Detector, LLMProvider, OCREngine

logger = logging.getLogger(__name__)


@lru_cache
def get_llm() -> LLMProvider:
    s = get_settings()
    from app.providers.llm.echo import EchoLLM

    if s.llm_provider == "gemini" and s.gemini_api_key:
        try:
            from app.providers.llm.gemini import GeminiLLM

            return GeminiLLM(api_key=s.gemini_api_key, model=s.gemini_model)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Gemini unavailable (%s); falling back to echo provider", exc)
    elif s.llm_provider == "gemini":
        logger.info("GEMINI_API_KEY not set; using offline echo LLM provider")
    return EchoLLM()


@lru_cache
def get_ocr() -> OCREngine:
    s = get_settings()
    from app.providers.ocr.engines import ChainedOCR, EasyOCREngine, NullOCREngine, PaddleOCREngine

    lang = s.ocr_lang
    # EasyOCR takes a list; include English alongside a non-English script for bilingual labels.
    easy_langs = [lang] if lang == "en" else [lang, "en"]

    def _try(build, label):
        try:
            return build()
        except Exception as exc:  # noqa: BLE001
            logger.info("OCR engine %s not available: %s", label, exc)
            return None

    def _paddle():
        return PaddleOCREngine(lang=lang)

    def _easy():
        return EasyOCREngine(langs=easy_langs)

    if s.ocr_provider == "paddle":
        return _try(_paddle, "paddle") or NullOCREngine()
    if s.ocr_provider == "easyocr":
        return _try(_easy, "easyocr") or NullOCREngine()
    if s.ocr_provider == "null":
        return NullOCREngine()

    # Default "chained": build whichever engines import successfully, in priority order.
    engines: list[OCREngine] = []
    for build, label in ((_paddle, "paddle"), (_easy, "easyocr")):
        eng = _try(build, label)
        if eng is not None:
            engines.append(eng)
    engines.append(NullOCREngine())
    return ChainedOCR(engines)


@lru_cache
def get_detector() -> Detector:
    s = get_settings()
    from app.providers.detector.yolo import StubDetector, YoloDetector

    if s.detector_provider == "yolo":
        try:
            return YoloDetector(weights=s.yolo_weights, conf_threshold=s.detector_conf_threshold)
        except Exception as exc:  # noqa: BLE001
            logger.warning("YOLO detector unavailable (%s); using stub detector", exc)
    return StubDetector()


@lru_cache
def get_barcode_decoder():
    s = get_settings()
    from app.providers.barcode.engines import NullBarcode, PyzbarDecoder

    if s.barcode_provider == "pyzbar":
        try:
            return PyzbarDecoder()
        except Exception as exc:  # noqa: BLE001
            logger.info("pyzbar unavailable (%s); barcode decoding disabled (manual entry)", exc)
    return NullBarcode()


@lru_cache
def get_embedder():
    s = get_settings()
    from app.providers.embeddings.embedders import HashingEmbedder, SentenceTransformerEmbedder

    if s.embeddings_provider == "sentence_transformers":
        try:
            return SentenceTransformerEmbedder()
        except Exception as exc:  # noqa: BLE001
            logger.info("sentence-transformers unavailable (%s); using hashing embedder", exc)
    return HashingEmbedder()


@lru_cache
def get_stt():
    s = get_settings()
    from app.providers.stt.engines import NullSTT, WhisperSTT

    if s.stt_provider == "whisper":
        try:
            return WhisperSTT(model_size=s.whisper_model)
        except Exception as exc:  # noqa: BLE001
            logger.info("Whisper unavailable (%s); STT disabled (client sends text)", exc)
    return NullSTT()


@lru_cache
def get_tts():
    s = get_settings()
    from app.providers.tts.engines import BrowserTTS, GttsTTS

    if s.tts_provider == "gtts":
        try:
            return GttsTTS()
        except Exception as exc:  # noqa: BLE001
            logger.info("gTTS unavailable (%s); using browser TTS", exc)
    return BrowserTTS()
