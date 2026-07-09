"""Deterministic price/value analysis tests."""

from app.services.catalog import Product
from app.services.value import analyze_value, metrics_for


def _p(pid, cat, mrp, **nutrition):
    return Product(product_id=pid, name=pid, category=cat, mrp=mrp, nutrition=nutrition)


def test_health_per_rupee_and_unknown_price():
    m = metrics_for(_p("a", "biscuits", 20, protein_g=10, fiber_g=8, sugar_g=2))
    assert m.health_per_rupee == round(m.health_score / 20, 3)
    assert metrics_for(_p("b", "biscuits", 0, sugar_g=2)).health_per_rupee is None


def test_cheapest_and_best_value():
    target = _p("t", "biscuits", 30, sugar_g=30, sodium_mg=400)          # pricey + unhealthy
    cheap_junk = _p("c", "biscuits", 10, sugar_g=35, sodium_mg=500)      # cheapest
    premium_healthy = _p("h", "biscuits", 40, protein_g=10, fiber_g=8, sugar_g=3)
    res = analyze_value(target, [target, cheap_junk, premium_healthy])

    assert res["category_size"] == 3
    assert res["cheapest"]["product_id"] == "c"
    # best value = most health per rupee; healthy@40 likely beats junk@10 if score gap is large
    assert res["best_value"]["product_id"] in ("h", "c")
    assert res["target_is_cheapest"] is False


def test_only_same_category_considered():
    target = _p("t", "biscuits", 30, sugar_g=10)
    other_cat = _p("x", "soft_drink", 5, sugar_g=40)
    res = analyze_value(target, [target, other_cat])
    assert res["category_size"] == 1               # only the biscuit
    assert res["cheapest"]["product_id"] == "t"
    assert res["target_is_cheapest"] is True


def test_price_percentile():
    target = _p("t", "cereal", 50, protein_g=8)
    cheaper = _p("a", "cereal", 20, protein_g=8)
    dearer = _p("b", "cereal", 90, protein_g=8)
    res = analyze_value(target, [target, cheaper, dearer])
    # target (50) is at-or-below 2 of 3 prices (itself + 90) → 2/3 ≈ 0.67
    assert res["price_percentile"] == round(2 / 3, 2)
