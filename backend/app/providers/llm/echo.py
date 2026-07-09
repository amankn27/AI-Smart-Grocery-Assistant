"""Zero-dependency LLM fallback.

Used when no real provider is configured (no ``GEMINI_API_KEY``) or when the configured
provider errors. It never calls the network, so the API always boots and ``/chat`` never
dead-ends (brief §3). The reply is deterministic and clearly labelled as offline so it is
obvious in the UI/tests that no real model ran.
"""

from __future__ import annotations

from typing import Optional

from app.providers.base import LLMProvider


class EchoLLM(LLMProvider):
    name = "echo"

    def complete(self, prompt: str, *, system: Optional[str] = None, max_tokens: int = 512) -> str:
        question = prompt.strip().splitlines()[-1] if prompt.strip() else ""
        return (
            "[offline assistant] No LLM provider is configured, so I can't reason over this "
            "in detail. Set GEMINI_API_KEY (or another provider in .env) to enable full answers. "
            f'You asked: "{question[:200]}"'
        )
