"""FastAPI application entrypoint.

Wires the Phase 0 routers, CORS for the React dev server, and structured logging. Model
providers are resolved lazily on first request so the app boots instantly even when heavy
vision/LLM deps are absent (they degrade to fallbacks).
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.routers import (
    analyze,
    auth,
    barcode,
    cart,
    chat,
    dashboard,
    history,
    pantry,
    products,
    recipe,
    recommend,
    vision,
    voice,
)

logging.basicConfig(
    level=logging.INFO,
    format='{"level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Best-effort DB init; safe no-op without SQLAlchemy/Postgres.
    try:
        from app.db.database import init_db

        init_db()
    except Exception as exc:  # noqa: BLE001
        logging.getLogger(__name__).info("DB init skipped: %s", exc)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "environment": settings.environment}


app.include_router(analyze.router)
app.include_router(cart.router)
app.include_router(chat.router)
app.include_router(products.router)
app.include_router(vision.router)
app.include_router(barcode.router)
app.include_router(recommend.router)
app.include_router(auth.router)
app.include_router(history.router)
app.include_router(dashboard.router)
app.include_router(pantry.router)
app.include_router(recipe.router)
app.include_router(voice.router)
