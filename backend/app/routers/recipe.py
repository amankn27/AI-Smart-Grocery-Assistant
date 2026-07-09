"""/recipe — generate a recipe from the current cart (or explicit ingredients)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.config.providers import get_llm
from app.services.cart import cart_store
from app.services.recipe import RecipeConstraints, build_ingredient_list, generate_recipe

router = APIRouter(tags=["recipe"])


class RecipeRequest(BaseModel):
    session_id: str = "demo"
    ingredients: list[str] | None = None   # override cart if provided
    diet: str = "any"
    cuisine: str = "Indian"
    servings: int = 2
    max_minutes: int | None = None


@router.post("/recipe")
def recipe(req: RecipeRequest) -> dict:
    cart_names = req.ingredients or [i.name for i in cart_store.items(req.session_id)]
    ingredients = build_ingredient_list(cart_names)
    constraints = RecipeConstraints(
        diet=req.diet, cuisine=req.cuisine, servings=req.servings, max_minutes=req.max_minutes
    )
    result = generate_recipe(get_llm(), ingredients, constraints)
    return result.as_dict()
