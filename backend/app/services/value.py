"""Deterministic price/value analysis over the catalog.

Pure functions (tested in ``tests/test_value.py``): compute a product's health-per-rupee, its
price position within its category, the cheapest same-category option, and the best-value pick
(most health per rupee). No model or network calls — value judgements stay explainable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.services.catalog import Product
from app.services.health_scoring import score_nutrition


@dataclass
class ValueMetrics:
    product_id: str
    name: str
    brand: str
    mrp: float
    health_score: int
    health_per_rupee: Optional[float]  # None when price unknown (<=0)

    def as_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "brand": self.brand,
            "mrp": self.mrp,
            "health_score": self.health_score,
            "health_per_rupee": self.health_per_rupee,
        }


def metrics_for(product: Product) -> ValueMetrics:
    score = score_nutrition(**product.nutrition).score
    hpr = round(score / product.mrp, 3) if product.mrp and product.mrp > 0 else None
    return ValueMetrics(
        product_id=product.product_id, name=product.name, brand=product.brand,
        mrp=product.mrp, health_score=score, health_per_rupee=hpr,
    )


def _price_percentile(mrp: float, prices: list[float]) -> Optional[float]:
    """Fraction of same-category items priced at or below ``mrp`` (0..1). None if no prices."""
    priced = [p for p in prices if p > 0]
    if not priced or mrp <= 0:
        return None
    at_or_below = sum(1 for p in priced if p <= mrp)
    return round(at_or_below / len(priced), 2)


def analyze_value(target: Product, candidates: list[Product]) -> dict:
    """Value analysis for ``target`` against same-category catalog products.

    Returns the target's metrics, its price percentile within the category, the cheapest
    same-category option, and the best-value option (highest health-per-rupee).
    """
    same_cat = [c for c in candidates if c.category == target.category]
    # Ensure the target is represented once.
    others = [c for c in same_cat if c.product_id != target.product_id]

    target_m = metrics_for(target)
    pool = [target_m] + [metrics_for(c) for c in others]

    priced = [m for m in pool if m.mrp and m.mrp > 0]
    cheapest = min(priced, key=lambda m: m.mrp) if priced else None

    valued = [m for m in pool if m.health_per_rupee is not None]
    best_value = max(valued, key=lambda m: m.health_per_rupee) if valued else None  # type: ignore[arg-type]

    return {
        "target": target_m.as_dict(),
        "category": target.category,
        "category_size": len(pool),
        "price_percentile": _price_percentile(target.mrp, [m.mrp for m in pool]),
        "cheapest": cheapest.as_dict() if cheapest else None,
        "best_value": best_value.as_dict() if best_value else None,
        "target_is_cheapest": bool(cheapest and cheapest.product_id == target.product_id),
        "target_is_best_value": bool(best_value and best_value.product_id == target.product_id),
    }
