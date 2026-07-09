"""API tests for Phase 2 endpoints. Uses a temp DB; skipped if web/DB deps absent."""

import os
import tempfile

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
pytest.importorskip("sqlalchemy")
pytest.importorskip("jose")

_db = tempfile.mktemp(suffix=".db").replace("\\", "/")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_db}")
os.environ.setdefault("JWT_SECRET", "test-secret")

from app.config.settings import get_settings  # noqa: E402

get_settings.cache_clear()
from app.db import database  # noqa: E402

database.get_engine.cache_clear()
database.get_sessionmaker.cache_clear()
database.init_db()

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def _auth_header(email):
    tok = client.post("/auth/register", json={"email": email, "password": "secret123"}).json()["access_token"]
    return {"Authorization": f"Bearer {tok}"}


def test_recipe_from_explicit_ingredients():
    r = client.post("/recipe", json={"ingredients": ["paneer", "peas"], "diet": "veg"})
    assert r.status_code == 200
    body = r.json()
    assert body["ingredients"] == ["paneer", "peas"]
    assert body["provider"] in ("echo", "gemini")


def test_voice_without_audio_or_text_asks_for_input():
    r = client.post("/voice", data={})
    assert r.status_code == 200
    assert r.json()["fallback"] == "no_speech_detected"


def test_voice_with_typed_text_answers():
    r = client.post("/voice", data={"text": "Is this healthy?"})
    body = r.json()
    assert body["transcript"] == "Is this healthy?"
    assert body["answer"]  # echo or real provider
    assert body["stt_engine"] == "client"


def test_pantry_crud_and_reminders():
    h = _auth_header("pantry@b.com")
    # add an already-expired and a soon-to-expire item
    client.post("/pantry", headers=h, json={"name": "Old Milk", "expiry_date": "2000-01-01"})
    client.post("/pantry", headers=h, json={"name": "Bread", "category": "bread"})  # no date

    items = client.get("/pantry", headers=h).json()["items"]
    assert len(items) == 2
    # expired item sorts first
    assert items[0]["name"] == "Old Milk"
    assert items[0]["status"] == "expired"

    rem = client.get("/pantry/reminders", headers=h).json()["reminders"]
    assert any(r["name"] == "Old Milk" for r in rem)


def test_pantry_requires_auth():
    assert client.get("/pantry").status_code == 401
