"""/products — catalog lookup by name or barcode (fills gaps OCR can't: MRP, canonical data)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services.catalog import get_catalog

router = APIRouter(prefix="/products", tags=["products"])


@router.get("")
def search_products(
    q: str | None = Query(default=None, description="fuzzy name/brand query"),
    barcode: str | None = Query(default=None),
    limit: int = Query(default=5, ge=1, le=25),
):
    catalog = get_catalog()
    if barcode:
        product = catalog.by_barcode(barcode)
        if not product:
            raise HTTPException(status_code=404, detail=f"No product for barcode {barcode}")
        return {"results": [product.as_dict()], "match": "barcode"}
    if q:
        return {"results": [p.as_dict() for p in catalog.search(q, limit=limit)], "match": "fuzzy"}
    return {"results": [p.as_dict() for p in catalog.all()[:limit]], "match": "all"}
