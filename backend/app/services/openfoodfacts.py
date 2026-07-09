"""Open Food Facts barcode fallback.

When a scanned barcode isn't in the local seed catalog, look it up in Open Food Facts
(https://world.openfoodfacts.org), a free database of ~3M real products. This turns barcode
scanning into a "scan any real product -> get its details" feature without a heavy model.

Design notes:
- Lightweight (a single HTTP GET), so it works on the free tier too, unlike YOLO/OCR.
- Degrades gracefully: disabled by config, a network error, a not-found code, or a malformed
  payload all return ``None`` so the router falls back to manual entry rather than erroring.
- OFF has no reliable Indian MRP (same caveat as the seed data), so ``mrp`` stays 0.0.
"""

from __future__ import annotations

import logging
from typing import Optional

from app.config.settings import get_settings
from app.services.catalog import Product

logger = logging.getLogger(__name__)

# Only request the fields we use — smaller, faster responses (OFF products are huge).
_OFF_FIELDS = "product_name,brands,quantity,categories_tags,nutriments"
_USER_AGENT = "SmartGroceryAssistant/1.0 (grocery health scanner)"


def _fetch_off_json(barcode: str, base_url: str, timeout: float) -> Optional[dict]:
    """Do the HTTP GET. Isolated so tests can monkeypatch it (no network in CI)."""
    import httpx

    url = f"{base_url.rstrip('/')}/api/v2/product/{barcode}.json"
    with httpx.Client(timeout=timeout, headers={"User-Agent": _USER_AGENT}) as client:
        resp = client.get(url, params={"fields": _OFF_FIELDS})
    if resp.status_code != 200:
        logger.info("OFF lookup for %s returned HTTP %s", barcode, resp.status_code)
        return None
    return resp.json()


def _num(nutriments: dict, *keys: str) -> Optional[float]:
    """First numeric value among the given OFF nutriment keys, else None."""
    for k in keys:
        v = nutriments.get(k)
        if v is None or v == "":
            continue
        try:
            return float(v)
        except (TypeError, ValueError):
            continue
    return None


def _to_product(barcode: str, off_product: dict) -> Optional[Product]:
    """Map an OFF product payload to our :class:`Product` (per-100g nutrition)."""
    name = (off_product.get("product_name") or "").strip()
    if not name:
        return None  # nameless OFF entries aren't useful — treat as a miss

    brand = (off_product.get("brands") or "").split(",")[0].strip()
    n = off_product.get("nutriments") or {}

    nutrition: dict[str, float] = {}
    mapping = {
        "energy_kcal": ("energy-kcal_100g",),
        "protein_g": ("proteins_100g",),
        "fat_g": ("fat_100g",),
        "saturated_fat_g": ("saturated-fat_100g",),
        "carbohydrate_g": ("carbohydrates_100g",),
        "sugar_g": ("sugars_100g",),
        "fiber_g": ("fiber_100g", "fibers_100g"),
    }
    for field_name, keys in mapping.items():
        val = _num(n, *keys)
        if val is not None:
            nutrition[field_name] = val

    # OFF stores sodium/salt in grams per 100g; we want sodium in mg.
    sodium_g = _num(n, "sodium_100g")
    if sodium_g is None:
        salt_g = _num(n, "salt_100g")
        if salt_g is not None:
            sodium_g = salt_g / 2.5  # standard salt->sodium conversion
    if sodium_g is not None:
        nutrition["sodium_mg"] = round(sodium_g * 1000, 1)

    return Product(
        product_id=barcode,
        name=name,
        brand=brand,
        barcode=barcode,
        category="",  # OFF categories are noisy; leave unset rather than guess
        mrp=0.0,       # OFF has no reliable MRP (documented limitation)
        weight_g=None,
        nutrition=nutrition,
    )


def lookup_off(barcode: str) -> Optional[Product]:
    """Return a Product for ``barcode`` from Open Food Facts, or None if unavailable.

    Never raises: disabled config, network errors, not-found, and bad payloads all -> None.
    """
    barcode = (barcode or "").strip()
    if not barcode:
        return None

    s = get_settings()
    if not getattr(s, "off_enabled", True):
        return None

    try:
        data = _fetch_off_json(barcode, s.off_base_url, s.off_timeout)
    except Exception as exc:  # noqa: BLE001 — external call must never break the request
        logger.info("OFF lookup for %s failed: %s", barcode, exc)
        return None

    if not data or data.get("status") != 1 or not data.get("product"):
        return None
    return _to_product(barcode, data["product"])
