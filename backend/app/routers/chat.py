"""/chat — single configurable LLM Q&A endpoint (brief §4).

Grounds the model with any product/nutrition context passed by the UI so answers like
"Is this healthy?" / "How much protein?" are about the scanned item. The provider is
resolved from config and degrades to the offline echo provider when no key is set.
"""

from __future__ import annotations

import json

from fastapi import APIRouter

from app.config.providers import get_llm
from app.schemas.models import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])

SYSTEM_PROMPT = (
    "You are a concise grocery health assistant for shoppers in India (prices in INR). "
    "Answer in 1-3 sentences. If nutrition context is provided, ground your answer in it. "
    "Do not invent nutrition numbers that are not in the context."
)


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    llm = get_llm()
    context_block = ""
    if req.context:
        context_block = f"Context (product/nutrition):\n{json.dumps(req.context, ensure_ascii=False)}\n\n"
    prompt = f"{context_block}Question: {req.question}"
    answer = llm.complete(prompt, system=SYSTEM_PROMPT, max_tokens=256)
    return ChatResponse(answer=answer, provider=llm.name)
