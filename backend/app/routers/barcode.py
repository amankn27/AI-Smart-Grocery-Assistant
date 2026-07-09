"""/barcode — decode an EAN/UPC/QR from an image and fill product data from the catalog.

Flow: decode → catalog lookup by barcode → merge with any OCR nutrition the client passes.
Degrades to "not found / manual entry" rather than erroring when no code is readable.
"""

from __future__ import annotations

from fastapi import APIRouter, File, Form, UploadFile

from app.config.providers import get_barcode_decoder
from app.services.catalog import get_catalog
from app.services.merge import merge_product_data

router = APIRouter(tags=["barcode"])


@router.post("/barcode")
async def scan_barcode(image: UploadFile = File(...)) -> dict:
    data = await image.read()
    decoder = get_barcode_decoder()
    codes = decoder.decode(data)
    if not codes:
        return {"decoder": decoder.name, "barcodes": [], "product": None, "fallback": "manual_entry"}

    catalog = get_catalog()
    product = None
    matched_code = None
    for code in codes:
        hit = catalog.by_barcode(code.value)
        if hit:
            product, matched_code = hit, code
            break

    return {
        "decoder": decoder.name,
        "barcodes": [{"value": c.value, "type": c.type} for c in codes],
        "matched_barcode": matched_code.value if matched_code else None,
        "product": product.as_dict() if product else None,
        "fallback": None if product else "not_in_catalog",
    }


@router.post("/barcode/lookup")
def lookup_barcode(barcode: str = Form(...)) -> dict:
    """Manual barcode entry path (when the camera can't read it)."""
    product = get_catalog().by_barcode(barcode)
    if not product:
        merged = merge_product_data()  # empty shell so the UI can prompt manual entry
        return {"product": None, "fallback": "manual_entry", "merged": merged.as_dict()}
    return {"product": product.as_dict(), "fallback": None}
