"""ORM models. Phase 1 adds users, scan history, and saved products.

Import-guarded so the module is only meaningful when SQLAlchemy is installed. Alembic
migrations live in ``backend/alembic/`` (Phase 1); ``init_db`` create_all is the dev path.
"""

from __future__ import annotations

from typing import Optional

try:
    from datetime import date, datetime, timezone

    from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

    def _utcnow() -> "datetime":
        return datetime.now(timezone.utc)

    class Base(DeclarativeBase):
        pass

    class User(Base):
        __tablename__ = "users"

        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        email: Mapped[str] = mapped_column(String(256), unique=True, index=True)
        password_hash: Mapped[str] = mapped_column(String(256), default="")  # empty for OAuth-only
        oauth_provider: Mapped[str] = mapped_column(String(32), default="")
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

        scans: Mapped[list["Scan"]] = relationship(back_populates="user", cascade="all, delete-orphan")
        saved: Mapped[list["SavedProduct"]] = relationship(back_populates="user", cascade="all, delete-orphan")
        pantry: Mapped[list["PantryItem"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    class Scan(Base):
        """A recorded product scan/add for history + dashboard analytics."""

        __tablename__ = "scans"

        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
        product_id: Mapped[str] = mapped_column(String(128), default="")
        name: Mapped[str] = mapped_column(String(256), default="")
        brand: Mapped[str] = mapped_column(String(128), default="")
        category: Mapped[str] = mapped_column(String(64), default="", index=True)
        mrp: Mapped[float] = mapped_column(Float, default=0.0)
        quantity: Mapped[int] = mapped_column(Integer, default=1)
        health_score: Mapped[int] = mapped_column(Integer, default=0)
        energy_kcal: Mapped[float] = mapped_column(Float, default=0.0)
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)

        user: Mapped["User"] = relationship(back_populates="scans")

    class SavedProduct(Base):
        __tablename__ = "saved_products"

        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
        product_id: Mapped[str] = mapped_column(String(128))
        name: Mapped[str] = mapped_column(String(256), default="")
        note: Mapped[str] = mapped_column(Text, default="")
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

        user: Mapped["User"] = relationship(back_populates="saved")

    class PantryItem(Base):
        __tablename__ = "pantry_items"

        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
        product_id: Mapped[str] = mapped_column(String(128), default="")
        name: Mapped[str] = mapped_column(String(256), default="")
        category: Mapped[str] = mapped_column(String(64), default="")
        quantity: Mapped[int] = mapped_column(Integer, default=1)
        expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
        opened: Mapped[bool] = mapped_column(Boolean, default=False)
        added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

        user: Mapped["User"] = relationship(back_populates="pantry")

except ImportError:  # pragma: no cover
    Base = None  # type: ignore[assignment]
