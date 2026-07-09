"""SQLAlchemy engine/session wiring.

Defaults to SQLite (zero-setup local/test) and switches to Postgres purely via
``DATABASE_URL`` (docker-compose sets it). SQLAlchemy is imported lazily so the
deterministic core and its tests don't require it to be installed.
"""

from __future__ import annotations

from functools import lru_cache

from app.config.settings import get_settings


@lru_cache
def get_engine():
    from sqlalchemy import create_engine

    url = get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args, future=True)


@lru_cache
def get_sessionmaker():
    from sqlalchemy.orm import sessionmaker

    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False, future=True)


def get_db():
    """FastAPI dependency yielding a session (used by Phase 1 persistence routers)."""
    SessionLocal = get_sessionmaker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables for models registered on Base. No-op if SQLAlchemy isn't installed."""
    try:
        from app.db.models import Base
    except Exception:  # noqa: BLE001
        return
    Base.metadata.create_all(bind=get_engine())
