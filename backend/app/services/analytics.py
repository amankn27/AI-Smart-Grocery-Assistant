"""Deterministic dashboard aggregations over scan history.

Pure function: list of scan dicts → spend / calories / category mix / average health score.
No DB or model access here (the router fetches rows and hands them in), so it's unit-tested
directly in ``tests/test_analytics.py``.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal


def summarize_scans(scans: list[dict]) -> dict:
    """Aggregate scan rows into dashboard metrics.

    Each scan dict is expected to have: mrp, quantity, category, health_score, energy_kcal.
    Spend uses Decimal to stay exact; the rest are simple sums/means.
    """
    total_spend = Decimal("0.00")
    total_calories = 0.0
    total_items = 0
    category_count: dict[str, int] = defaultdict(int)
    category_spend: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    health_scores: list[int] = []

    for s in scans:
        qty = int(s.get("quantity", 1) or 1)
        mrp = Decimal(str(s.get("mrp", 0) or 0))
        line = mrp * qty
        cat = s.get("category") or "uncategorized"

        total_spend += line
        total_items += qty
        total_calories += float(s.get("energy_kcal", 0) or 0) * qty
        category_count[cat] += qty
        category_spend[cat] += line
        if s.get("health_score") is not None:
            health_scores.append(int(s["health_score"]))

    avg_health = round(sum(health_scores) / len(health_scores), 1) if health_scores else None

    category_mix = sorted(
        (
            {"category": c, "items": category_count[c], "spend": f"{category_spend[c]:.2f}"}
            for c in category_count
        ),
        key=lambda d: d["items"],
        reverse=True,
    )

    return {
        "total_spend": f"{total_spend:.2f}",
        "total_items": total_items,
        "total_calories": round(total_calories, 1),
        "average_health_score": avg_health,
        "scan_count": len(scans),
        "category_mix": category_mix,
    }
