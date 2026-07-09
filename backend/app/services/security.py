"""Password hashing + JWT issue/verify.

Kept as small pure-ish helpers so they're unit-testable. passlib/python-jose are imported at
module load (they're core deps in requirements.txt); tests that touch this importorskip them
so the deterministic-core suite still runs on a minimal install.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from jose import JWTError, jwt

from app.config.settings import get_settings

_ALGO = "HS256"


def _prepare(password: str) -> bytes:
    # bcrypt only considers the first 72 bytes and (v4+) errors on longer input — truncate.
    return password.encode("utf-8")[:72]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prepare(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_prepare(password), hashed.encode("utf-8"))
    except ValueError:
        return False


def _create_token(subject: str, ttl: timedelta, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": subject, "type": token_type, "iat": now, "exp": now + ttl}
    return jwt.encode(payload, get_settings().jwt_secret, algorithm=_ALGO)


def create_access_token(subject: str) -> str:
    s = get_settings()
    return _create_token(subject, timedelta(minutes=s.jwt_access_ttl_min), "access")


def create_refresh_token(subject: str) -> str:
    s = get_settings()
    return _create_token(subject, timedelta(days=s.jwt_refresh_ttl_days), "refresh")


def decode_token(token: str, *, expected_type: Optional[str] = None) -> dict[str, Any]:
    """Return the token payload, raising ValueError on any invalidity (expired/bad type/sig)."""
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[_ALGO])
    except JWTError as exc:
        raise ValueError(f"invalid token: {exc}") from exc
    if expected_type and payload.get("type") != expected_type:
        raise ValueError(f"expected {expected_type} token, got {payload.get('type')}")
    return payload
