"""/diet/plan — deterministic catalog basket toward a calorie/protein target + LLM narrative."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config.providers import get_llm
from app.services.catalog import get_catalog
from app.services.diet import build_basket, build_narrative_prompt

router = APIRouter(tags=["diet"])


class DietRequest(BaseModel):
    target_kcal: float = Field(gt=0, le=6000)
    min_protein_g: float = 0.0
    diet: str = "any"
    cuisine: str = "Indian"
    max_items: int = Field(default=8, ge=1, le=20)


@router.post("/diet/plan")
def plan(req: DietRequest) -> dict:
    catalog = get_catalog()
    plan = build_basket(
        catalog.all(), req.target_kcal, min_protein_g=req.min_protein_g, max_items=req.max_items
    )
    llm = get_llm()
    narrative = ""
    if plan.items:
        narrative = llm.complete(
            build_narrative_prompt(plan, req.diet, req.cuisine),
            system="You are a practical nutrition assistant.",
            max_tokens=300,
        )
    return {**plan.as_dict(), "narrative": narrative, "narrative_provider": llm.name if plan.items else "none"}
