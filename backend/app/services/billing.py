"""Deterministic billing / cart math for the Indian market.

Pure functions only — no I/O, no model calls, no framework imports. Every value is
computed from its inputs so the whole module is trivially unit-testable (see
`tests/test_billing.py`). Money is handled with :class:`~decimal.Decimal` and rounded to
paise (2 dp) to avoid float drift on totals.

Assumptions (brief §2): currency INR, prices are MRP (GST-inclusive under Indian law),
GST is shown as a back-computed breakup for transparency, not added on top of MRP.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable

# GST rate slabs applicable to common packaged food categories. These are indicative
# Phase 0 values keyed by our internal category; the source of truth for production
# should be a maintained tax table. Rates are fractions (0.05 == 5%).
GST_RATES: dict[str, Decimal] = {
    "biscuits": Decimal("0.18"),
    "chips_namkeen": Decimal("0.12"),
    "chocolate": Decimal("0.18"),
    "instant_noodles": Decimal("0.18"),
    "soft_drink": Decimal("0.28"),
    "juice": Decimal("0.12"),
    "milk_dairy": Decimal("0.05"),
    "bread": Decimal("0.05"),
    "cereal": Decimal("0.18"),
    "cooking_oil": Decimal("0.05"),
    "tea_coffee": Decimal("0.05"),
    "snack_bar": Decimal("0.18"),
}
DEFAULT_GST_RATE = Decimal("0.18")

_PAISE = Decimal("0.01")


def gst_rate_for(category: str | None) -> Decimal:
    """Return the GST fraction for a category, falling back to the default slab."""
    if not category:
        return DEFAULT_GST_RATE
    return GST_RATES.get(category.strip().lower(), DEFAULT_GST_RATE)


def _money(value: Decimal | int | float | str) -> Decimal:
    """Coerce to a paise-rounded Decimal (half-up, the convention for retail invoices)."""
    return Decimal(str(value)).quantize(_PAISE, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class LineItem:
    """One priced row in the cart. ``mrp`` is the GST-inclusive per-unit price in INR."""

    product_id: str
    name: str
    mrp: Decimal
    quantity: int
    category: str | None = None

    def __post_init__(self) -> None:
        if self.quantity < 0:
            raise ValueError(f"quantity must be >= 0, got {self.quantity}")
        if Decimal(str(self.mrp)) < 0:
            raise ValueError(f"mrp must be >= 0, got {self.mrp}")

    @property
    def line_total(self) -> Decimal:
        """MRP × quantity, rounded to paise."""
        return _money(Decimal(str(self.mrp)) * self.quantity)

    def gst_breakup(self) -> "GstBreakup":
        """Back-compute the GST component embedded in this line's MRP total."""
        rate = gst_rate_for(self.category)
        gross = self.line_total
        # MRP is inclusive: net = gross / (1 + rate); tax = gross - net.
        net = _money(gross / (Decimal("1") + rate))
        tax = _money(gross - net)
        # CGST and SGST split the tax evenly for intra-state sales.
        cgst = _money(tax / 2)
        sgst = _money(tax - cgst)
        return GstBreakup(rate=rate, taxable_value=net, cgst=cgst, sgst=sgst, total_tax=tax)


@dataclass(frozen=True)
class GstBreakup:
    rate: Decimal
    taxable_value: Decimal
    cgst: Decimal
    sgst: Decimal
    total_tax: Decimal


@dataclass
class CartSummary:
    subtotal: Decimal = field(default_factory=lambda: Decimal("0.00"))
    taxable_value: Decimal = field(default_factory=lambda: Decimal("0.00"))
    total_cgst: Decimal = field(default_factory=lambda: Decimal("0.00"))
    total_sgst: Decimal = field(default_factory=lambda: Decimal("0.00"))
    total_gst: Decimal = field(default_factory=lambda: Decimal("0.00"))
    total: Decimal = field(default_factory=lambda: Decimal("0.00"))
    item_count: int = 0

    def as_dict(self) -> dict[str, str | int]:
        """JSON-friendly view; Decimals rendered as fixed-2dp strings for exact display."""
        return {
            "subtotal": f"{self.subtotal:.2f}",
            "taxable_value": f"{self.taxable_value:.2f}",
            "total_cgst": f"{self.total_cgst:.2f}",
            "total_sgst": f"{self.total_sgst:.2f}",
            "total_gst": f"{self.total_gst:.2f}",
            "total": f"{self.total:.2f}",
            "item_count": self.item_count,
        }


def summarize_cart(items: Iterable[LineItem]) -> CartSummary:
    """Fold a set of line items into subtotal / GST breakup / grand total.

    Because MRP is GST-inclusive, ``subtotal`` and ``total`` are equal; the GST figures
    are the embedded tax broken out for the invoice. Keeping them separate makes the
    Phase 1 PDF invoice and any future exclusive-pricing locale a one-line change.
    """
    summary = CartSummary()
    for item in items:
        if item.quantity == 0:
            continue
        breakup = item.gst_breakup()
        summary.subtotal += item.line_total
        summary.taxable_value += breakup.taxable_value
        summary.total_cgst += breakup.cgst
        summary.total_sgst += breakup.sgst
        summary.total_gst += breakup.total_tax
        summary.item_count += item.quantity

    # Normalize every accumulated figure back to paise.
    summary.subtotal = _money(summary.subtotal)
    summary.taxable_value = _money(summary.taxable_value)
    summary.total_cgst = _money(summary.total_cgst)
    summary.total_sgst = _money(summary.total_sgst)
    summary.total_gst = _money(summary.total_gst)
    summary.total = summary.subtotal  # MRP-inclusive: grand total == subtotal
    return summary
