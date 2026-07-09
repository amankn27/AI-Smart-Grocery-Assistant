"""Deterministically merge OCR-extracted nutrition with catalog data (gap-filling).

Rule (brief §1 Phase 1 "fills gaps OCR missed"): a **confident** OCR value wins, because it
came from the actual package in front of the user; otherwise the catalog value fills the
field. Provenance is tracked per field so the UI can show where each number came from and
still flag anything unknown. Pure functions — tested in ``tests/test_merge.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from app.services.catalog import Product
from app.services.nutrition import NutritionFacts

_NUTRITION_FIELDS = (
    "energy_kcal", "protein_g", "fat_g", "saturated_fat_g",
    "carbohydrate_g", "sugar_g", "fiber_g", "sodium_mg",
)


@dataclass
class MergedProduct:
    name: str
    brand: str = ""
    barcode: str = ""
    category: str = ""
    mrp: float = 0.0
    nutrition: dict[str, float] = field(default_factory=dict)
    sources: dict[str, str] = field(default_factory=dict)  # field -> "ocr" | "catalog"
    unknown_fields: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "brand": self.brand,
            "barcode": self.barcode,
            "category": self.category,
            "mrp": self.mrp,
            "nutrition": self.nutrition,
            "sources": self.sources,
            "unknown_fields": self.unknown_fields,
        }


def merge_product_data(
    *,
    ocr: Optional[NutritionFacts] = None,
    catalog: Optional[Product] = None,
    ocr_name: str = "",
) -> MergedProduct:
    """Combine an OCR nutrition read with a catalog product.

    - Identity (name/brand/barcode/category/MRP) comes from the catalog when present,
      since OCR can't supply price or a canonical barcode mapping (brief §5).
    - Each nutrition field: confident OCR value wins; else catalog; else unknown.
    """
    merged = MergedProduct(
        name=(catalog.name if catalog and catalog.name else ocr_name),
        brand=catalog.brand if catalog else "",
        barcode=catalog.barcode if catalog else "",
        category=catalog.category if catalog else "",
        mrp=catalog.mrp if catalog else 0.0,
    )

    ocr_fields = ocr.fields if ocr else {}
    catalog_nutrition = catalog.nutrition if catalog else {}

    for name in _NUTRITION_FIELDS:
        ocr_field = ocr_fields.get(name)
        if ocr_field is not None and ocr_field.ok:
            merged.nutrition[name] = ocr_field.value  # type: ignore[assignment]
            merged.sources[name] = "ocr"
        elif name in catalog_nutrition:
            merged.nutrition[name] = catalog_nutrition[name]
            merged.sources[name] = "catalog"
        else:
            merged.unknown_fields.append(name)

    return merged
