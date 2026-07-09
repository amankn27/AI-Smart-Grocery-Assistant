"""Tests for deterministic OCR↔catalog gap-filling merge."""

from app.services.catalog import Product
from app.services.merge import merge_product_data
from app.services.nutrition import Field, NutritionFacts


def _catalog_product():
    return Product(
        product_id="1", name="Marie Gold", brand="Britannia", barcode="890",
        category="biscuits", mrp=30.0,
        nutrition={"energy_kcal": 450, "protein_g": 7, "sugar_g": 20, "sodium_mg": 350},
    )


def test_confident_ocr_wins_over_catalog():
    ocr = NutritionFacts(fields={"sugar_g": Field(value=18.0, unit="g", confidence=0.9)})
    merged = merge_product_data(ocr=ocr, catalog=_catalog_product())
    assert merged.nutrition["sugar_g"] == 18.0     # OCR (18) beat catalog (20)
    assert merged.sources["sugar_g"] == "ocr"


def test_catalog_fills_missing_and_low_confidence_fields():
    ocr = NutritionFacts(fields={"sugar_g": Field(value=99.0, unit="g", confidence=0.2)})  # low conf
    merged = merge_product_data(ocr=ocr, catalog=_catalog_product())
    # low-confidence OCR ignored -> catalog fills it
    assert merged.nutrition["sugar_g"] == 20
    assert merged.sources["sugar_g"] == "catalog"
    # protein only in catalog
    assert merged.nutrition["protein_g"] == 7
    assert merged.sources["protein_g"] == "catalog"


def test_identity_comes_from_catalog():
    merged = merge_product_data(catalog=_catalog_product(), ocr_name="blurry text")
    assert merged.name == "Marie Gold"
    assert merged.brand == "Britannia"
    assert merged.mrp == 30.0


def test_unknown_fields_reported_when_neither_source_has_them():
    merged = merge_product_data(catalog=_catalog_product())
    assert "fat_g" in merged.unknown_fields
    assert "energy_kcal" not in merged.unknown_fields


def test_ocr_only_no_catalog():
    ocr = NutritionFacts(fields={"protein_g": Field(value=8.0, unit="g", confidence=0.9)})
    merged = merge_product_data(ocr=ocr, ocr_name="Unknown Snack")
    assert merged.name == "Unknown Snack"
    assert merged.nutrition["protein_g"] == 8.0
    assert merged.mrp == 0.0
