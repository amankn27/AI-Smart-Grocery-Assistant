"""Open Food Facts fallback tests. The HTTP fetch is monkeypatched — no network in CI."""

import app.services.openfoodfacts as off
from app.services.openfoodfacts import lookup_off

# A trimmed real-shape OFF v2 payload (Veeba-style tomato ketchup).
_OFF_HIT = {
    "status": 1,
    "product": {
        "product_name": "Tomato Ketchup",
        "brands": "Veeba, Other",
        "nutriments": {
            "energy-kcal_100g": 110,
            "proteins_100g": 1.2,
            "fat_100g": 0.2,
            "saturated-fat_100g": 0.05,
            "carbohydrates_100g": 26,
            "sugars_100g": 22.5,
            "salt_100g": 2.5,  # -> sodium 1.0 g -> 1000 mg
        },
    },
}


def test_maps_off_payload_to_product(monkeypatch):
    monkeypatch.setattr(off, "_fetch_off_json", lambda *a, **k: _OFF_HIT)
    p = lookup_off("8901234567890")
    assert p is not None
    assert p.name == "Tomato Ketchup"
    assert p.brand == "Veeba"                 # first brand only
    assert p.barcode == "8901234567890"
    assert p.nutrition["sugar_g"] == 22.5
    assert p.nutrition["energy_kcal"] == 110.0
    assert p.nutrition["sodium_mg"] == 1000.0  # salt 2.5g / 2.5 * 1000
    assert p.mrp == 0.0                         # OFF has no MRP


def test_sodium_prefers_direct_sodium_over_salt(monkeypatch):
    payload = {
        "status": 1,
        "product": {"product_name": "X", "brands": "B",
                    "nutriments": {"sodium_100g": 0.3, "salt_100g": 2.5}},
    }
    monkeypatch.setattr(off, "_fetch_off_json", lambda *a, **k: payload)
    p = lookup_off("111")
    assert p.nutrition["sodium_mg"] == 300.0   # 0.3 g -> 300 mg, salt ignored


def test_not_found_returns_none(monkeypatch):
    monkeypatch.setattr(off, "_fetch_off_json", lambda *a, **k: {"status": 0})
    assert lookup_off("000") is None


def test_nameless_product_treated_as_miss(monkeypatch):
    monkeypatch.setattr(off, "_fetch_off_json",
                        lambda *a, **k: {"status": 1, "product": {"product_name": "", "nutriments": {}}})
    assert lookup_off("222") is None


def test_network_error_degrades_gracefully(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("connection reset")
    monkeypatch.setattr(off, "_fetch_off_json", boom)
    assert lookup_off("333") is None  # must not raise


def test_disabled_by_config_skips_lookup(monkeypatch):
    from app.config import settings as settings_mod

    settings_mod.get_settings.cache_clear()
    monkeypatch.setenv("OFF_ENABLED", "false")

    called = {"n": 0}
    def counter(*a, **k):
        called["n"] += 1
        return _OFF_HIT
    monkeypatch.setattr(off, "_fetch_off_json", counter)
    try:
        assert lookup_off("444") is None
        assert called["n"] == 0  # never hit the network when disabled
    finally:
        settings_mod.get_settings.cache_clear()
