"""Unit tests for deterministic health scoring. No model/network deps."""

from app.services.health_scoring import score_nutrition


def test_healthy_food_scores_high_and_grades_well():
    r = score_nutrition(energy_kcal=120, protein_g=12, fat_g=2, saturated_fat_g=0.5,
                        sugar_g=2, fiber_g=8, sodium_mg=50)
    assert r.score >= 80
    assert r.grade == "A"
    assert any("protein" in p.lower() for p in r.positives)
    assert any("fibre" in p.lower() for p in r.positives)


def test_junk_food_scores_low_with_red_warnings():
    r = score_nutrition(energy_kcal=520, protein_g=4, fat_g=30, saturated_fat_g=14,
                        sugar_g=45, fiber_g=1, sodium_mg=800)
    assert r.score <= 35
    assert r.grade in ("D", "E")
    severities = {w.severity for w in r.warnings}
    assert "red" in severities
    fields = {w.field for w in r.warnings}
    assert {"sugar_g", "sodium_mg", "saturated_fat_g"} <= fields


def test_missing_fields_neither_reward_nor_penalize():
    # Only energy given; should stay near max with just the calorie-density check.
    r = score_nutrition(energy_kcal=100)
    assert r.score == 100


def test_score_is_clamped_0_100():
    r = score_nutrition(protein_g=100, fiber_g=100)  # big bonuses
    assert r.score <= 100
    r2 = score_nutrition(sugar_g=90, sodium_mg=2000, saturated_fat_g=40, fat_g=40, energy_kcal=900)
    assert r2.score >= 0
