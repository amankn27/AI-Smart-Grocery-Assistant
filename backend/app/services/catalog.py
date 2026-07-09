"""Product catalog: the source of MRP + barcode→product mapping OCR can't supply (brief §5).

Loads a seed CSV (an Open Food Facts India subset built by ``data/seed/build_seed.py``)
into memory and offers name/barcode lookup with light fuzzy matching. Pure-Python + stdlib
``csv`` so it runs anywhere; swapping to a DB-backed repository later is a drop-in change
behind the same functions.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
from typing import Optional

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


@dataclass
class Product:
    product_id: str
    name: str
    brand: str = ""
    barcode: str = ""
    category: str = ""
    mrp: float = 0.0
    weight_g: Optional[float] = None
    nutrition: dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "brand": self.brand,
            "barcode": self.barcode,
            "category": self.category,
            "mrp": self.mrp,
            "weight_g": self.weight_g,
            "nutrition": self.nutrition,
        }


_NUTRITION_COLS = (
    "energy_kcal",
    "protein_g",
    "fat_g",
    "saturated_fat_g",
    "carbohydrate_g",
    "sugar_g",
    "fiber_g",
    "sodium_mg",
)


def _to_float(value: str | None) -> Optional[float]:
    if value is None or value.strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


class Catalog:
    def __init__(self, products: list[Product]) -> None:
        self._products = products
        self._by_barcode = {p.barcode: p for p in products if p.barcode}
        self._by_id = {p.product_id: p for p in products}

    @classmethod
    def from_csv(cls, path: str | Path) -> "Catalog":
        path = Path(path)
        products: list[Product] = []
        if not path.exists():
            logger.warning("Seed catalog %s not found; catalog will be empty", path)
            return cls(products)
        with path.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                nutrition = {c: v for c in _NUTRITION_COLS if (v := _to_float(row.get(c))) is not None}
                products.append(
                    Product(
                        product_id=row.get("product_id") or row.get("barcode") or row.get("name", ""),
                        name=row.get("name", "").strip(),
                        brand=row.get("brand", "").strip(),
                        barcode=row.get("barcode", "").strip(),
                        category=row.get("category", "").strip(),
                        mrp=_to_float(row.get("mrp")) or 0.0,
                        weight_g=_to_float(row.get("weight_g")),
                        nutrition=nutrition,
                    )
                )
        logger.info("Loaded %d products from %s", len(products), path)
        return cls(products)

    def by_barcode(self, barcode: str) -> Optional[Product]:
        return self._by_barcode.get(barcode.strip())

    def by_id(self, product_id: str) -> Optional[Product]:
        return self._by_id.get(product_id)

    def search(self, query: str, limit: int = 5) -> list[Product]:
        """Rank products by fuzzy similarity of query to "brand name"."""
        q = query.strip().lower()
        if not q:
            return []
        scored = []
        for p in self._products:
            hay = f"{p.brand} {p.name}".lower()
            ratio = SequenceMatcher(None, q, hay).ratio()
            if q in hay:
                ratio = max(ratio, 0.75)
            scored.append((ratio, p))
        scored.sort(key=lambda t: t[0], reverse=True)
        return [p for ratio, p in scored[:limit] if ratio > 0.3]

    def all(self) -> list[Product]:
        return list(self._products)


def _resolve_seed_path(configured: str) -> Path:
    """Resolve the seed CSV whether the app is run from the repo root or from backend/.

    Tries the configured path as-is (absolute or relative to cwd), then relative to the
    repo root (…/backend/app/services/catalog.py → parents[3]).
    """
    p = Path(configured)
    if p.is_absolute() and p.exists():
        return p
    candidates = [p, Path(__file__).resolve().parents[3] / configured]
    for cand in candidates:
        if cand.exists():
            return cand
    return p  # let from_csv log the "not found" and return an empty catalog


@lru_cache
def get_catalog() -> Catalog:
    return Catalog.from_csv(_resolve_seed_path(get_settings().seed_products_csv))
