"""Build the Phase 0 product catalog from an Open Food Facts (India) subset.

Queries the OFF search API for a handful of common Indian grocery categories, maps the
fields we care about to our schema, and writes ``products.csv`` next to this script.

Usage:
    python data/seed/build_seed.py --per-category 6

Network is required to (re)build. A pre-built ``products.csv`` is committed so the app runs
offline; this script exists so the seed set is reproducible and extensible (brief §5).
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

OFF_SEARCH = "https://world.openfoodfacts.org/cgi/search.pl"

# Our internal category -> an OFF search term that returns representative products.
CATEGORY_QUERIES = {
    "biscuits": "biscuits",
    "chips_namkeen": "namkeen",
    "chocolate": "chocolate",
    "instant_noodles": "instant noodles",
    "soft_drink": "soft drink",
    "juice": "fruit juice",
    "milk_dairy": "milk",
    "bread": "bread",
    "cereal": "breakfast cereal",
    "cooking_oil": "cooking oil",
    "tea_coffee": "tea",
    "snack_bar": "energy bar",
}

FIELDS = [
    "product_id", "name", "brand", "barcode", "category", "mrp", "weight_g",
    "energy_kcal", "protein_g", "fat_g", "saturated_fat_g",
    "carbohydrate_g", "sugar_g", "fiber_g", "sodium_mg",
]

# OFF has no reliable Indian MRP; seed a nominal price so billing is demoable. Replace with
# a real price feed when available (flagged in docs — OFF cannot supply MRP).
NOMINAL_MRP = {
    "biscuits": 30, "chips_namkeen": 20, "chocolate": 80, "instant_noodles": 14,
    "soft_drink": 40, "juice": 110, "milk_dairy": 60, "bread": 45,
    "cereal": 210, "cooking_oil": 160, "tea_coffee": 155, "snack_bar": 40,
}


# Plausible per-100g upper bounds; OFF has data-entry errors (e.g. sodium in mg vs g),
# so clamp implausible values to blank rather than poison the catalog/health scoring.
_MAX_PER_100G = {
    "energy_kcal": 900, "protein_g": 100, "fat_g": 100, "saturated_fat_g": 100,
    "carbohydrate_g": 100, "sugar_g": 100, "fiber_g": 100, "sodium_mg": 5000,
}


def _nutriment(nutr: dict, *keys, scale=1.0, bound: str | None = None):
    for k in keys:
        v = nutr.get(k)
        if v is not None:
            try:
                val = round(float(v) * scale, 2)
            except (TypeError, ValueError):
                continue
            if val < 0:
                return ""
            if bound and val > _MAX_PER_100G[bound]:
                return ""  # implausible -> treat as unknown
            return val
    return ""


def _get_with_retry(params: dict, retries: int = 4):
    """OFF's public API returns transient 503s under load — back off and retry."""
    delay = 2.0
    last_exc = None
    for attempt in range(retries):
        try:
            resp = requests.get(OFF_SEARCH, params=params, timeout=30,
                                headers={"User-Agent": "smart-grocery-ai/0.1 (seed builder)"})
            if resp.status_code == 503:
                raise requests.HTTPError("503 Service Unavailable")
            resp.raise_for_status()
            return resp
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(delay)
            delay *= 2
    raise last_exc  # type: ignore[misc]


def fetch_category(term: str, category: str, per_category: int) -> list[dict]:
    params = {
        "search_terms": term,
        "search_simple": 1,
        "action": "process",
        "json": 1,
        "page_size": per_category * 3,
        "countries_tags_en": "india",
        "fields": "code,product_name,brands,quantity,nutriments",
    }
    resp = _get_with_retry(params)
    rows = []
    for p in resp.json().get("products", []):
        name = (p.get("product_name") or "").strip()
        if not name:
            continue
        n = p.get("nutriments", {})
        rows.append({
            "product_id": p.get("code") or name,
            "name": name,
            "brand": (p.get("brands") or "").split(",")[0].strip(),
            "barcode": p.get("code", ""),
            "category": category,
            "mrp": NOMINAL_MRP.get(category, 50),
            "weight_g": "",
            "energy_kcal": _nutriment(n, "energy-kcal_100g", bound="energy_kcal"),
            "protein_g": _nutriment(n, "proteins_100g", bound="protein_g"),
            "fat_g": _nutriment(n, "fat_100g", bound="fat_g"),
            "saturated_fat_g": _nutriment(n, "saturated-fat_100g", bound="saturated_fat_g"),
            "carbohydrate_g": _nutriment(n, "carbohydrates_100g", bound="carbohydrate_g"),
            "sugar_g": _nutriment(n, "sugars_100g", bound="sugar_g"),
            "fiber_g": _nutriment(n, "fiber_100g", bound="fiber_g"),
            "sodium_mg": _nutriment(n, "sodium_100g", scale=1000.0, bound="sodium_mg"),  # g -> mg
        })
        if len(rows) >= per_category:
            break
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-category", type=int, default=6)
    ap.add_argument("--out", default=str(Path(__file__).parent / "products.csv"))
    args = ap.parse_args()

    if requests is None:
        print("`requests` not installed. Run: pip install requests", file=sys.stderr)
        return 1

    out = Path(args.out)

    # Merge with any existing catalog so a partial/flaky fetch never SHRINKS the seed set.
    existing: dict[str, dict] = {}
    if out.exists():
        with out.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                existing[row["product_id"]] = row

    merged: dict[str, dict] = dict(existing)
    fetched = 0
    for category, term in CATEGORY_QUERIES.items():
        try:
            rows = fetch_category(term, category, args.per_category)
            print(f"{category:16s} -> {len(rows)} products")
            for r in rows:
                merged[r["product_id"]] = r
            fetched += len(rows)
        except Exception as exc:  # noqa: BLE001
            print(f"{category:16s} -> FAILED ({exc})", file=sys.stderr)
        time.sleep(1.5)  # be polite to the public API

    with out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(merged.values())
    print(f"Fetched {fetched} this run; catalog now has {len(merged)} products -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
