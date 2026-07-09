"""Unit tests for the deterministic billing core. No model/network deps."""

from decimal import Decimal

import pytest

from app.services.billing import (
    DEFAULT_GST_RATE,
    LineItem,
    gst_rate_for,
    summarize_cart,
)


def test_gst_rate_lookup_and_default():
    assert gst_rate_for("soft_drink") == Decimal("0.28")
    assert gst_rate_for("MILK_DAIRY") == Decimal("0.05")  # case-insensitive
    assert gst_rate_for("unknown_cat") == DEFAULT_GST_RATE
    assert gst_rate_for(None) == DEFAULT_GST_RATE


def test_line_total_rounds_to_paise():
    item = LineItem("p1", "Biscuit", Decimal("10.333"), quantity=3, category="biscuits")
    assert item.line_total == Decimal("31.00")  # 30.999 -> 31.00


def test_gst_breakup_is_inclusive_and_splits_evenly():
    # 28% GST inclusive on 128.00 => net 100.00, tax 28.00, cgst=sgst=14.00
    item = LineItem("c1", "Cola", Decimal("128.00"), quantity=1, category="soft_drink")
    b = item.gst_breakup()
    assert b.taxable_value == Decimal("100.00")
    assert b.total_tax == Decimal("28.00")
    assert b.cgst == Decimal("14.00")
    assert b.sgst == Decimal("14.00")


def test_summary_totals_and_inclusive_grand_total():
    items = [
        LineItem("a", "Cola", Decimal("128.00"), 1, "soft_drink"),   # gst 28.00
        LineItem("b", "Milk", Decimal("105.00"), 2, "milk_dairy"),   # 210 incl 5%
    ]
    s = summarize_cart(items)
    assert s.item_count == 3
    assert s.subtotal == Decimal("338.00")
    assert s.total == s.subtotal            # MRP inclusive => total == subtotal
    assert s.total_gst == s.total_cgst + s.total_sgst
    assert s.total_gst > 0


def test_zero_quantity_items_are_skipped():
    s = summarize_cart([LineItem("a", "X", Decimal("50.00"), 0, "bread")])
    assert s.item_count == 0
    assert s.total == Decimal("0.00")


def test_negative_inputs_rejected():
    with pytest.raises(ValueError):
        LineItem("a", "X", Decimal("10.00"), quantity=-1)
    with pytest.raises(ValueError):
        LineItem("a", "X", Decimal("-5.00"), quantity=1)
