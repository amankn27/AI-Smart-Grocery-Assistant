"""API integration tests. Skipped cleanly if FastAPI/httpx aren't installed so the
deterministic-core suite still runs on a minimal environment."""

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")  # required by starlette TestClient

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_analyze_endpoint():
    r = client.post("/analyze", json={"sugar_g": 45, "sodium_mg": 800, "saturated_fat_g": 14})
    assert r.status_code == 200
    body = r.json()
    assert body["score"] <= 40
    assert any(w["severity"] == "red" for w in body["warnings"])


def test_cart_flow():
    sid = "test-session"
    r = client.post(
        "/cart/add",
        params={"session_id": sid},
        json={"product_id": "c1", "name": "Cola", "mrp": 128.0, "quantity": 1, "category": "soft_drink"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["item_count"] == 1
    assert body["subtotal"] == "128.00"
    assert body["total_gst"] == "28.00"

    r2 = client.post("/cart/update", params={"session_id": sid}, json={"product_id": "c1", "quantity": 0})
    assert r2.json()["item_count"] == 0


def test_chat_offline_provider():
    r = client.post("/chat", json={"question": "Is this healthy?"})
    assert r.status_code == 200
    # Without a key, the echo provider answers deterministically.
    assert r.json()["provider"] in ("echo", "gemini")
