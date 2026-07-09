"""Gemini LLM provider (default cloud provider for Phase 0).

Wraps ``google-generativeai`` behind the :class:`LLMProvider` interface with a timeout and
a single retry. The SDK is imported lazily so the app boots (and tests run) even when the
package isn't installed — the factory only instantiates this when a key is present.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class GeminiLLM(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash", *, timeout: float = 20.0) -> None:
        # Lazy import: only required when this provider is actually selected.
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        self._genai = genai
        self._model_name = model
        self._timeout = timeout
        self._model = genai.GenerativeModel(model)

    def complete(self, prompt: str, *, system: Optional[str] = None, max_tokens: int = 512) -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        last_err: Optional[Exception] = None
        for attempt in range(2):  # one retry
            try:
                resp = self._model.generate_content(
                    full_prompt,
                    generation_config={"max_output_tokens": max_tokens, "temperature": 0.3},
                    request_options={"timeout": self._timeout},
                )
                return (resp.text or "").strip()
            except Exception as exc:  # noqa: BLE001 — provider must not leak SDK errors
                last_err = exc
                logger.warning("Gemini attempt %d failed: %s", attempt + 1, exc)
        # Graceful degradation: surface a safe message instead of raising into the request.
        return f"[assistant temporarily unavailable] {last_err}"
