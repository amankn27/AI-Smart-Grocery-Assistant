"""PDF invoice generation from a cart summary (reportlab).

The GST breakup comes straight from the deterministic billing core, so the numbers on the
PDF are identical to what the API returns. reportlab is imported lazily so the module can be
imported without it (the route surfaces a clear error if it's missing)."""

from __future__ import annotations

import io

from app.services.billing import LineItem, summarize_cart


def build_invoice_pdf(items: list[LineItem], *, title: str = "Smart Grocery Assistant") -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    summary = summarize_cart(items)
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 25 * mm

    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, y, title)
    y -= 8 * mm
    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, y, "Tax Invoice (GST-inclusive MRP)  ·  Currency: INR")
    y -= 10 * mm

    # Header row
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Item")
    c.drawString(110 * mm, y, "Qty")
    c.drawString(130 * mm, y, "MRP")
    c.drawRightString(190 * mm, y, "Amount")
    y -= 2 * mm
    c.line(20 * mm, y, 190 * mm, y)
    y -= 6 * mm

    c.setFont("Helvetica", 10)
    for it in items:
        if it.quantity == 0:
            continue
        c.drawString(20 * mm, y, it.name[:45])
        c.drawString(110 * mm, y, str(it.quantity))
        c.drawString(130 * mm, y, f"{float(it.mrp):.2f}")
        c.drawRightString(190 * mm, y, f"{it.line_total:.2f}")
        y -= 6 * mm
        if y < 40 * mm:
            c.showPage()
            y = height - 25 * mm

    y -= 2 * mm
    c.line(120 * mm, y, 190 * mm, y)
    y -= 7 * mm
    c.setFont("Helvetica", 10)
    for label, value in (
        ("Taxable value", summary.taxable_value),
        ("CGST", summary.total_cgst),
        ("SGST", summary.total_sgst),
        ("Total GST", summary.total_gst),
    ):
        c.drawString(120 * mm, y, label)
        c.drawRightString(190 * mm, y, f"{value:.2f}")
        y -= 6 * mm

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.black)
    c.drawString(120 * mm, y, "Grand Total")
    c.drawRightString(190 * mm, y, f"INR {summary.total:.2f}")

    c.showPage()
    c.save()
    return buf.getvalue()
