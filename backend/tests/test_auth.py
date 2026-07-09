"""Auth + persistence integration tests.

Uses a throwaway SQLite DB. Skipped cleanly if auth/DB deps aren't installed so the
deterministic-core suite still runs on a minimal environment.
"""

import os
import tempfile

import pytest

pytest.importorskip("sqlalchemy")
pytest.importorskip("jose")
pytest.importorskip("passlib")
pytest.importorskip("fastapi")
pytest.importorskip("httpx")

# Point at a temp DB and reset cached settings/engine BEFORE importing the app.
_db = tempfile.mktemp(suffix=".db").replace("\\", "/")
os.environ["DATABASE_URL"] = f"sqlite:///{_db}"
os.environ["JWT_SECRET"] = "test-secret"

from app.config.settings import get_settings  # noqa: E402

get_settings.cache_clear()
from app.db import database  # noqa: E402

database.get_engine.cache_clear()
database.get_sessionmaker.cache_clear()
database.init_db()

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def _register(email="a@b.com", password="secret123"):
    return client.post("/auth/register", json={"email": email, "password": password})


def test_register_login_me_flow():
    r = _register("flow@b.com")
    assert r.status_code == 201
    access = r.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert me.status_code == 200
    assert me.json()["email"] == "flow@b.com"


def test_duplicate_registration_conflicts():
    _register("dup@b.com")
    assert _register("dup@b.com").status_code == 409


def test_login_wrong_password_rejected():
    _register("pw@b.com", "rightpass")
    r = client.post("/auth/login", data={"username": "pw@b.com", "password": "wrongpass"})
    assert r.status_code == 401


def test_protected_route_requires_token():
    assert client.get("/auth/me").status_code == 401
    assert client.get("/history").status_code == 401


def test_history_and_dashboard_roundtrip():
    tok = _register("hist@b.com").json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    client.post(
        "/history/scan", headers=h,
        json={"name": "Cola", "category": "soft_drink", "mrp": 40, "quantity": 2,
              "nutrition": {"sugar_g": 40, "sodium_mg": 20, "energy_kcal": 42}},
    )
    hist = client.get("/history", headers=h).json()
    assert len(hist["scans"]) == 1
    # High sugar (40g/100g) is one red flag → penalized from 100 (but not junk-food low).
    assert hist["scans"][0]["health_score"] < 100

    dash = client.get("/dashboard", headers=h).json()
    assert dash["total_spend"] == "80.00"
    assert dash["category_mix"][0]["category"] == "soft_drink"


def test_refresh_issues_new_access_token():
    refresh = _register("ref@b.com").json()["refresh_token"]
    r = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200
    assert "access_token" in r.json()
