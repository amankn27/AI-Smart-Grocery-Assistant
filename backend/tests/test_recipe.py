"""Deterministic recipe ingredient-assembly + prompt tests, plus echo-provider path."""

from app.services.recipe import (
    RecipeConstraints,
    build_ingredient_list,
    build_prompt,
    generate_recipe,
)


def test_ingredients_deduplicated_and_normalized():
    ings = build_ingredient_list(
        cart_items=["Marie Gold Biscuit", "  marie gold biscuit ", "Milk"],
        pantry_items=["milk", "Eggs"],
    )
    assert ings == ["marie gold biscuit", "milk", "eggs"]  # order preserved, deduped


def test_prompt_includes_constraints_and_ingredients():
    p = build_prompt(["paneer", "peas"], RecipeConstraints(diet="veg", cuisine="Indian", servings=4, max_minutes=30))
    assert "veg" in p and "Indian" in p and "4 servings" in p
    assert "under 30 minutes" in p
    assert "paneer" in p and "peas" in p


class _EchoLike:
    name = "echo"

    def complete(self, prompt, system=None, max_tokens=512):
        return "RECIPE-TEXT"


def test_generate_recipe_uses_provider():
    r = generate_recipe(_EchoLike(), ["dal", "rice"], RecipeConstraints())
    assert r.ingredients == ["dal", "rice"]
    assert r.recipe_text == "RECIPE-TEXT"
    assert r.provider == "echo"


def test_empty_cart_is_handled():
    r = generate_recipe(_EchoLike(), [], RecipeConstraints())
    assert r.provider == "deterministic"
    assert "cart" in r.recipe_text.lower()
