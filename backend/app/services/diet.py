"""Deterministic diet / meal-basket planning over the catalog.

The basket selection is a pure, tested greedy knapsack-by-calories: pick the highest-health
catalog items toward a daily calorie target without exceeding it, reporting totals and the
gap. The LLM (in the router) only writes the *narrative* on how to use the basket; it never
changes the numbers.

Note: catalog nutrition is per-100g, so a selected item is treated as one ~100g portion —
a documented simplification adequate for a planning suggestion, not a clinical tool.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.services.catalog import Product
from app.services.health_scoring import score_nutrition


@dataclass
class BasketItem:
    product_id: str
    name: str
    energy_kcal: float
    protein_g: float
    health_score: int

    def as_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "energy_kcal": self.energy_kcal,
            "protein_g": self.protein_g,
            "health_score": self.health_score,
        }


@dataclass
class DietPlan:
    target_kcal: float
    items: list[BasketItem] = field(default_factory=list)
    total_kcal: float = 0.0
    total_protein_g: float = 0.0
    meets_protein: bool = False

    def as_dict(self) -> dict:
        return {
            "target_kcal": self.target_kcal,
            "total_kcal": round(self.total_kcal, 1),
            "total_protein_g": round(self.total_protein_g, 1),
            "kcal_gap": round(self.target_kcal - self.total_kcal, 1),
            "meets_protein": self.meets_protein,
            "items": [i.as_dict() for i in self.items],
        }


def build_basket(
    products: list[Product],
    target_kcal: float,
    *,
    min_protein_g: float = 0.0,
    max_items: int = 8,
) -> DietPlan:
    """Greedily pick highest-health items whose calories fit under ``target_kcal``.

    Deterministic: candidates are sorted by (health_score desc, protein desc, kcal asc) so the
    result is stable. An item is added only if it keeps total calories at/under the target.
    """
    candidates = []
    for p in products:
        kcal = float(p.nutrition.get("energy_kcal", 0) or 0)
        if kcal <= 0:
            continue  # can't budget calories for it
        protein = float(p.nutrition.get("protein_g", 0) or 0)
        score = score_nutrition(**p.nutrition).score
        candidates.append((p, kcal, protein, score))

    candidates.sort(key=lambda c: (-c[3], -c[2], c[1]))

    plan = DietPlan(target_kcal=target_kcal)
    for p, kcal, protein, score in candidates:
        if len(plan.items) >= max_items:
            break
        if plan.total_kcal + kcal > target_kcal:
            continue
        plan.items.append(BasketItem(p.product_id, p.name, round(kcal, 1), round(protein, 1), score))
        plan.total_kcal += kcal
        plan.total_protein_g += protein

    plan.meets_protein = plan.total_protein_g >= min_protein_g
    return plan


def build_narrative_prompt(plan: DietPlan, diet: str, cuisine: str) -> str:
    items = ", ".join(i.name for i in plan.items) or "(no suitable items)"
    return (
        f"Suggest how to distribute these grocery items across a {diet} {cuisine} day of eating "
        f"(~{int(plan.total_kcal)} kcal, {int(plan.total_protein_g)} g protein): {items}. "
        "Give 3 short meal ideas. Do not invent calorie numbers beyond the total given."
    )
