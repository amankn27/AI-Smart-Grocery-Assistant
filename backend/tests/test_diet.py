"""Deterministic diet-basket planning tests."""

from app.services.catalog import Product
from app.services.diet import build_basket


def _p(pid, kcal, protein, **extra):
    return Product(product_id=pid, name=pid, category="x",
                   nutrition={"energy_kcal": kcal, "protein_g": protein, **extra})


def test_stays_under_target_and_prefers_healthier():
    products = [
        _p("healthy", 200, 12, fiber_g=8, sugar_g=2),   # high health score
        _p("junk", 200, 3, sugar_g=40, sodium_mg=800),  # low health score
    ]
    plan = build_basket(products, target_kcal=250)
    # only one 200-kcal item fits under 250; the healthier one is chosen first
    assert plan.total_kcal == 200
    assert [i.product_id for i in plan.items] == ["healthy"]


def test_never_exceeds_target():
    products = [_p(f"i{i}", 150, 5) for i in range(10)]
    plan = build_basket(products, target_kcal=500)
    assert plan.total_kcal <= 500
    assert len(plan.items) == 3   # 3 * 150 = 450 <= 500, 4th would exceed


def test_items_without_calories_are_skipped():
    products = [_p("nocal", 0, 5), _p("ok", 100, 5)]
    plan = build_basket(products, target_kcal=300)
    assert [i.product_id for i in plan.items] == ["ok"]


def test_protein_flag_and_gap():
    products = [_p("a", 100, 20), _p("b", 100, 20)]
    plan = build_basket(products, target_kcal=250, min_protein_g=30)
    assert plan.total_protein_g == 40
    assert plan.meets_protein is True
    assert plan.as_dict()["kcal_gap"] == 50   # 250 - 200


def test_max_items_cap():
    products = [_p(f"i{i}", 50, 5) for i in range(20)]
    plan = build_basket(products, target_kcal=10000, max_items=4)
    assert len(plan.items) == 4
