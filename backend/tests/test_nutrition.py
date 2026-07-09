"""Unit tests for OCR-text → structured nutrition parsing. No model/network deps."""

from app.services.nutrition import parse_nutrition


def test_parses_clean_panel():
    text = """Nutrition Facts per 100g
    Energy 480 kcal
    Protein 7.2 g
    Total Fat 24 g
    Carbohydrate 60 g
    Sugar 22 g
    Sodium 450 mg
    """
    facts = parse_nutrition(text)
    assert facts.basis == "per_100g"
    assert facts.get("energy_kcal") == 480
    assert facts.get("protein_g") == 7.2
    assert facts.get("sugar_g") == 22
    assert facts.get("sodium_mg") == 450


def test_handles_ocr_misspellings_with_lower_confidence():
    text = "Enery 200 kcal\nProtien 5 g"
    facts = parse_nutrition(text)
    # values still extracted...
    assert facts.get("energy_kcal") == 200
    assert facts.get("protein_g") == 5
    # ...but confidence is below the exact-match tier
    assert facts.fields["energy_kcal"].confidence < 0.9


def test_salt_in_grams_converts_to_sodium_mg():
    facts = parse_nutrition("Salt 1 g")
    # sodium ≈ salt(g) * 400
    assert facts.get("sodium_mg") == 400.0


def test_kj_energy_converts_to_kcal():
    facts = parse_nutrition("Energy 2000 kj")
    assert facts.fields["energy_kcal"].value == round(2000 / 4.184, 1)


def test_comma_decimal_separator():
    facts = parse_nutrition("Protein 7,5 g")
    assert facts.get("protein_g") == 7.5


def test_missing_fields_are_absent_not_zero():
    facts = parse_nutrition("Energy 100 kcal")
    assert "protein_g" not in facts.fields
    assert facts.get("protein_g") is None
