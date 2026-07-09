"""Recipe generation from cart/pantry contents.

Deterministic part (tested): assemble a de-duplicated ingredient list from cart items (plus
optional pantry/extra items) and build the LLM prompt with the user's constraints. The LLM
turns that into a recipe; when no LLM is configured the echo provider still returns a usable
deterministic suggestion, so `/recipe` never dead-ends.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RecipeConstraints:
    diet: str = "any"          # any | veg | non-veg | vegan
    cuisine: str = "Indian"
    servings: int = 2
    max_minutes: Optional[int] = None


def build_ingredient_list(
    cart_items: list[str],
    pantry_items: Optional[list[str]] = None,
    extra: Optional[list[str]] = None,
) -> list[str]:
    """De-duplicate + normalize ingredient names, preserving first-seen order."""
    seen: dict[str, None] = {}
    for name in [*cart_items, *(pantry_items or []), *(extra or [])]:
        key = " ".join(name.strip().lower().split())
        if key and key not in seen:
            seen[key] = None
    return list(seen.keys())


def build_prompt(ingredients: list[str], c: RecipeConstraints) -> str:
    limit = f" in under {c.max_minutes} minutes" if c.max_minutes else ""
    return (
        f"Create a simple {c.diet} {c.cuisine} recipe for {c.servings} servings{limit} "
        f"using mainly these ingredients: {', '.join(ingredients)}.\n"
        "Assume basic staples (salt, oil, spices, water) are available. "
        "Return a title, an ingredient list with rough quantities, and numbered steps. "
        "Do not require ingredients that are not commonly available in an Indian kitchen."
    )


@dataclass
class RecipeResult:
    ingredients: list[str] = field(default_factory=list)
    recipe_text: str = ""
    provider: str = ""

    def as_dict(self) -> dict:
        return {"ingredients": self.ingredients, "recipe_text": self.recipe_text, "provider": self.provider}


def generate_recipe(llm, ingredients: list[str], constraints: RecipeConstraints) -> RecipeResult:
    """Call the LLM to produce a recipe; providers degrade gracefully (echo) on their own."""
    if not ingredients:
        return RecipeResult(ingredients=[], recipe_text="Add items to your cart first.", provider="deterministic")
    prompt = build_prompt(ingredients, constraints)
    text = llm.complete(prompt, system="You are a helpful home-cooking assistant.", max_tokens=400)
    return RecipeResult(ingredients=ingredients, recipe_text=text, provider=llm.name)
