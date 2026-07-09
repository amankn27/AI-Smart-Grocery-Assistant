"""Tests for deterministic healthier-alternative ranking."""

from app.services.catalog import Product
from app.services.recommend import rank_alternatives


def _p(pid, cat, **nutrition):
    return Product(product_id=pid, name=pid, category=cat, nutrition=nutrition)


def test_only_same_category_and_strictly_healthier():
    target = _p("cola", "soft_drink", sugar_g=40, sodium_mg=20)
    candidates = [
        _p("water", "soft_drink", sugar_g=0, sodium_mg=0),        # healthier, same cat
        _p("chips", "chips_namkeen", sugar_g=1, sodium_mg=800),   # different category
        _p("cola2", "soft_drink", sugar_g=45, sodium_mg=20),      # worse
    ]
    alts = rank_alternatives(target, candidates)
    ids = [a.product.product_id for a in alts]
    assert ids == ["water"]
    assert alts[0].score_delta > 0


def test_ranked_by_score_improvement():
    target = _p("junk", "biscuits", sugar_g=40, saturated_fat_g=15, sodium_mg=600, fiber_g=0)
    a = _p("ok", "biscuits", sugar_g=20, saturated_fat_g=5, sodium_mg=300, fiber_g=3)
    b = _p("great", "biscuits", sugar_g=8, saturated_fat_g=1, sodium_mg=120, fiber_g=8, protein_g=9)
    alts = rank_alternatives(target, [a, b])
    assert [x.product.product_id for x in alts] == ["great", "ok"]  # bigger improvement first


def test_target_excluded_and_empty_when_none_better():
    target = _p("best", "cereal", sugar_g=2, fiber_g=10, protein_g=12)
    worse = _p("worse", "cereal", sugar_g=30, fiber_g=1)
    alts = rank_alternatives(target, [target, worse])
    assert alts == []
