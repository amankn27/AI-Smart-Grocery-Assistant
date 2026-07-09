"""Deterministic pantry expiry/reminder tests with a fixed 'today'."""

from datetime import date

from app.services.pantry import (
    days_left,
    expiry_status,
    list_with_status,
    reminders,
)

TODAY = date(2026, 7, 9)


def test_days_left_and_status():
    assert days_left("2026-07-12", TODAY) == 3
    assert days_left("2026-07-01", TODAY) == -8
    assert days_left(None, TODAY) is None

    assert expiry_status("2026-07-01", TODAY) == "expired"
    assert expiry_status("2026-07-10", TODAY) == "expiring_soon"   # 1 day (<=3)
    assert expiry_status("2026-07-20", TODAY) == "fresh"
    assert expiry_status(None, TODAY) == "no_date"


def test_soon_days_threshold_is_configurable():
    assert expiry_status("2026-07-15", TODAY, soon_days=3) == "fresh"       # 6 days
    assert expiry_status("2026-07-15", TODAY, soon_days=7) == "expiring_soon"


def test_list_sorted_by_urgency():
    items = [
        {"id": 1, "name": "Fresh", "expiry_date": "2026-08-01"},   # fresh
        {"id": 2, "name": "Expired", "expiry_date": "2026-07-01"}, # expired
        {"id": 3, "name": "NoDate", "expiry_date": None},          # no date
        {"id": 4, "name": "Soon", "expiry_date": "2026-07-10"},    # soon
    ]
    order = [v.name for v in list_with_status(items, TODAY)]
    assert order == ["Expired", "Soon", "Fresh", "NoDate"]


def test_reminders_only_expired_and_soon():
    items = [
        {"id": 1, "name": "Fresh", "expiry_date": "2026-08-01"},
        {"id": 2, "name": "Expired", "expiry_date": "2026-07-01"},
        {"id": 4, "name": "Soon", "expiry_date": "2026-07-11"},
    ]
    names = {v.name for v in reminders(items, TODAY, within_days=3)}
    assert names == {"Expired", "Soon"}
