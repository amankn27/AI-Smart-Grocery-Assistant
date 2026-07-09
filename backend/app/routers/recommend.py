"""/recommend — healthier alternatives (deterministic) + RAG-grounded explanation (LLM).

The alternatives are computed by :func:`rank_alternatives` over the catalog; the RAG
retriever pulls relevant nutrition guidance, and the LLM turns retrieved facts + the score
comparison into a short explanation. With no LLM key the explanation degrades to a
deterministic summary — the ranked alternatives are always real.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config.providers import get_llm
from app.rag.index import get_retriever
from app.services.catalog import get_catalog
from app.services.recommend import rank_alternatives

router = APIRouter(tags=["recommend"])


class RecommendRequest(BaseModel):
    product_id: str | None = None
    barcode: str | None = None
    limit: int = 3


@router.post("/recommend")
def recommend(req: RecommendRequest) -> dict:
    catalog = get_catalog()
    target = catalog.by_id(req.product_id) if req.product_id else None
    if target is None and req.barcode:
        target = catalog.by_barcode(req.barcode)
    if target is None:
        raise HTTPException(status_code=404, detail="Product not found in catalog")

    alternatives = rank_alternatives(target, catalog.all(), limit=req.limit)

    # Retrieve grounding snippets for the target's category / main issues.
    retriever = get_retriever()
    query = f"healthier alternative to {target.category} high sugar sodium fat {target.name}"
    snippets = retriever.retrieve(query, k=3)

    explanation = _explain(target, alternatives, snippets)

    return {
        "target": {"product_id": target.product_id, "name": target.name, "category": target.category},
        "alternatives": [a.as_dict() for a in alternatives],
        "explanation": explanation["text"],
        "explanation_provider": explanation["provider"],
        "sources": [{"id": s.id, "score": round(s.score, 3), **s.metadata} for s in snippets],
    }


def _explain(target, alternatives, snippets) -> dict:
    if not alternatives:
        return {"text": f"No clearly healthier {target.category} alternative was found in the catalog.",
                "provider": "deterministic"}

    grounding = "\n".join(f"- {s.text}" for s in snippets)
    alt_lines = "\n".join(
        f"- {a.product.brand} {a.product.name} (health score {a.score}, +{a.score_delta})"
        for a in alternatives
    )
    prompt = (
        f"The shopper is looking at '{target.name}' ({target.category}).\n"
        f"Healthier catalog alternatives (already computed, do not change them):\n{alt_lines}\n\n"
        f"Relevant nutrition guidance:\n{grounding}\n\n"
        "In 2-3 sentences, explain why the alternatives are healthier. Use only the guidance "
        "above; do not invent nutrition numbers."
    )
    llm = get_llm()
    text = llm.complete(prompt, max_tokens=200)
    return {"text": text, "provider": llm.name}
