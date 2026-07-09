"""/barcode — decode an EAN/UPC/QR from an image and fill product data from the catalog.

Flow: decode → catalog lookup by barcode → merge with any OCR nutrition the client passes.
Degrades to "not found / manual entry" rather than erroring when no code is readable.
"""

from __future__ import annotations

from fastapi import APIRouter, File, Form, UploadFile

from app.config.providers import get_barcode_decoder
from app.services.catalog import get_catalog
from app.services.merge import merge_product_data
from app.services.openfoodfacts import lookup_off

router = APIRouter(tags=["barcode"])


def _resolve_barcode(value: str):
    """Local seed catalog first, then Open Food Facts. Returns (product, source|None)."""
    hit = get_catalog().by_barcode(value)
    if hit:
        return hit, "catalog"
    off = lookup_off(value)
    if off:
        return off, "openfoodfacts"
    return None, None


@router.post("/barcode")
async def scan_barcode(image: UploadFile = File(...)) -> dict:
    data = await image.read()
    decoder = get_barcode_decoder()
    codes = decoder.decode(data)
    if not codes:
        return {"decoder": decoder.name, "barcodes": [], "product": None, "fallback": "manual_entry"}

    product = None
    source = None
    matched_code = None
    for code in codes:
        product, source = _resolve_barcode(code.value)
        if product:
            matched_code = code
            break

    return {
        "decoder": decoder.name,
        "barcodes": [{"value": c.value, "type": c.type} for c in codes],
        "matched_barcode": matched_code.value if matched_code else None,
        "product": product.as_dict() if product else None,
        "source": source,
        "fallback": None if product else "not_in_catalog",
    }


@router.post("/barcode/lookup")
def lookup_barcode(barcode: str = Form(...)) -> dict:
    """Manual barcode entry path (when the camera can't read it)."""
    product, source = _resolve_barcode(barcode)
    if not product:
        merged = merge_product_data()  # empty shell so the UI can prompt manual entry
        return {"product": None, "source": None, "fallback": "manual_entry", "merged": merged.as_dict()}
    return {"product": product.as_dict(), "source": source, "fallback": None}
