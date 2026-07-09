"""Deterministic pantry / expiry logic.

Pure functions over dates — no DB, no models — so expiry status and reminder selection are
fully unit-tested with a fixed ``today`` (see ``tests/test_pantry.py``). The router fetches
rows and hands dicts in; this module decides freshness and what to remind about.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

# Status buckets, ordered by urgency for sorting.
STATUS_ORDER = {"expired": 0, "expiring_soon": 1, "fresh": 2, "no_date": 3}

DEFAULT_SOON_DAYS = 3


def _as_date(value) -> Optional[date]:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def days_left(expiry, today: date) -> Optional[int]:
    """Whole days from ``today`` until ``expiry`` (negative if already past). None if no date."""
    exp = _as_date(expiry)
    if exp is None:
        return None
    return (exp - today).days


def expiry_status(expiry, today: date, soon_days: int = DEFAULT_SOON_DAYS) -> str:
    """Classify an item: ``expired`` | ``expiring_soon`` | ``fresh`` | ``no_date``."""
    dl = days_left(expiry, today)
    if dl is None:
        return "no_date"
    if dl < 0:
        return "expired"
    if dl <= soon_days:
        return "expiring_soon"
    return "fresh"


@dataclass
class PantryView:
    id: int
    name: str
    category: str
    quantity: int
    expiry_date: Optional[str]
    days_left: Optional[int]
    status: str

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "quantity": self.quantity,
            "expiry_date": self.expiry_date,
            "days_left": self.days_left,
            "status": self.status,
        }


def build_view(item: dict, today: date, soon_days: int = DEFAULT_SOON_DAYS) -> PantryView:
    """Attach computed days_left + status to a raw pantry row dict."""
    return PantryView(
        id=item.get("id", 0),
        name=item.get("name", ""),
        category=item.get("category", ""),
        quantity=int(item.get("quantity", 1) or 1),
        expiry_date=str(item["expiry_date"]) if item.get("expiry_date") else None,
        days_left=days_left(item.get("expiry_date"), today),
        status=expiry_status(item.get("expiry_date"), today, soon_days),
    )


def list_with_status(items: list[dict], today: date, soon_days: int = DEFAULT_SOON_DAYS) -> list[PantryView]:
    """All items with status, sorted most-urgent first (expired → soon → fresh → no date)."""
    views = [build_view(i, today, soon_days) for i in items]
    views.sort(key=lambda v: (STATUS_ORDER[v.status], v.days_left if v.days_left is not None else 10**6))
    return views


def reminders(items: list[dict], today: date, within_days: int = DEFAULT_SOON_DAYS) -> list[PantryView]:
    """Items that are expired or expiring within ``within_days`` — the reminder feed."""
    out = [
        v for v in list_with_status(items, today, within_days)
        if v.status in ("expired", "expiring_soon")
    ]
    return out
