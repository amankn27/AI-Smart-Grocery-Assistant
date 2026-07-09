"""/value — price/value comparison for a catalog product."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.catalog import get_catalog
from app.services.value import analyze_value

router = APIRouter(tags=["value"])


class ValueRequest(BaseModel):
    product_id: str | None = None
    barcode: str | None = None


@router.post("/value")
def value(req: ValueRequest) -> dict:
    catalog = get_catalog()
    target = catalog.by_id(req.product_id) if req.product_id else None
    if target is None and req.barcode:
        target = catalog.by_barcode(req.barcode)
    if target is None:
        raise HTTPException(status_code=404, detail="Product not found in catalog")
    return analyze_value(target, catalog.all())
