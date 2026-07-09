"""Unit tests for deterministic dashboard aggregation. No DB/model deps."""

from app.services.analytics import summarize_scans


def test_empty_history():
    out = summarize_scans([])
    assert out["total_spend"] == "0.00"
    assert out["total_items"] == 0
    assert out["average_health_score"] is None
    assert out["category_mix"] == []


def test_spend_calories_and_category_mix():
    scans = [
        {"mrp": 40, "quantity": 2, "category": "soft_drink", "health_score": 20, "energy_kcal": 42},
        {"mrp": 30, "quantity": 1, "category": "biscuits", "health_score": 40, "energy_kcal": 450},
        {"mrp": 30, "quantity": 3, "category": "biscuits", "health_score": 40, "energy_kcal": 450},
    ]
    out = summarize_scans(scans)
    assert out["total_spend"] == "200.00"          # 80 + 30 + 90
    assert out["total_items"] == 6
    assert out["total_calories"] == 42 * 2 + 450 + 450 * 3   # 1884.0
    assert out["average_health_score"] == round((20 + 40 + 40) / 3, 1)
    # biscuits (4 items) ranks above soft_drink (2 items)
    assert out["category_mix"][0]["category"] == "biscuits"
    assert out["category_mix"][0]["items"] == 4


def test_missing_category_bucketed_as_uncategorized():
    out = summarize_scans([{"mrp": 10, "quantity": 1}])
    assert out["category_mix"][0]["category"] == "uncategorized"
