"""Central configuration, loaded from environment / ``.env`` (brief §8: all toggles via env).

Uses pydantic-settings when available, with a stdlib fallback so the deterministic core and
its tests never hard-depend on pydantic being installed.
"""

from __future__ import annotations

import os
from functools import lru_cache

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        model_config = SettingsConfigDict(env_file=".env", extra="ignore")

        app_name: str = "Smart Grocery Assistant"
        environment: str = "development"

        # --- Providers (swappable) ---
        llm_provider: str = "gemini"           # gemini | echo
        gemini_api_key: str | None = None
        gemini_model: str = "gemini-2.5-flash"

        ocr_provider: str = "chained"          # chained | paddle | easyocr | null
        ocr_lang: str = "en"                   # en | hi | ... (Paddle/EasyOCR language code)
        detector_provider: str = "yolo"        # yolo | stub
        yolo_weights: str = "yolov8n.pt"
        detector_conf_threshold: float = 0.25
        low_confidence_threshold: float = 0.40  # below this → ask user to confirm

        # --- Phase 1 providers ---
        barcode_provider: str = "pyzbar"       # pyzbar | null
        # Open Food Facts fallback for barcodes not in the seed catalog (~3M real products).
        off_enabled: bool = True
        off_base_url: str = "https://world.openfoodfacts.org"
        off_timeout: float = 6.0
        embeddings_provider: str = "hashing"   # sentence_transformers | hashing
        vector_store: str = "memory"           # chroma | memory
        rag_corpus_path: str = "data/rag/corpus.jsonl"
        chroma_path: str = "./.chroma"

        # --- Phase 2 providers (voice) ---
        stt_provider: str = "whisper"          # whisper | null
        whisper_model: str = "base"
        tts_provider: str = "browser"          # browser | gtts

        # --- Auth (Phase 1 slice 3) ---
        jwt_secret: str = "change-me-in-production"
        jwt_access_ttl_min: int = 30
        jwt_refresh_ttl_days: int = 7

        # --- Data / infra ---
        database_url: str = "sqlite:///./grocery.db"
        redis_url: str | None = None
        seed_products_csv: str = "data/seed/products.csv"

        # --- Locale (brief §2) ---
        currency: str = "INR"
        locale: str = "en_IN"

        # --- CORS (comma-separated allowed origins for the frontend) ---
        cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

except ImportError:  # pragma: no cover - fallback when pydantic-settings absent
    class Settings:  # type: ignore[no-redef]
        def __init__(self) -> None:
            g = os.getenv
            self.app_name = g("APP_NAME", "Smart Grocery Assistant")
            self.environment = g("ENVIRONMENT", "development")
            self.llm_provider = g("LLM_PROVIDER", "gemini")
            self.gemini_api_key = g("GEMINI_API_KEY")
            self.gemini_model = g("GEMINI_MODEL", "gemini-2.5-flash")
            self.ocr_provider = g("OCR_PROVIDER", "chained")
            self.ocr_lang = g("OCR_LANG", "en")
            self.detector_provider = g("DETECTOR_PROVIDER", "yolo")
            self.yolo_weights = g("YOLO_WEIGHTS", "yolov8n.pt")
            self.detector_conf_threshold = float(g("DETECTOR_CONF_THRESHOLD", "0.25"))
            self.low_confidence_threshold = float(g("LOW_CONFIDENCE_THRESHOLD", "0.40"))
            self.barcode_provider = g("BARCODE_PROVIDER", "pyzbar")
            self.off_enabled = g("OFF_ENABLED", "true").lower() not in ("0", "false", "no")
            self.off_base_url = g("OFF_BASE_URL", "https://world.openfoodfacts.org")
            self.off_timeout = float(g("OFF_TIMEOUT", "6.0"))
            self.embeddings_provider = g("EMBEDDINGS_PROVIDER", "hashing")
            self.vector_store = g("VECTOR_STORE", "memory")
            self.rag_corpus_path = g("RAG_CORPUS_PATH", "data/rag/corpus.jsonl")
            self.chroma_path = g("CHROMA_PATH", "./.chroma")
            self.stt_provider = g("STT_PROVIDER", "whisper")
            self.whisper_model = g("WHISPER_MODEL", "base")
            self.tts_provider = g("TTS_PROVIDER", "browser")
            self.jwt_secret = g("JWT_SECRET", "change-me-in-production")
            self.jwt_access_ttl_min = int(g("JWT_ACCESS_TTL_MIN", "30"))
            self.jwt_refresh_ttl_days = int(g("JWT_REFRESH_TTL_DAYS", "7"))
            self.database_url = g("DATABASE_URL", "sqlite:///./grocery.db")
            self.redis_url = g("REDIS_URL")
            self.seed_products_csv = g("SEED_PRODUCTS_CSV", "data/seed/products.csv")
            self.currency = g("CURRENCY", "INR")
            self.locale = g("LOCALE", "en_IN")
            self.cors_origins = g("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")


@lru_cache
def get_settings() -> "Settings":
    return Settings()
