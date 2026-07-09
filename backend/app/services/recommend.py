"""Deterministic healthier-alternative ranking.

The *alternatives themselves* are chosen by a pure, tested function — same category, a
strictly better health score than the scanned item, ranked by score improvement (ties broken
by lower sugar then lower sodium). The LLM only phrases the explanation later; it never
invents products or numbers (brief §3). Tested in ``tests/test_recommend.py``.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.catalog import Product
from app.services.health_scoring import score_nutrition


def _score_of(product: Product) -> int:
    return score_nutrition(**product.nutrition).score


@dataclass
class Alternative:
    product: Product
    score: int
    score_delta: int

    def as_dict(self) -> dict:
        d = self.product.as_dict()
        d["health_score"] = self.score
        d["score_delta"] = self.score_delta
        return d


def rank_alternatives(target: Product, candidates: list[Product], limit: int = 3) -> list[Alternative]:
    """Return healthier same-category alternatives to ``target``, best improvement first."""
    target_score = _score_of(target)
    out: list[Alternative] = []
    for c in candidates:
        if c.product_id == target.product_id:
            continue
        if c.category != target.category:
            continue
        c_score = _score_of(c)
        if c_score <= target_score:
            continue
        out.append(Alternative(product=c, score=c_score, score_delta=c_score - target_score))

    out.sort(
        key=lambda a: (
            -a.score_delta,
            a.product.nutrition.get("sugar_g", 0.0),
            a.product.nutrition.get("sodium_mg", 0.0),
        )
    )
    return out[:limit]
